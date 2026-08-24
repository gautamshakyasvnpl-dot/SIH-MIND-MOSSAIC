import uuid

import pytest
from fastapi.testclient import TestClient

from app.main import app
from conftest import SAMPLE_TXT


def test_full_api_smoke_flow() -> None:
    with TestClient(app) as client:
        _run_flow(client)


def _run_flow(client: TestClient) -> None:
    email = f"user-{uuid.uuid4().hex[:10]}@example.com"

    register = client.post(
        "/api/auth/register",
        json={"email": email, "password": "Str0ngPassw0rd!", "display_name": "Smoke Tester"},
    )
    assert register.status_code == 200, register.text
    token = register.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    me = client.get("/api/auth/me", headers=headers)
    assert me.status_code == 200, me.text
    assert me.json()["email"] == email

    profile = client.get("/api/profile", headers=headers)
    assert profile.status_code == 200, profile.text
    assert profile.json()["modality_affinity"] in {"text", "audio", "visual"}

    put_profile = client.put(
        "/api/profile", json={"font_style": "dyslexia_friendly"}, headers=headers
    )
    assert put_profile.status_code == 200, put_profile.text
    profile_after = client.get("/api/profile", headers=headers)
    assert profile_after.status_code == 200
    assert profile_after.json()["font_style"] == "dyslexia_friendly"
    assert "modality_affinity" in profile_after.json()

    consents_post = client.post(
        "/api/consents",
        json={"voice": True, "telemetry": False, "memory": True},
        headers=headers,
    )
    assert consents_post.status_code == 200, consents_post.text
    consents_get = client.get("/api/consents", headers=headers)
    assert consents_get.status_code == 200, consents_get.text
    assert consents_get.json() == {"voice": True, "telemetry": False, "memory": True}

    upload = client.post(
        "/api/documents",
        files={"file": ("sample.txt", SAMPLE_TXT.encode("utf-8"), "text/plain")},
        headers=headers,
    )
    assert upload.status_code == 200, upload.text
    doc = upload.json()
    doc_id = doc["id"]
    assert set(doc) == {"id", "filename", "doc_type", "char_count", "created_at"}
    assert doc["doc_type"] == "txt"
    assert doc["filename"] == "sample.txt"

    listing = client.get("/api/documents", headers=headers)
    assert listing.status_code == 200, listing.text
    assert len(listing.json()["items"]) == 1

    adapt = client.post(
        f"/api/documents/{doc_id}/adapt",
        json={"formats": ["simplified_text", "tts_audio"]},
        headers=headers,
    )
    assert adapt.status_code == 200, adapt.text
    payload = adapt.json()
    assert payload["document_id"] == doc_id
    assert payload["used_llm"] is False
    results = payload["results"]
    assert len(results) == 2
    by_format = {item["format"]: item for item in results}
    assert by_format["simplified_text"]["status"] == "ok"
    assert isinstance(by_format["simplified_text"]["content"], str)
    assert by_format["simplified_text"]["content"].strip()

    delete = client.delete(f"/api/documents/{doc_id}", headers=headers)
    assert delete.status_code == 204, delete.text

    gone = client.get(f"/api/documents/{doc_id}", headers=headers)
    assert gone.status_code == 404, gone.text
