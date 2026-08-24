import os
import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app  # noqa: E402


@pytest.fixture(scope="module")
def client() -> TestClient:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def auth(client: TestClient) -> dict[str, str]:
    email = f"alias_{uuid.uuid4().hex[:8]}@test.com"
    r = client.post(
        "/api/auth/register",
        json={"email": email, "password": "password123", "display_name": "AL"},
    )
    headers = {"Authorization": f"Bearer {r.json()['token']}"}
    consent = client.post("/api/consents", headers=headers, json={"telemetry": True})
    assert consent.status_code == 200, consent.text
    return headers


TEXT = (
    "Convolutions slide a kernel across an input signal. Each output value is a "
    "weighted sum of neighbouring samples. For example, image blur is just a "
    "convolution with an averaging kernel. This single operation powers most "
    "classical computer vision pipelines."
)


def test_alias_simplify_returns_short_or_equal(client, auth):
    r = client.post(
        "/api/adaptive/simplify", headers=auth, json={"text": TEXT, "level": 2}
    ).json()
    assert r["engine"].startswith("heuristic")
    assert len(r["text"]) <= len(TEXT)


def test_alias_analogy_contains_marker(client, auth):
    r = client.post(
        "/api/adaptive/analogy", headers=auth, json={"text": "Recursion means a function calling itself.", "level": 4}
    ).json()
    assert "Analogy:" in r["text"]


def test_alias_feedback_updates_preferences(client, auth):
    before = client.get("/api/preferences", headers=auth).json()["scores"]["examples"]
    r = client.post("/api/feedback", headers=auth, json={"event": "requested_example"})
    after = r.json()["scores"]["examples"]
    assert after > before


def test_alias_learner_profile_get_patch(client, auth):
    got = client.get("/api/learner/profile", headers=auth).json()
    assert isinstance(got, dict)
    patched = client.patch(
        "/api/learner/profile", headers=auth, json={"pace": "gentle"}
    ).json()
    assert patched["pace"] == "gentle"
    assert client.get("/api/profile", headers=auth).json()["pace"] == "gentle"


def test_voice_synthesize_mocked(client, auth, monkeypatch):
    from pathlib import Path

    from app.services import tts as tts_mod

    def fake(text, out_path: Path):
        out_path.write_bytes(b"ID3fake")
        return out_path, "ok"

    monkeypatch.setattr(tts_mod, "synthesize_speech_bounded", fake)
    r = client.post("/api/voice/synthesize", headers=auth, json={"text": "hello"})
    assert r.status_code == 200
    assert r.json()["audio_url"].startswith("/api/audio/")


def test_voice_synthesize_requires_text(client, auth):
    r = client.post("/api/voice/synthesize", headers=auth, json={})
    assert r.status_code == 400


def test_cors_allows_configured_origin(client):
    origin = os.environ.get("ALLOWED_ORIGINS_TEST", "http://localhost:5173")
    r = client.get("/docs", headers={"Origin": origin})
    assert r.headers.get("access-control-allow-origin") == origin


def test_explain_transforms_via_canonical_route(client, auth):
    b = client.post(
        "/api/documents/explain",
        headers=auth,
        json={"text": "One. Two. Three sentences here for bullets.", "level": 4, "transform": "bullets"},
    ).json()
    assert b["text"].startswith("- ")
    s = client.post(
        "/api/documents/explain",
        headers=auth,
        json={"text": TEXT, "level": 4, "transform": "summary"},
    ).json()
    assert len(s["text"]) < len(TEXT)
