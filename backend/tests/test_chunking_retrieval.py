from app.services.chunking import chunk_text
from app.services.retrieval import search

LONG_TEXT = (
    "Photosynthesis converts light energy into chemical energy inside plants. "
    "Chlorophyll is the pigment that captures sunlight in the leaves. "
    "Water and carbon dioxide are the raw materials for this process. "
    "Glucose and oxygen are produced at the end of photosynthesis. "
    "Respiration releases stored energy from glucose in every living cell. "
    "Mitochondria are the organelles where cellular respiration takes place. "
    "Oxygen is used during respiration to break down glucose completely. "
    "Carbon dioxide and water are released as waste products of respiration. "
    "Plants perform both photosynthesis and respiration throughout their life. "
    "During daylight hours photosynthesis usually exceeds respiration in rate. "
    "At night only respiration continues because there is no sunlight. "
    "Farmers value both processes when planning crop growth cycles. "
)


def _word_count(s: str) -> int:
    return len(s.split())


def test_chunks_respect_target_size():
    chunks = chunk_text(LONG_TEXT, target_words=40, overlap_words=8)
    assert len(chunks) >= 3
    oversized = [c for c in chunks if _word_count(c) > 70]
    assert oversized == []


def test_overlap_present_between_consecutive_chunks():
    chunks = chunk_text(LONG_TEXT, target_words=30, overlap_words=10)
    for prev, nxt in zip(chunks, chunks[1:]):
        tail = prev.split()[-10:]
        head = nxt.split()[:10]
        assert any(w in head for w in tail)


def test_no_content_word_lost():
    chunks = chunk_text(LONG_TEXT, target_words=25, overlap_words=5)
    joined = " ".join(chunks).lower()
    for word in ["chlorophyll", "mitochondria", "glucose", "daylight", "farmers"]:
        assert word in joined


def test_oversized_sentence_split_at_word_boundaries():
    huge = ("alpha beta gamma delta epsilon " * 120).strip() + "."
    chunks = chunk_text(huge, target_words=60, overlap_words=10)
    assert len(chunks) >= 2
    for c in chunks:
        assert _word_count(c) <= 70
    assert chunks[0].startswith("alpha beta gamma")
    assert chunks[-1].rstrip().endswith("epsilon.")
    assert sum(_word_count(c) for c in chunks) >= 600


def test_punctuation_free_text_splits_with_overlap():
    words = [f"w{i}" for i in range(400)]
    text = " ".join(words)
    chunks = chunk_text(text, target_words=50, overlap_words=10)
    assert len(chunks) >= 5
    for c in chunks:
        assert _word_count(c) <= 55
    for prev, nxt in zip(chunks, chunks[1:]):
        assert nxt.split()[:10] == prev.split()[-10:]
    out_words = " ".join(chunks).split()
    assert set(out_words) == set(words)


def test_empty_text_returns_empty_list():
    assert chunk_text("") == []
    assert chunk_text("   ") == []


def test_search_ranks_distinctive_chunk_first():
    chunks = chunk_text(LONG_TEXT, target_words=60, overlap_words=0)
    hits = search(chunks, "Where does respiration take place mitochondria?", top_k=2)
    assert len(hits) == 2
    best = chunks[hits[0]].lower()
    assert "mitochondria" in best or "respiration" in best


def test_search_top_k_respected():
    chunks = chunk_text(LONG_TEXT, target_words=20, overlap_words=0)
    hits = search(chunks, "photosynthesis", top_k=3)
    assert len(hits) == 3
    assert len(set(hits)) == 3


def test_search_empty_inputs():
    assert search([], "anything") == []
    assert search(["text here"], "   ") == []


def test_search_ties_prefer_lower_index():
    chunks = ["apple banana", "banana apple"]
    hits = search(chunks, "banana", top_k=2)
    assert hits[0] == 0
