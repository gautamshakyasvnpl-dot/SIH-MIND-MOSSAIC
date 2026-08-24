import io
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
    email = f"w3_{uuid.uuid4().hex[:8]}@test.com"
    r = client.post(
        "/api/auth/register",
        json={"email": email, "password": "password123", "display_name": "W3"},
    )
    assert r.status_code == 200, r.text
    headers = {"Authorization": f"Bearer {r.json()['token']}"}
    consent = client.post("/api/consents", headers=headers, json={"voice": True})
    assert consent.status_code == 200, consent.text
    return headers


@pytest.fixture(scope="module")
def doc_id(client: TestClient, auth: dict[str, str]) -> str:
    text = ("Photosynthesis captures sunlight. " * 30).strip()
    files = {"file": ("w3.txt", io.BytesIO(text.encode()), "text/plain")}
    r = client.post("/api/documents", headers=auth, files=files)
    assert r.status_code == 200, r.text
    return r.json()["id"]


def test_checkin_low_mood_flow(
    client: TestClient, auth: dict[str, str]
) -> None:
    r = client.post(
        "/api/checkins", headers=auth, json={"mood": 1, "note": "tough day"}
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["mood"] == 1 and body["note"] == "tough day"
    assert "box breathing" in body["suggestion"].lower()
    assert "counselling" in body["suggestion"].lower()

    listing = client.get("/api/checkins", headers=auth).json()["items"]
    assert len(listing) == 1 and listing[0]["id"] == body["id"]

    r = client.post("/api/checkins", headers=auth, json={"mood": 9})
    assert r.status_code == 422

    r = client.post("/api/checkins", headers=auth, json={"mood": 0})
    assert r.status_code == 422


def test_recommend_endpoint(
    client: TestClient, auth: dict[str, str], doc_id: str
) -> None:
    r = client.put(
        "/api/profile", headers=auth, json={"modality_affinity": "audio"}
    )
    r = client.get(f"/api/documents/{doc_id}/recommend", headers=auth)
    assert r.status_code == 200, r.text
    body = r.json()
    assert set(body) == {"format", "reason"}
    assert body["format"] == "audio"
    assert "modality_affinity" in body["reason"]

    r = client.get(f"/api/documents/{doc_id}/recommend", headers={})
    assert r.status_code in (401, 403)


def test_stt_without_key_returns_empty(
    client: TestClient,
    auth: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    r = client.post(
        "/api/stt",
        headers=auth,
        files={"file": ("note.webm", b"RIFFfakeaudio", "audio/webm")},
    )
    assert r.status_code == 200, r.text
    assert r.json() == {"text": "", "engine": ""}

    r = client.post(
        "/api/stt",
        headers=auth,
        files={"file": ("note.exe", b"x", "application/octet-stream")},
    )
    assert r.status_code == 400


def test_checkin_listing_caps_at_fifty(client: TestClient) -> None:
    email = f"cap_{uuid.uuid4().hex[:8]}@test.com"
    r = client.post(
        "/api/auth/register",
        json={"email": email, "password": "password123", "display_name": "Cap"},
    )
    assert r.status_code == 200, r.text
    headers = {"Authorization": f"Bearer {r.json()['token']}"}

    for _ in range(55):
        r = client.post("/api/checkins", headers=headers, json={"mood": 4, "note": None})
        assert r.status_code == 200, r.text

    listing = client.get("/api/checkins", headers=headers).json()["items"]
    assert len(listing) == 50
    created = [item["created_at"] for item in listing]
    assert created == sorted(created, reverse=True)
