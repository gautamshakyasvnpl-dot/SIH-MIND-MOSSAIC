"""Adaptive Cognitive Experience Engine — preference scores.

Scores live in [0, 1] and are labelled "learning preference scores",
never diagnoses. Updates follow the transparent rule:

    new_score = 0.7 * previous + 0.3 * interaction_signal

Every mapped event yields a human-readable explanation string so the UI
can answer "Why am I seeing this?".
"""

from typing import Any

DEFAULT_SCORES: dict[str, float] = {
    "short_explanations": 0.5,
    "examples": 0.5,
    "visual": 0.45,
    "audio": 0.4,
    "step_by_step": 0.5,
    "quizzes": 0.45,
}

LABELS: dict[str, str] = {
    "short_explanations": "Short explanations",
    "examples": "Examples",
    "visual": "Visual explanations",
    "audio": "Audio & read-aloud",
    "step_by_step": "Step-by-step learning",
    "quizzes": "Frequent quizzes",
}

# event -> (score_key, signal_target)
EVENT_SIGNALS: dict[str, tuple[str, float]] = {
    "feedback_too_long": ("short_explanations", 1.0),
    "requested_simpler": ("short_explanations", 1.0),
    "explain_deeper": ("short_explanations", 0.15),
    "explain_deeper_stepwise": ("step_by_step", 1.0),
    "requested_example": ("examples", 1.0),
    "feedback_need_example": ("examples", 1.0),
    "example_helped": ("examples", 1.0),
    "opened_concept_map": ("visual", 1.0),
    "viewed_diagram": ("visual", 1.0),
    "played_audio": ("audio", 1.0),
    "read_aloud": ("audio", 1.0),
    "quiz_started": ("quizzes", 1.0),
    "quiz_completed": ("quizzes", 0.85),
    "quiz_correct": ("quizzes", 1.0),
    "completed_card": ("step_by_step", 0.9),
    "thumbs_up": ("__context__", 1.0),
    "thumbs_down": ("__context__", 0.05),
}

_FORMAT_TO_KEY: dict[str, str] = {
    "simplified_text": "short_explanations",
    "example": "examples",
    "concept_map": "visual",
    "audio": "audio",
    "quiz": "quizzes",
    "steps": "step_by_step",
}

_CLAMP = (0.02, 0.98)


def bootstrap_from_profile(profile: dict) -> dict[str, float]:
    """Seed scores from explicit onboarding choices (categorical prefs)."""
    scores = dict(DEFAULT_SCORES)
    modality = str(profile.get("modality_affinity", "text"))
    if modality == "audio":
        scores["audio"] = 0.9
        scores["visual"] = 0.25
    elif modality == "visual":
        scores["visual"] = 0.9
    if str(profile.get("chunk_size", "medium")) == "small":
        scores["short_explanations"] = 0.8
    if str(profile.get("pace", "standard")) == "gentle":
        scores["step_by_step"] = 0.75
    return scores


def apply_signal(
    scores: dict[str, float], event: str, meta: dict[str, Any] | None = None
) -> tuple[dict[str, float], list[dict[str, Any]]]:
    """Return (updated_scores, changes) for one logged interaction."""
    updated = {k: float(v) for k, v in (scores or DEFAULT_SCORES).items()}
    mapping = EVENT_SIGNALS.get(event)
    if mapping is None:
        return updated, []
    key, target = mapping
    meta = meta or {}
    if key == "__context__":
        fmt = str(meta.get("format", ""))
        key = _FORMAT_TO_KEY.get(fmt, "")
        if not key:
            return updated, []

    old = float(updated.get(key, DEFAULT_SCORES.get(key, 0.5)))
    new = round(min(_CLAMP[1], max(_CLAMP[0], 0.7 * old + 0.3 * target)), 4)
    updated[key] = new
    direction = "raised" if new > old else "lowered"
    label = LABELS.get(key, key)
    pct = int(round(new * 100))
    reason = (
        f"{label} score {direction} to {pct}% because you chose "
        f"\"{event.replace('_', ' ')}\"."
        if new != old
        else f"{label} stays at {pct}% - already close to this preference."
    )
    return updated, [{"key": key, "old": round(old, 4), "new": new, "explanation": reason}]


def describe_profile(scores: dict[str, float]) -> list[str]:
    """Plain-language lines for the 'Why this format?' panel."""
    merged = {**DEFAULT_SCORES, **(scores or {})}
    top = sorted(merged.items(), key=lambda kv: -kv[1])[:3]
    lines = []
    for key, value in top:
        label = LABELS.get(key, key)
        lines.append(
            f"You seem to prefer {label.lower()} right now "
            f"(learning-preference confidence {int(round(value * 100))}%)."
        )
    return lines


def presentation_hints(scores: dict[str, float]) -> dict[str, Any]:
    """How the reader should present content given current scores."""
    s = {**DEFAULT_SCORES, **(scores or {})}
    return {
        "start_level": 1 if s["short_explanations"] >= 0.62 else 4,
        "show_example_first": s["examples"] >= 0.6,
        "suggest_concept_map": s["visual"] >= 0.55,
        "suggest_quiz_after_cards": 2 if s["quizzes"] >= 0.6 else 4,
        "prefer_audio": s["audio"] >= 0.65,
        "hints_explanation": describe_profile(s),
    }
