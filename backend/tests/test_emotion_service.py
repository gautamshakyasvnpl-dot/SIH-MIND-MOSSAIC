from app.services import emotion
from app.services.wellbeing import suggest_for_mood


def test_model_available():
    assert emotion.is_emotion_model_available() is True


def test_detect_returns_label_and_score():
    out = emotion.detect_emotion("I am so happy and excited, this is wonderful news")
    assert out is not None
    assert out["label"] in {"anger", "disgust", "fear", "joy", "neutral", "sadness", "surprise"}
    assert 0.0 < out["score"] <= 1.0


def test_detect_empty_text_is_none():
    assert emotion.detect_emotion("") is None
    assert emotion.detect_emotion("   ") is None


def test_detect_unseen_words_only_is_none(monkeypatch):
    monkeypatch.setattr(
        emotion,
        "_load",
        lambda: {
            "classes": ["joy", "sadness"],
            "log_prior": [-0.6, -0.6],
            "class_totals": [10, 10],
            "alpha": 0.5,
            "token_counts": {"happy": [9, 0], "cry": [0, 9]},
        },
    )
    assert emotion.detect_emotion("xyzzyq") is None


def test_sad_note_skews_away_from_joy():
    happy = emotion.detect_emotion("I am thrilled and delighted about the win")
    sad = emotion.detect_emotion(
        "I feel miserable and lonely, everything went wrong and I keep crying"
    )
    assert happy is not None and sad is not None
    assert happy["label"] == "joy"
    assert sad["label"] != "joy"


def test_lexicon_covers_words_rare_in_training_data():
    assert emotion.detect_emotion("I am so angry right now")["label"] == "anger"
    assert emotion.detect_emotion("I am anxious about the deadline")["label"] == "fear"


def test_plain_fact_stays_neutral():
    out = emotion.detect_emotion("the meeting is at noon in room 4")
    assert out is not None
    assert out["label"] in {"neutral", "surprise"}


def test_low_mood_keeps_crisis_copy_even_with_emotion():
    s = suggest_for_mood(1, "sadness")
    assert "box breathing" in s.lower()
    assert "counselling" in s.lower()
    assert "heavy-hearted" in s.lower()


def test_emotion_ack_appended_without_breaking_mid_mood_copy():
    s = suggest_for_mood(3)
    s2 = suggest_for_mood(3, "anger")
    assert "break" in s.lower()
    assert "frustrated" in s2.lower()
    assert len(s2) > len(s)


def test_no_emotion_matches_original_behaviour():
    assert suggest_for_mood(4) == suggest_for_mood(4, None)
