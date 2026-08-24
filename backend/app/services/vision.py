import io
import json
import math
from pathlib import Path

_MODEL_PATH = Path(__file__).resolve().parent / "data" / "face_centroids.json"

_POOL = 12
_DIM = _POOL * _POOL * 2
_MIN_SCORE = 0.35

_model: dict | None = None
_loaded_path: Path | None = None


def _load() -> dict | None:
    global _model, _loaded_path
    if _model is not None and _loaded_path == _MODEL_PATH:
        return _model
    try:
        data = json.loads(_MODEL_PATH.read_text(encoding="utf-8"))
        if data.get("means") and data.get("vars") and data.get("feature_mean"):
            _model = data
            _loaded_path = _MODEL_PATH
            return _model
    except Exception:
        pass
    _model = None
    _loaded_path = _MODEL_PATH
    return None


def is_face_model_available() -> bool:
    return _load() is not None


def _featurize(gray: bytes) -> list[float]:
    feats = [0.0] * _DIM
    half = _POOL * _POOL
    for row in range(48):
        base = row * 48
        prow = (row // 4) * _POOL
        for col in range(48):
            v = gray[base + col]
            block = prow + col // 4
            feats[block] += v
            g = 0
            if col < 47:
                g += abs(v - gray[base + col + 1])
            if row < 47:
                g += abs(v - gray[base + 48 + col])
            feats[half + block] += g
    norm = 16.0 * 255.0
    return [f / norm for f in feats]


def detect_face_mood(image_bytes: bytes) -> dict | None:
    """{"label", "score", "runner_up"} from a face photo; None when the
    model or decoder is unavailable, the image is undecodable, or the top
    score is below the honesty threshold."""
    model = _load()
    if model is None or not image_bytes:
        return None
    try:
        from PIL import Image

        with Image.open(io.BytesIO(image_bytes)) as im:
            small = im.convert("L")
            if small.size != (48, 48):
                small = small.resize((48, 48))
            raw = _featurize(small.tobytes())
    except Exception:
        return None

    mean: list[float] = model["feature_mean"]
    std: list[float] = model["feature_std"]
    vec = [(raw[i] - mean[i]) / std[i] for i in range(_DIM)]

    weights: list[tuple[float, str]] = []
    for c, m in model["means"].items():
        var: list[float] = model["vars"][c]
        s: float = float(model.get("priors", {}).get(c, 0.0))
        for i, x in enumerate(vec):
            d = x - m[i]
            s -= 0.5 * (math.log(var[i]) + d * d / var[i])
        weights.append((s, c))

    peak = max(w for w, _ in weights)
    exps = [(math.exp(w - peak), c) for w, c in weights]
    total = sum(e for e, _ in exps) or 1.0
    ranked = sorted(
        ((c, round(e / total, 3)) for e, c in exps), key=lambda t: -t[1]
    )
    label, score = ranked[0]
    if score < _MIN_SCORE:
        return {"label": "", "score": round(score, 3), "runner_up": ""}
    runner_up = ranked[1][0] if len(ranked) > 1 else ""
    return {"label": label, "score": score, "runner_up": runner_up}
