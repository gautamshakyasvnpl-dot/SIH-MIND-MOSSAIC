import pytest

from app.services.recommender import recommend_format
from app.services.wellbeing import suggest_for_mood

LONG_TEXT = "word " * 1000


def test_low_mood_gets_grounding_and_escalation():
    s = suggest_for_mood(1)
    assert "box breathing" in s.lower()
    assert "counselling" in s.lower()
    assert suggest_for_mood(2) == s


def test_mid_mood_break_nudge():
    s = suggest_for_mood(3)
    assert "break" in s.lower()


def test_high_mood_positive_reinforcement():
    for mood in (4, 5):
        s = suggest_for_mood(mood)
        assert "counselling" not in s.lower()
        assert len(s) > 10


def test_mood_clamped():
    assert suggest_for_mood(0) == suggest_for_mood(1)
    assert suggest_for_mood(9) == suggest_for_mood(5)


def test_recommend_audio_for_audio_affinity():
    r = recommend_format("short", {"modality_affinity": "audio"})
    assert r["format"] == "audio"
    assert "modality_affinity" in r["reason"]
    assert "listening" in r["reason"]


def test_recommend_audio_for_audio_affinity_even_when_noise_sensitive():
    r = recommend_format("short", {"modality_affinity": "audio", "noise_sensitive": True})
    assert r["format"] == "audio"
    assert "modality_affinity" in r["reason"]
    assert set(r) == {"format", "reason"}


def test_recommend_simplified_for_visual():
    r = recommend_format(LONG_TEXT, {"modality_affinity": "visual"})
    assert r["format"] == "simplified_text"
    assert "visual" in r["reason"].lower()


def test_recommend_simplified_for_small_chunks():
    r = recommend_format("x", {"modality_affinity": "text", "chunk_size": "small"})
    assert r["format"] == "simplified_text"
    assert "small chunks" in r["reason"]


def test_long_doc_prefers_audio_unless_noise_sensitive():
    r = recommend_format(LONG_TEXT, {"modality_affinity": "text", "noise_sensitive": False})
    assert r["format"] == "audio"
    r2 = recommend_format(
        LONG_TEXT,
        {"modality_affinity": "text", "noise_sensitive": True, "chunk_size": "large"},
    )
    assert r2["format"] == "original_text"


def test_every_rule_returns_reason_citing_profile():
    cases: list[dict] = [
        {"modality_affinity": "audio"},
        {"modality_affinity": "visual"},
        {"modality_affinity": "text", "chunk_size": "small"},
        {"modality_affinity": "text"},
    ]
    for profile in cases:
        out = recommend_format("", profile)
        assert out["format"] in {"audio", "simplified_text", "original_text"}
        assert isinstance(out["reason"], str) and len(out["reason"]) > 20
