import json
import math
import re
from collections import Counter
from pathlib import Path

_MODEL_PATH = Path(__file__).resolve().parent / "data" / "emotion_nb.json"

_TOKEN_RE = re.compile(r"[a-z']+")

_LEXICON: dict[str, tuple[str, ...]] = {
    "anger": ("angry", "furious", "annoyed", "irritated", "frustrated", "outraged"),
    "fear": ("scared", "anxious", "nervous", "worried", "panicked", "terrified", "afraid"),
    "sadness": ("sad", "down", "lonely", "miserable", "depressed", "crying", "hopeless"),
    "joy": ("happy", "excited", "thrilled", "delighted", "glad", "cheerful"),
    "disgust": ("disgusted", "grossed", "revolted"),
    "surprise": ("surprised", "shocked", "stunned"),
}

_model: dict | None = None
_loaded_path: Path | None = None


def _load() -> dict | None:
    global _model, _loaded_path
    if _model is not None and _loaded_path == _MODEL_PATH:
        return _model
    try:
        data = json.loads(_MODEL_PATH.read_text(encoding="utf-8"))
        if isinstance(data.get("token_counts"), dict) and data.get("classes"):
            _model = data
            _loaded_path = _MODEL_PATH
            return _model
    except Exception:
        pass
    _model = None
    _loaded_path = _MODEL_PATH
    return None


def is_emotion_model_available() -> bool:
    return _load() is not None


def detect_emotion(text: str) -> dict | None:
    """{"label", "score"} for note text; None when unavailable or empty."""
    model = _load()
    if model is None or not text or not text.strip():
        return None

    tokens = {t for t in _TOKEN_RE.findall(text.lower())}

    votes: Counter[str] = Counter()
    for label, cues in _LEXICON.items():
        votes[label] += sum(1 for cue in cues if cue in tokens)
    lexicon_label, lexicon_votes = votes.most_common(1)[0] if votes else (None, 0)

    nb_label, nb_score = _nb_classify(model, tokens)
    if lexicon_votes > 0 and lexicon_label is not None:
        return {"label": lexicon_label, "score": round(min(1.0, 0.6 + 0.1 * lexicon_votes), 3)}
    return {"label": nb_label, "score": nb_score} if nb_label else None


def _nb_classify(model: dict, tokens: set[str]) -> tuple[str | None, float]:
    counts: dict[str, list[int]] = model["token_counts"]
    classes: list[str] = model["classes"]
    log_prior: list[float] = model["log_prior"]
    totals: list[int] = model["class_totals"]
    alpha = float(model.get("alpha", 0.5))
    vocab_size = max(len(counts), 1)

    scores = list(log_prior)
    matched = 0
    for tok in tokens:
        row = counts.get(tok)
        if row is None:
            continue
        matched += 1
        for i in range(len(classes)):
            scores[i] += math.log(row[i] + alpha) - math.log(totals[i] + alpha * vocab_size)
    if matched == 0:
        return None, 0.0

    peak = max(scores)
    weights = [math.exp(s - peak) for s in scores]
    total = sum(weights)
    best = weights.index(max(weights))
    return classes[best], round(weights[best] / total, 3)
