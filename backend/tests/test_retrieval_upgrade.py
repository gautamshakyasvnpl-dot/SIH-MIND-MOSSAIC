import pytest

from app.services.recommender import recommend_format
from app.services.retrieval import (
    cosine,
    embed_texts,
    is_semantic_available,
    search,
    search_with_embeddings,
)

RICH = [
    "Photosynthesis captures sunlight with chlorophyll in leaves.",
    "Mitochondria are where cellular respiration reactions occur.",
]


def test_search_with_embeddings_falls_back_lexically():
    idx = search_with_embeddings([None, None], None, RICH, "mitochondria respiration", top_k=1)
    assert idx == [1]
    assert search(RICH, "mitochondria", top_k=2) == [1, 0]


def test_cosine_basics():
    assert cosine([1, 0], [1, 0]) == 1.0
    assert cosine([1, 0], [0, 1]) == 0.0
    assert cosine([], []) == 0.0


def test_embed_texts_none_without_key(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    assert is_semantic_available() is False
    assert embed_texts(["hello"]) is None


def test_usage_history_overrides_base_rule():
    base = recommend_format(
        "short", {"modality_affinity": "text", "chunk_size": "large"}
    )
    assert base["format"] == "original_text"

    learned = recommend_format(
        "short",
        {"modality_affinity": "text", "chunk_size": "large"},
        {"simplified_text": 3},
    )
    assert learned["format"] == "simplified_text"
    assert "3 times before" in learned["reason"]


def test_usage_below_threshold_ignored():
    r = recommend_format("x", {}, {"audio": 1})
    assert "times before" not in r["reason"]
