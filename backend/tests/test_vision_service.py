import io
import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app  # noqa: E402
from app.services import vision  # noqa: E402

pil = pytest.importorskip("PIL")


def make_image_bytes(mode: str = "L", size: tuple[int, int] = (48, 48), value: int = 128) -> bytes:
    from PIL import Image

    buf = io.BytesIO()
    Image.new(mode, size, value).save(buf, format="PNG")
    return buf.getvalue()


def test_face_model_available():
    assert vision.is_face_model_available() is True


def test_detect_on_synthetic_image():
    out = vision.detect_face_mood(make_image_bytes())
    assert out is not None
    assert set(out) >= {"label", "score"}
    assert 0.0 <= out["score"] <= 1.0


def test_detect_corrupt_bytes_is_none():
    assert vision.detect_face_mood(b"not-an-image") is None
    assert vision.detect_face_mood(b"") is None


def test_low_confidence_returns_empty_label_not_guess(monkeypatch):
    fake = {
        "means": {
            "joy": [0.0] * (12 * 12 * 2),
            "sadness": [0.0] * (12 * 12 * 2),
            "fear": [0.0] * (12 * 12 * 2),
        },
        "vars": {
            "joy": [1e-6] * (12 * 12 * 2),
            "sadness": [1e-6] * (12 * 12 * 2),
            "fear": [1e-6] * (12 * 12 * 2),
        },
        "priors": {"joy": 0.0, "sadness": 0.0, "fear": 0.0},
        "feature_mean": [0.5] * (12 * 12 * 2),
        "feature_std": [1.0] * (12 * 12 * 2),
    }
    monkeypatch.setattr(vision, "_load", lambda: fake)
    out = vision.detect_face_mood(make_image_bytes(value=200))
    assert out is not None and out["label"] == ""


@pytest.fixture(scope="module")
def client() -> TestClient:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def auth(client: TestClient) -> dict[str, str]:
    email = f"face_{uuid.uuid4().hex[:8]}@test.com"
    r = client.post(
        "/api/auth/register",
        json={"email": email, "password": "password123", "display_name": "Face"},
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


def test_face_route_absent_from_release_surface(client, auth):
    r = client.post(
        "/api/emotion/face",
        headers=auth,
        files={"file": ("face.png", io.BytesIO(make_image_bytes()), "image/png")},
    )
    assert r.status_code == 404


def test_text_emotion_still_works_via_checkins(client, auth):
    r = client.post("/api/checkins", headers=auth, json={"mood": 3, "note": "I am so angry right now"})
    assert r.status_code == 200, r.text
    assert "suggestion" in r.json()
