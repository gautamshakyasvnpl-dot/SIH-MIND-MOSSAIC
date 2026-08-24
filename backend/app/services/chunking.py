import re

_SENTENCE_RE = re.compile(r"[^.!?]+[.!?]+[\s]*|[^.!?]+$")
_WORD_RE = re.compile(r"\S+")


def _words(text: str) -> list[str]:
    return _WORD_RE.findall(text)


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENTENCE_RE.findall(text) if s.strip()]


def _split_oversized(
    sentence: str, target_words: int, overlap_words: int
) -> list[str]:
    words = _words(sentence)
    if len(words) <= target_words:
        return [sentence]
    if 0 < overlap_words < target_words:
        step = max(target_words - overlap_words, 1)
    else:
        step = target_words
    return [" ".join(words[i : i + step]) for i in range(0, len(words), step)]


def chunk_text(
    text: str, target_words: int = 120, overlap_words: int = 20
) -> list[str]:
    if target_words <= 0 or not text or not text.strip():
        return []

    units: list[str] = []
    for sentence in _sentences(text):
        units.extend(_split_oversized(sentence, target_words, overlap_words))
    if not units:
        return []

    chunks: list[str] = []
    current: list[str] = []
    current_words = 0

    def flush() -> None:
        nonlocal current, current_words
        if current:
            chunks.append(" ".join(current))
            tail = _words(chunks[-1])
            if overlap_words > 0 and len(tail) > overlap_words:
                carry = " ".join(tail[-overlap_words:])
                current = [carry]
                current_words = overlap_words
            else:
                current = []
                current_words = 0

    for unit in units:
        n_words = len(_words(unit))
        if current_words + n_words > target_words and current:
            flush()
        current.append(unit)
        current_words += n_words
    if current:
        chunks.append(" ".join(current))

    return [c for c in (c.strip() for c in chunks) if c]
