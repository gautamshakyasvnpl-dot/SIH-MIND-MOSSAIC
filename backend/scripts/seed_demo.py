"""Seed the NEUROLEARN demo account.

Creates demo@neurolearn.app / demo12345 with a Signals & Systems lecture,
a starter preference profile and interaction history so the Personalization
Center looks alive on first login. Idempotent: re-running refreshes nothing
but reports the existing account.

Usage:
    backend\\.venv\\Scripts\\python backend\\scripts\\seed_demo.py
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

from app.core.security import hash_password  # noqa: E402
from app.db import Base, engine, SessionLocal  # noqa: E402
from app.models import (  # noqa: E402
    Document,
    InteractionEvent,
    PreferenceScore,
    User,
)
from app.services import preferences as prefs  # noqa: E402

DEMO_EMAIL = "demo@neurolearn.app"
DEMO_PASSWORD = "demo12345"

LECTURE = (
    "Signals and Systems - Lecture 5: The Fourier Transform. "
    "The Fourier Transform converts a time-domain signal into its frequency-domain representation, "
    "revealing which frequencies a signal contains. Engineers care because circuits, filters and "
    "communication systems all behave differently at different frequencies. For example, a square "
    "wave can be built by adding sine waves whose frequencies are odd multiples of the fundamental. "
    "The transform is defined by an integral that multiplies the signal x(t) by e^(-j*2*pi*f*t) and "
    "integrates over time; the result X(f) tells us how much of each frequency lives inside x(t). "
    "Low frequency components carry the overall shape of the signal, while high frequency components "
    "carry sharp edges and fine detail. A low-pass filter keeps the slow parts and removes the fast ones, "
    "which is exactly how audio smoothing works. In practice we compute the transform digitally using the "
    "Fast Fourier Transform (FFT), an algorithm that reduces the cost from O(N^2) to O(N log N). "
    "Sampling at rate Fs must exceed twice the highest frequency present, otherwise aliasing folds "
    "high frequencies into low ones and corrupts the spectrum."
)

COURSE_MODULES = {
    "lecture1_continuous_time_signals.txt": (
        "A continuous-time signal is defined for every value of time, unlike a discrete signal which "
        "is defined only at sampled instants. Common examples include sinusoids, exponentials and step "
        "functions. Signal energy is the area under the squared magnitude, while power is energy per unit "
        "time for periodic signals. Periodic signals such as sin(2*pi*f*t) repeat with period T = 1/f. "
        "For example, mains electricity in India is a 50 Hz sinusoid, so its period is 20 milliseconds."
    ),
    "lecture2_discrete_time_signals.txt": (
        "Discrete-time signals arise by sampling a continuous signal every T seconds, producing a sequence "
        "x[n] = x(nT). The sampling theorem states that Fs must be greater than twice the highest frequency "
        "to avoid losing information. Unit impulse and unit step sequences are the building blocks of "
        "discrete analysis. Digital audio, for example, samples music at 44.1 kHz because human hearing "
        "tops out near 20 kHz."
    ),
    "lecture3_lti_systems.txt": (
        "A system is linear when superposition holds and time-invariant when a delayed input produces an "
        "equally delayed output. Linear time-invariant systems are completely characterised by their "
        "impulse response h(t). The output of an LTI system is the convolution of the input with h(t). "
        "Convolution swaps difficult differential equations for integral operations. Stability follows "
        "when the impulse response is absolutely integrable."
    ),
    "lecture4_fourier_series.txt": (
        "Periodic signals can be expanded as a Fourier Series: a sum of sines and cosines at harmonics of "
        "the fundamental frequency. The coefficients measure how much each harmonic contributes. For example, "
        "a square wave contains only odd harmonics whose amplitudes fall off as one over n. Gibbs phenomenon "
        "describes the overshoot near sharp edges that persists no matter how many harmonics are added. "
        "Fourier series convert differential equations into simple algebra on coefficients."
    ),
    "lecture6_laplace_transform.txt": (
        "The Laplace Transform maps a differential equation in time into an algebraic equation in the "
        "s-domain using the kernel e^(-s t). It generalises the Fourier Transform by adding exponential "
        "damping, so it converges for a wider class of signals. Poles and zeros of the transfer function "
        "reveal stability and resonance. For instance, a pole in the right half plane signals an unstable "
        "system. Inverse transformation via partial fractions recovers the time-domain solution."
    ),
    "lecture7_z_transform.txt": (
        "The Z Transform is the discrete-time cousin of the Laplace Transform, mapping sequences to the "
        "complex z-plane through X(z) = sum x[n] z^(-n). The unit circle plays the role that the imaginary "
        "axis plays for Laplace, and poles inside the unit circle indicate stability. The Z Transform turns "
        "difference equations into polynomial algebra, which is how digital filters are designed. Students "
        "often find region-of-convergence reasoning tricky at first, but it follows directly from convergence "
        "of the defining geometric series."
    ),
}

SEED_EVENTS = [
    ("feedback_too_long", "Fourier Transform"),
    ("requested_example", "Square wave"),
    ("opened_concept_map", "Frequency spectrum"),
]

MEMORY_EVENTS = [
    ("quiz_incorrect", "Z Transform"),
    ("quiz_incorrect", "Z Transform"),
    ("quiz_incorrect", "Region of convergence"),
]


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == DEMO_EMAIL).first()
        if user is None:
            user = User(
                id=uuid_hex(),
                email=DEMO_EMAIL,
                display_name="Demo Student",
                password_hash=hash_password(DEMO_PASSWORD),
            )
            db.add(user)
            db.commit()
            print(f"created demo user {DEMO_EMAIL}")
        else:
            print(f"demo user already exists: {DEMO_EMAIL}")

        existing_docs = {
            d.filename for d in db.query(Document).filter(Document.user_id == user.id).all()
        }
        to_seed = []
        if "lecture5_fourier_transform.txt" not in existing_docs:
            to_seed.append(("lecture5_fourier_transform.txt", LECTURE))
        for fname, body in COURSE_MODULES.items():
            if fname not in existing_docs:
                to_seed.append((fname, body))
        for fname, body in to_seed:
            db.add(
                Document(
                    id=uuid_hex(),
                    user_id=user.id,
                    filename=fname,
                    doc_type="txt",
                    char_count=len(body),
                    text_content=body,
                )
            )
        db.commit()
        print(f"seeded {len(to_seed)} lecture document(s)")

        scores = prefs.bootstrap_from_profile(
            {"modality_affinity": "visual", "chunk_size": "small", "pace": "gentle"}
        )
        for event, concept in SEED_EVENTS:
            scores, _ = prefs.apply_signal(scores, event)
        row = db.get(PreferenceScore, user.id)
        if row is None:
            db.add(PreferenceScore(user_id=user.id, scores=scores))
        else:
            row.scores = scores

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if not db.query(InteractionEvent).filter(InteractionEvent.user_id == user.id).first():
            for i, (event, concept) in enumerate([*SEED_EVENTS, *MEMORY_EVENTS]):
                db.add(
                    InteractionEvent(
                        id=uuid_hex(),
                        user_id=user.id,
                        event=event,
                        concept=concept,
                        meta={},
                        created_at=now - timedelta(minutes=45 - i * 6),
                    )
                )
        db.commit()
        print(f"scores: { {k: round(v, 2) for k, v in scores.items()} }")
        print("login: demo@neurolearn.app / demo12345")
    finally:
        db.close()


def uuid_hex() -> str:
    import uuid

    return uuid.uuid4().hex


if __name__ == "__main__":
    main()
