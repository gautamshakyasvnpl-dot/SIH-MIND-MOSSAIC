import math
import os
from collections import Counter

import re

_TOKEN_RE = re.compile(r"\w+")

_STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "is", "are", "was",
    "were", "for", "on", "with", "as", "by", "at", "from", "it", "this",
    "that", "be", "has", "have", "had", "not", "but", "they", "their",
    "its", "what", "how", "why", "do", "does", "did", "can", "could",
    "will", "would", "about", "into", "over", "under", "which", "who",
}

_EMBED_MODEL = os.environ.get("GEMINI_EMBED_MODEL", "gemini-embedding-001")


def _tokens(text: str) -> list[str]:
    return [t for t in _TOKEN_RE.findall(text.lower()) if t not in _STOPWORDS]


def search(chunks: list[str], query: str, top_k: int = 2) -> list[int]:
    if not chunks or not query.strip() or top_k <= 0:
        return []

    chunk_tokens = [_tokens(c) for c in chunks]
    query_tokens = _tokens(query)
    if not query_tokens or all(not t for t in chunk_tokens):
        return []

    n_docs = len(chunks)
    df: Counter[str] = Counter()
    for toks in chunk_tokens:
        df.update(set(toks))

    idf = {
        term: math.log((n_docs + 1) / (count + 1)) + 1
        for term, count in df.items()
    }

    def tfidf(toks: list[str]) -> dict[str, float]:
        counts = Counter(toks)
        total = len(toks)
        return {
            term: (cnt / total) * idf.get(term, math.log((n_docs + 1) / 1) + 1)
            for term, cnt in counts.items()
        }

    q_vec = tfidf(query_tokens)
    q_norm = math.sqrt(sum(v * v for v in q_vec.values()))

    scores: list[tuple[float, int]] = []
    for idx, toks in enumerate(chunk_tokens):
        c_vec = tfidf(toks)
        c_norm = math.sqrt(sum(v * v for v in c_vec.values()))
        if q_norm == 0 or c_norm == 0:
            scores.append((0.0, idx))
            continue
        dot = sum(q_vec[t] * c_vec[t] for t in q_vec if t in c_vec)
        scores.append((dot / (q_norm * c_norm), idx))

    ranked = sorted(scores, key=lambda s: (-s[0], s[1]))
    return [idx for _, idx in ranked[:top_k]]


def is_semantic_available() -> bool:
    return bool(os.environ.get("GEMINI_API_KEY"))


def embed_texts(texts: list[str]) -> list[list[float]] | None:
    """Gemini embeddings; None when unavailable or on any failure."""
    if not texts or not is_semantic_available():
        return None
    try:
        from google import genai

        client = genai.Client()
        result = client.models.embed_content(
            model=_EMBED_MODEL,
            contents=list(texts),
        )
        vectors = [list(e.values) for e in result.embeddings]
        if len(vectors) != len(texts) or any(not v for v in vectors):
            return None
        return vectors
    except Exception:
        return None


def cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def search_with_embeddings(
    chunk_vectors: list[list[float] | None],
    query_vector: list[float] | None,
    chunks: list[str],
    query: str,
    top_k: int = 2,
) -> list[int]:
    """Semantic ranking when vectors exist for every chunk + the query;
    otherwise falls back to lexical TF-IDF."""
    if (
        top_k <= 0
        or not chunks
        or query_vector is None
        or any(v is None for v in chunk_vectors)
    ):
        return search(chunks, query, top_k=top_k)
    scored = [
        (cosine(query_vector, v), i)
        for i, v in enumerate(chunk_vectors)
    ]
    ranked = sorted(scored, key=lambda s: (-s[0], s[1]))
    return [i for _, i in ranked[:top_k]]
