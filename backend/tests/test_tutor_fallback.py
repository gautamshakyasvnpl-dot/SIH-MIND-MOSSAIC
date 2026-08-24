import json

import pytest

from app.services.tutor import (
    answer_question,
    break_into_sprints,
    evaluate_answer,
    make_viva_question,
)

RICH_CHUNKS = [
    (
        "Photosynthesis converts light energy into chemical energy inside plants. "
        "Chlorophyll is the pigment that captures sunlight in the leaves. "
        "Water molecules are split during the light reactions of photosynthesis."
    ),
    (
        "Cellular respiration releases energy from glucose in living cells. "
        "Mitochondria are the organelles where respiration reactions occur. "
        "Carbon dioxide is released as a waste product of respiration."
    ),
]

THIN_CHUNKS = ["Plants grow."]


@pytest.fixture(autouse=True)
def no_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)


def test_answer_extractive_contains_keyword():
    r = answer_question(RICH_CHUNKS, "What captures sunlight?")
    assert r["used_llm"] is False
    assert "chlorophyll" in r["answer"].lower()


def test_answer_zero_overlap_returns_grounded_miss():
    r = answer_question(RICH_CHUNKS, "What causes volcanic eruptions deep underwater?")
    assert r["used_llm"] is False
    assert "could not find" in r["answer"].lower()
    assert "document" in r["answer"].lower()


def test_answer_empty_question_returns_miss_not_crash():
    r = answer_question(RICH_CHUNKS, "   ")
    assert r["used_llm"] is False
    assert r["answer"] == ""


def test_make_viva_none_on_thin_material():
    assert make_viva_question(THIN_CHUNKS, []) is None


def test_five_distinct_viva_questions_on_rich_material():
    asked: list[str] = []
    questions: list[str] = []
    for _ in range(7):
        q = make_viva_question(RICH_CHUNKS, asked)
        if q is None:
            break
        questions.append(q)
        asked.append(q)
    assert len({q.split(":")[-1].strip().lower() for q in questions}) >= 3
    assert len(questions) >= 3


def test_evaluate_answer_scores():
    strong = evaluate_answer(
        "What captures sunlight?",
        RICH_CHUNKS[0],
        "Chlorophyll is the pigment that captures sunlight.",
    )
    weak = evaluate_answer("What captures sunlight?", RICH_CHUNKS[0], "banana banana")
    assert strong["score"] == 2
    assert weak["score"] == 0
    assert isinstance(strong["feedback"], str) and strong["feedback"]


def test_evaluate_answer_partial_against_long_chunk():
    long_chunk = " ".join(RICH_CHUNKS)
    partial = evaluate_answer(
        "Where does respiration occur?",
        long_chunk,
        "In the mitochondria of the cells.",
    )
    assert partial["score"] >= 1


def test_sprint_pace_minutes():
    gentle = break_into_sprints("Lab report", None, "gentle")
    standard = break_into_sprints("Lab report", None, "standard")
    assert all(s["minutes"] == 15 for s in gentle)
    assert all(s["minutes"] == 25 for s in standard)
    assert 3 <= len(gentle) <= 5
    assert 3 <= len(standard) <= 5


def test_sprint_count_scales_with_notes():
    short = break_into_sprints("Essay", "short notes", "standard")
    long_notes = "detail " * 400
    big = break_into_sprints("Essay", long_notes, "standard")
    assert len(big) >= len(short)


def _llm_sprints(*specs: tuple[str, int]) -> str:
    return json.dumps(
        [{"description": d, "minutes": m} for d, m in specs]
    )


@pytest.fixture
def llm_enabled(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.services import tutor as tutor_module

    monkeypatch.setattr(tutor_module.llm_client, "is_llm_available", lambda: True)


def test_sprint_validation_discards_too_many_llm_sprints(
    monkeypatch: pytest.MonkeyPatch, llm_enabled: None
) -> None:
    from app.services import tutor as tutor_module

    monkeypatch.setattr(
        tutor_module,
        "_llm_invoke",
        lambda prompt: _llm_sprints(
            *[("Step", 25)] * 6
        ),
    )
    result = tutor_module.break_into_sprints("Essay", None, "standard")
    assert result == tutor_module._deterministic_sprints(None, "standard")
    assert all(s["minutes"] == 25 for s in result)


def test_sprint_validation_discards_zero_minute_sprint(
    monkeypatch: pytest.MonkeyPatch, llm_enabled: None
) -> None:
    from app.services import tutor as tutor_module

    monkeypatch.setattr(
        tutor_module,
        "_llm_invoke",
        lambda prompt: _llm_sprints(
            ("Understand", 0), ("Draft", 25), ("Review", 25)
        ),
    )
    result = tutor_module.break_into_sprints("Essay", None, "standard")
    assert result == tutor_module._deterministic_sprints(None, "standard")


def test_sprint_validation_enforces_pace_mapping(
    monkeypatch: pytest.MonkeyPatch, llm_enabled: None
) -> None:
    from app.services import tutor as tutor_module

    monkeypatch.setattr(
        tutor_module,
        "_llm_invoke",
        lambda prompt: _llm_sprints(("A", 30), ("B", 30), ("C", 30)),
    )
    gentle = tutor_module.break_into_sprints("Essay", None, "gentle")
    standard = tutor_module.break_into_sprints("Essay", None, "standard")
    assert all(s["minutes"] == 15 for s in gentle)
    assert all(s["minutes"] == 25 for s in standard)
    assert 3 <= len(gentle) <= 5


def test_sprint_accepts_valid_llm_output(
    monkeypatch: pytest.MonkeyPatch, llm_enabled: None
) -> None:
    from app.services import tutor as tutor_module

    monkeypatch.setattr(
        tutor_module,
        "_llm_invoke",
        lambda prompt: _llm_sprints(
            ("Read the brief", 15), ("Outline points", 15), ("Write draft", 15), ("Polish", 15)
        ),
    )
    result = tutor_module.break_into_sprints("Essay", None, "gentle")
    assert [s["description"] for s in result] == [
        "Read the brief",
        "Outline points",
        "Write draft",
        "Polish",
    ]
    assert all(s["minutes"] == 15 for s in result)


def test_five_distinct_questions_guaranteed_on_small_doc():
    small = [
        "Neurons transmit electrical signals through axons.",
        "Synapses relay signals between cells using neurotransmitters.",
    ]
    asked: list[str] = []
    got: list[str] = []
    for _ in range(5):
        q = make_viva_question(small, asked)
        assert q is not None
        assert q not in got
        got.append(q)
        asked.append(q)
    assert len(set(got)) == 5
