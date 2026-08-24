"""Train the fer2013 face-mood model (offline demo trainer).

Features: each 48x48 grayscale face becomes a 288-dim vector - 4x4 box
pools of pixel intensity plus 4x4 pools of |horizontal|+|vertical|
gradient energy (expressions live in edges, not absolute brightness).
Model: diagonal Gaussian Naive Bayes - single-pass training, pure
stdlib scoring at runtime. pillow is required here and inside
services/vision.py's decoder.

Usage:
    backend\\.venv\\Scripts\\python backend\\scripts\\train_face_model.py
"""

import json
import math
from pathlib import Path

from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[2]
FER_ROOT = REPO_ROOT / "datasets" / "fer2013"
ARTIFACT = REPO_ROOT / "backend" / "app" / "services" / "data" / "face_centroids.json"

POOL = 12
CELL = 4
DIM = POOL * POOL * 2
LABEL_MAP = {"angry": "anger", "happy": "joy", "sad": "sadness"}
CLASSES = ["anger", "disgust", "fear", "joy", "neutral", "sadness", "surprise"]
VAR_EPS = 1e-3


def featurize(path: Path) -> list[float]:
    with Image.open(path) as im:
        small = im.convert("L")
        if small.size != (48, 48):
            small = small.resize((48, 48))
        px = small.tobytes()

    feats = [0.0] * DIM
    half = POOL * POOL
    for row in range(48):
        base = row * 48
        prow = (row // CELL) * POOL
        for col in range(48):
            v = px[base + col]
            block = prow + col // CELL
            feats[block] += v
            g = 0
            if col < 47:
                g += abs(v - px[base + col + 1])
            if row < 47:
                g += abs(v - px[base + 48 + col])
            feats[half + block] += g
    norm = CELL * CELL * 255.0
    return [f / norm for f in feats]


def collect(split: str) -> tuple[list[list[float]], list[str]]:
    vectors: list[list[float]] = []
    labels: list[str] = []
    root = FER_ROOT / split
    if not root.exists():
        return vectors, labels
    for folder in sorted(root.iterdir()):
        label = LABEL_MAP.get(folder.name.lower(), folder.name.lower())
        if label not in CLASSES or not folder.is_dir():
            continue
        for path in folder.iterdir():
            try:
                vectors.append(featurize(path))
                labels.append(label)
            except Exception:
                continue
    return vectors, labels


def main() -> None:
    train_x, train_y = collect("train")
    test_x, test_y = collect("test")
    if not train_x:
        raise SystemExit(f"No training images found under {FER_ROOT}")

    total = [0.0] * DIM
    for vec in train_x:
        for i, v in enumerate(vec):
            total[i] += v
    mean = [t / len(train_x) for t in total]

    sq = [0.0] * DIM
    for vec in train_x:
        for i, v in enumerate(vec):
            d = v - mean[i]
            sq[i] += d * d
    std = [math.sqrt(s / len(train_x)) or 1e-6 for s in sq]

    def standardize(vec: list[float]) -> list[float]:
        return [(v - mean[i]) / std[i] for i, v in enumerate(vec)]

    counts: dict[str, int] = {c: 0 for c in CLASSES}
    s1: dict[str, list[float]] = {c: [0.0] * DIM for c in CLASSES}
    s2: dict[str, list[float]] = {c: [0.0] * DIM for c in CLASSES}

    def observe(vec_std: list[float], label: str) -> None:
        counts[label] += 1
        m = s1[label]
        q = s2[label]
        for i, v in enumerate(vec_std):
            m[i] += v
            q[i] += v * v

    for raw, label in zip(train_x, train_y):
        observe(standardize(raw), label)

    model: dict[str, dict[str, list[float]]] = {}
    priors: dict[str, float] = {}
    for c in CLASSES:
        k = counts[c]
        if not k:
            continue
        mu = [v / k for v in s1[c]]
        var = [
            max(s2[c][i] / k - mu[i] * mu[i], VAR_EPS) for i in range(DIM)
        ]
        model[c] = {"mu": mu, "var": var}
        priors[c] = math.log(k / len(train_x))

    def loglik(vec_std: list[float], c: str) -> float:
        m = model[c]
        mu, var = m["mu"], m["var"]
        s = priors[c]
        for i, x in enumerate(vec_std):
            d = x - mu[i]
            s -= 0.5 * (math.log(var[i]) + d * d / var[i])
        return s

    def predict(raw: list[float]) -> str | None:
        vec = standardize(raw)
        best_label, best_s = None, -float("inf")
        for c in model:
            s = loglik(vec, c)
            if s > best_s:
                best_label, best_s = c, s
        return best_label

    correct_train = sum(1 for r, y in zip(train_x, train_y) if predict(r) == y)
    correct_test = sum(1 for r, y in zip(test_x, test_y) if predict(r) == y)
    train_accuracy = correct_train / len(train_x)
    accuracy = correct_test / len(test_x) if test_x else 0.0

    artifact = {
        "version": 2,
        "source": "fer2013 (Kaggle FER2013)",
        "pool": POOL,
        "classes": sorted(model),
        "feature_mean": [round(v, 6) for v in mean],
        "feature_std": [round(v, 6) for v in std],
        "priors": {c: round(p, 5) for c, p in priors.items()},
        "means": {
            c: [round(v, 5) for v in m["mu"]] for c, m in model.items()
        },
        "vars": {
            c: [round(v, 6) for v in m["var"]] for c, m in model.items()
        },
        "meta": {
            "train_images": len(train_x),
            "test_images": len(test_x),
            "train_accuracy": round(train_accuracy, 4),
            "test_accuracy": round(accuracy, 4),
        },
    }

    ARTIFACT.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT.write_text(json.dumps(artifact), encoding="utf-8")

    print(f"train: {len(train_x)}  test: {len(test_x)}  classes: {sorted(model)}")
    print(f"gnb train_accuracy: {train_accuracy:.4f}  test_accuracy: {accuracy:.4f}")
    print(f"wrote: {ARTIFACT} ({ARTIFACT.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
