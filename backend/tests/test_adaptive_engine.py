import io
import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app  # noqa: E402
from app.services.preferences import apply_signal, bootstrap_from_profile, presentation_hints  # noqa: E402
from app.services.reader import build_cards, explain_ladder, make_quiz, prioritize  # noqa: E402

LECTURE = (
    "The Fourier Transform converts a time-domain signal into its frequency-domain representation. "
    "Engineers use it because circuits behave differently at different frequencies. "
    "For example, a square wave is built from many sine waves added together. "
    "The transform is defined by an integral that multiplies the signal by complex exponentials. "
    "Low frequency components carry the overall shape of the signal. "
    "High frequency components carry sharp edges and fine detail. "
    "In practice we compute it with the Fast Fourier Transform on sampled data."
)


def test_apply_signal_formula_and_explanation():
    updated, changes = apply_signal({"short_explanations": 0.5}, "feedback_too_long")
    assert updated["short_explanations"] == pytest.approx(0.65)
    assert changes[0]["explanation"].startswith("Short explanations score raised")


def test_apply_signal_unknown_event_is_noop():
    scores = {"examples": 0.4}
    updated, changes = apply_signal(scores, "danced_a_jig")
    assert updated == scores and changes == []


def test_scores_never_leave_clamp_band():
    s = {"short_explanations": 0.97}
    for _ in range(6):
        s, _ = apply_signal(s, "requested_simpler")
    assert s["short_explanations"] <= 0.98
    low = {"audio": 0.05}
    for _ in range(6):
        low, _ = apply_signal(low, "read_aloud")
    assert low["audio"] >= 0.02


def test_bootstrap_respects_profile():
    audio_profile = bootstrap_from_profile({"modality_affinity": "audio", "chunk_size": "small"})
    assert audio_profile["audio"] > 0.8
    assert audio_profile["short_explanations"] > 0.7


def test_presentation_hints_shape_reader():
    hints = presentation_hints({"short_explanations": 0.9, "quizzes": 0.9})
    assert hints["start_level"] == 1 and hints["suggest_quiz_after_cards"] == 2


def test_build_cards_shape_and_example_detection():
    cards = build_cards(LECTURE)
    assert len(cards) >= 3
    c = cards[0]
    assert {"index", "title", "simple", "technical", "example", "has_visual", "concept"} <= set(c)
    examples = [x for x in cards if x["example"]]
    assert examples, "the 'For example' sentence should surface as an example"


def test_ladder_level1_shorter_than_level4():
    l1, t1 = explain_ladder(LECTURE, 1)
    _, t4 = explain_ladder(LECTURE, 4)
    assert l1 == 1 and len(t1) < len(t4)
    _, t3 = explain_ladder("Recursion means a function calling itself.", 3)
    assert "Analogy:" in t3


def test_quiz_items_are_wellformed_and_deterministic():
    q1 = make_quiz(LECTURE, count=2)
    q2 = make_quiz(LECTURE, count=2)
    assert q1 == q2, "same input must give identical practice quiz"
    for item in q1:
        assert item["question"].startswith("Fill the gap:")
        assert len(item["options"]) >= 4
        assert 0 <= item["answer_index"] < len(item["options"])
        assert "______" in item["question"]
        correct = item["options"][item["answer_index"]]
        assert correct.isalpha()


def test_prioritize_thirds_cover_everything():
    plan = prioritize([f"Chapter {i}" for i in range(7)])
    total = sum(len(v) for v in plan.values())
    assert total == 7
    assert plan["high"][0] == "Chapter 0"
    assert plan["low"][-1] == "Chapter 6"


@pytest.fixture(scope="module")
def client() -> TestClient:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def auth(client: TestClient) -> dict[str, str]:
    email = f"adapt_{uuid.uuid4().hex[:8]}@test.com"
    r = client.post(
        "/api/auth/register",
        json={"email": email, "password": "password123", "display_name": "A"},
    )
    headers = {"Authorization": f"Bearer {r.json()['token']}"}
    consent = client.post("/api/consents", headers=headers, json={"telemetry": True})
    assert consent.status_code == 200, consent.text
    return headers


@pytest.fixture(scope="module")
def doc_id(client: TestClient, auth: dict[str, str]) -> str:
    files = {"file": ("signals.txt", io.BytesIO((LECTURE * 3).encode()), "text/plain")}
    r = client.post("/api/documents", headers=auth, files=files)
    assert r.status_code == 200, r.text
    return r.json()["id"]


def test_full_adaptive_loop(client: TestClient, auth: dict[str, str], doc_id: str):
    base = client.get("/api/preferences", headers=auth).json()
    start_score = base["scores"]["short_explanations"]

    r = client.post(
        "/api/interactions",
        headers=auth,
        json={"event": "feedback_too_long", "document_id": doc_id, "concept": "Fourier Transform"},
    )
    assert r.status_code == 200, r.text
    after_one = r.json()["scores"]["short_explanations"]
    assert after_one > start_score

    r = client.post("/api/interactions", headers=auth, json={"event": "feedback_too_long"})
    after_two = r.json()["scores"]["short_explanations"]
    assert after_two > after_one

    reader = client.get(f"/api/documents/{doc_id}/reader", headers=auth).json()
    assert reader["presentation"]["start_level"] == 1
    assert reader["presentation"]["hints_explanation"]
    assert len(reader["cards"]) >= 3

    lvl1 = client.post(
        "/api/documents/explain",
        headers=auth,
        json={"text": LECTURE, "level": 1},
    ).json()
    assert lvl1["engine"] == "heuristic-ladder"

    quiz = client.post(f"/api/documents/{doc_id}/quiz", headers=auth, json={"count": 3}).json()
    assert quiz["items"]

    prefs_after = client.get("/api/preferences", headers=auth).json()
    assert prefs_after["recent_events"], "interaction history must be queryable"


def test_manual_preference_override(client: TestClient, auth: dict[str, str]):
    r = client.put("/api/preferences", headers=auth, json={"scores": {"visual": 0.95}})
    assert r.json()["scores"]["visual"] == 0.95


def test_communication_email_template(client: TestClient, auth: dict[str, str]):
    r = client.post(
        "/api/communication",
        headers=auth,
        json={"mode": "email", "raw": "I could not finish the lab report because I was unwell.", "recipient": "Professor Rao"},
    ).json()
    assert r["engine"] == "template"
    assert r["result"].startswith("Subject:")
    assert "Dear Professor Rao" in r["result"]


def test_plan_endpoint(client: TestClient, auth: dict[str, str]):
    r = client.post(
        "/api/wellbeing/plan",
        headers=auth,
        json={"items": ["Fourier Series", "Laplace", "Z-Transform", "Sampling", "Convolution"]},
    ).json()
    assert sum(len(v) for v in (r["high"], r["medium"], r["low"])) == 5
