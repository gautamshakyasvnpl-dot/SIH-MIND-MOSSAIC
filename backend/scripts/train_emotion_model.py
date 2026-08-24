"""Train a tiny pure-python Naive Bayes emotion classifier on MELD.

Offline demo trainer: reads datasets/emotion/MELD_train_sent_emo.csv,
writes backend/app/services/data/emotion_nb.json. Stdlib only, so the
runtime service never needs numpy/pandas/sklearn.

Usage:
    backend\\.venv\\Scripts\\python backend\\scripts\\train_emotion_model.py
"""

import csv
import json
import math
import re
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TRAIN_CSV = REPO_ROOT / "datasets" / "emotion" / "MELD_train_sent_emo.csv"
ARTIFACT = REPO_ROOT / "backend" / "app" / "services" / "data" / "emotion_nb.json"

MIN_TOKEN_TOTAL = 1
MAX_VOCAB = 20000
ALPHA = 0.1

_TOKEN_RE = re.compile(r"[a-z']+")


def tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


def main() -> None:
    if not TRAIN_CSV.exists():
        raise SystemExit(
            f"Training data not found: {TRAIN_CSV}. "
            "Download MELD train_sent_emo.csv (see datasets/README.md)."
        )

    per_class: dict[str, Counter] = {}
    class_docs: Counter = Counter()
    examples: list[tuple[list[str], str]] = []

    with TRAIN_CSV.open(encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            label = (row.get("Emotion") or "").strip().lower()
            utterance = row.get("Utterance") or ""
            tokens = tokenize(utterance)
            if not label or not tokens:
                continue
            per_class.setdefault(label, Counter()).update(tokens)
            class_docs[label] += 1
            examples.append((tokens, label))

    total_by_token: Counter = Counter()
    for counts in per_class.values():
        total_by_token.update(counts)

    vocab = [
        tok
        for tok, _ in total_by_token.most_common(MAX_VOCAB)
        if total_by_token[tok] >= MIN_TOKEN_TOTAL
    ]
    vocab_set = set(vocab)

    classes = sorted(per_class)
    n_docs = sum(class_docs.values())
    log_prior = [math.log(class_docs[c] / n_docs) for c in classes]

    token_counts: dict[str, list[int]] = {tok: [] for tok in vocab}
    for c in classes:
        cc = per_class[c]
        for tok in vocab:
            token_counts[tok].append(cc.get(tok, 0))

    class_totals = [
        sum(token_counts[tok][i] for tok in vocab) for i in range(len(classes))
    ]

    def score(tokens: set[str], i: int) -> float:
        s = log_prior[i]
        denom_log = math.log(class_totals[i] + ALPHA * len(vocab))
        for tok in tokens:
            if tok in vocab_set:
                s += math.log(token_counts[tok][i] + ALPHA) - denom_log
        return s

    correct = 0
    for tokens, gold in examples:
        token_set = {t for t in tokens if t in vocab_set}
        best = max(range(len(classes)), key=lambda i: score(token_set, i))
        if classes[best] == gold:
            correct += 1

    accuracy = correct / len(examples) if examples else 0.0

    artifact = {
        "version": 1,
        "source": "MELD train_sent_emo.csv",
        "alpha": ALPHA,
        "classes": classes,
        "log_prior": [round(p, 6) for p in log_prior],
        "class_totals": class_totals,
        "token_counts": token_counts,
        "meta": {"train_examples": len(examples), "train_accuracy": round(accuracy, 4)},
    }

    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps(artifact), encoding="utf-8")

    print(f"classes: {classes}")
    print(f"examples: {len(examples)}  vocab: {len(vocab)}")
    print(f"train_accuracy: {accuracy:.4f}")
    print(f"wrote: {ARTIFACT} ({ARTIFACT.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
