"""Adaptive reader: concept cards, explanation ladder, practice quizzes.

All functions are deterministic heuristics (labelled engine="heuristic")
so the demo works with no LLM key. The ladder and quiz never claim to be
AI-generated when they are not.
"""

import hashlib
import re

_SENT_RE = re.compile(r"(?<=[.!?])\s+")
_WORD_RE = re.compile(r"[a-zA-Z']+")

_STOPWORDS = {
    "the", "a", "an", "and", "or", "of", "to", "in", "is", "are", "was",
    "were", "for", "on", "with", "as", "by", "at", "from", "that", "this",
    "it", "its", "be", "has", "have", "had", "not", "but", "they", "their",
    "which", "into", "can", "will", "would", "when", "then", "than",
}

_EXAMPLE_RE = re.compile(r"\b(for example|e\.g\.|such as|for instance)\b", re.I)


def _sentences(text: str) -> list[str]:
    return [s.strip() for s in _SENT_RE.split((text or "").strip()) if s.strip()]


def _title_of(sentence: str, max_words: int = 7) -> str:
    clause = re.split(r"[,;:]", sentence, maxsplit=1)[0]
    words = clause.split()
    return " ".join(words[:max_words]).rstrip(".!?") or "Concept"


def build_cards(text: str, cards_count: int = 5) -> list[dict]:
    sentences = [s for s in _sentences(text) if len(s.split()) >= 4]
    if not sentences:
        return []
    per_card = max(1, -(-len(sentences) // cards_count))
    cards: list[dict] = []
    for idx in range(min(cards_count, -(-len(sentences) // per_card))):
        group = sentences[idx * per_card : (idx + 1) * per_card]
        if not group:
            continue
        example = next(
            (s for s in group if _EXAMPLE_RE.search(s)), None
        )
        simple = group[0]
        if len(group) > 1:
            simple = " ".join(group[: max(1, len(group) // 2)])
        cards.append(
            {
                "index": idx,
                "title": _title_of(group[0]),
                "simple": simple,
                "technical": " ".join(group),
                "example": example,
                "has_visual": True,
                "concept": _title_of(group[0], 4),
            }
        )
    return cards


def explain_ladder(text: str, level: int, context: str = "") -> tuple[int, str]:
    """Levels 1..5; deterministic simplification / deepening."""
    level = max(1, min(5, int(level)))
    sentences = _sentences(text)
    if not sentences:
        return level, text or ""
    base = sentences[0]

    if level == 1:
        words = base.split()
        return level, (" ".join(words[:14]) + ("…" if len(words) > 14 else "")).rstrip(",")
    if level == 2:
        clauses = re.split(r"[,;]", base)
        keep = [c.strip() for c in clauses if len(c.split()) <= 12][:2]
        return level, (" ".join(keep) or base).rstrip(",;")
    if level == 3:
        key = _most_significant_word(base)
        return level, (
            f"Analogy: think of {key or 'this idea'} like a recipe — a few simple "
            f"parts combine in a set order to give you something more useful than "
            f"each part alone. In short: {base}"
        )
    if level == 4:
        return level, text.strip()

    extra = _sentences(context)[:2] if context else []
    detail = " ".join([text.strip()] + extra)
    math_bits = [s for s in sentences if any(ch in s for ch in "=∑∫+−×/")]
    if math_bits:
        detail += " Key relations: " + " ".join(math_bits[:2])
    return level, detail


def _significant_words(sentence: str) -> list[str]:
    return [w.lower() for w in _WORD_RE.findall(sentence) if w.lower() not in _STOPWORDS]


def _most_significant_word(sentence: str) -> str:
    words = _significant_words(sentence)
    return max(words, key=len) if words else ""


def make_quiz(text: str, count: int = 3) -> list[dict]:
    """Cloze questions. answer_index included on purpose: this is a
    self-study practice mode, not a proctored exam."""
    pool = [
        s
        for s in _sentences(text)
        if len(s.split()) >= 8 and len(_significant_words(s)) >= 3
    ]
    vocab = sorted({w for w in _significant_words(text) if len(w) >= 5})
    items: list[dict] = []
    used_sentences: set[str] = set()
    for sentence in pool:
        if len(items) >= max(1, min(count, 6)):
            break
        if sentence in used_sentences:
            continue
        target = _most_significant_word(sentence)
        if not target or len(vocab) < 4:
            continue
        match = re.search(re.escape(target), sentence, re.I)
        if not match:
            continue
        blanked = (
            sentence[: match.start()]
            + "______"
            + sentence[match.end() :]
        )
        distractors = [
            w
            for w in vocab
            if w != target.lower()
            and abs(len(w) - len(target)) <= 4
        ]
        seed = int(hashlib.sha256(sentence.encode()).hexdigest(), 16)
        picked: list[str] = []
        for offset in range(len(distractors)):
            word = distractors[(seed >> (offset % 16)) % len(distractors)]
            if word not in picked:
                picked.append(word)
            if len(picked) == 3:
                break
        while len(picked) < 3:
            filler = f"option-{len(picked) + 1}"
            picked.append(filler)
        options = [*picked, target]
        order = [(seed >> i) % 97 for i in range(4)]
        paired = sorted(zip(options, order), key=lambda t: t[1])
        ordered = [w for w, _ in paired]
        items.append(
            {
                "id": hashlib.sha256(blanked.encode()).hexdigest()[:12],
                "question": f"Fill the gap: {blanked}",
                "options": ordered,
                "answer_index": ordered.index(target),
                "concept": _title_of(sentence, 4),
            }
        )
        used_sentences.add(sentence)
    return items


def to_bullets(text: str) -> str:
    sentences = _sentences(text)
    return "\n".join(f"- {s}" for s in sentences[:6]) or f"- {text.strip()}"


def summarize(text: str, max_sentences: int = 2) -> str:
    sentences = [s for s in _sentences(text) if len(s.split()) >= 4]
    if not sentences:
        return text.strip()
    ranked = sorted(sentences, key=lambda s: len(_significant_words(s)), reverse=True)
    keep = set(id(s) for s in ranked[:max_sentences])
    ordered = [s for s in sentences if id(s) in keep]
    return " ".join(ordered)


def extract_example(text: str) -> str | None:
    for s in _sentences(text):
        if _EXAMPLE_RE.search(s):
            return s
    return None


def prioritize(items: list[str]) -> dict[str, list[str]]:
    """Split study topics into three priority levels (wellbeing support)."""
    clean = [i.strip() for i in items if i.strip()]
    n = len(clean)
    high_cut = -(-n // 3)
    med_cut = high_cut + (-(-max(n - high_cut, 0) // 2))
    return {
        "high": clean[:high_cut],
        "medium": clean[high_cut:med_cut],
        "low": clean[med_cut:],
    }
