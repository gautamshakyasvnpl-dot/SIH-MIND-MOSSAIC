import base64
import io
import json
import time
import uuid

import pytest
from fastapi.testclient import TestClient

from app.api import media as media_api  # noqa: E402
from app.main import app  # noqa: E402

LONG_TEXT = (
    "Photosynthesis converts light energy into chemical energy inside plants. "
    "Chlorophyll is the pigment that captures sunlight in the leaves. "
    "Water and carbon dioxide are the raw materials for this process. "
    "Glucose and oxygen are produced at the end of photosynthesis. "
    "Cellular respiration releases energy from glucose in living cells. "
    "Mitochondria are the organelles where respiration reactions occur. "
    "Oxygen is used during respiration to break down glucose completely. "
    "Carbon dioxide and water are released as waste products of respiration. "
    "Plants perform both photosynthesis and respiration throughout their life. "
    "During daylight hours photosynthesis usually exceeds respiration in rate. "
    "At night only respiration continues because there is no sunlight. "
    "Farmers value both processes when planning crop growth cycles."
)


@pytest.fixture(scope="module")
def client() -> TestClient:
    with TestClient(app) as c:
        yield c


def _register(client: TestClient, prefix: str) -> dict[str, str]:
    email = f"{prefix}_{uuid.uuid4().hex[:8]}@test.com"
    r = client.post(
        "/api/auth/register",
        json={"email": email, "password": "password123", "display_name": prefix.upper()},
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


@pytest.fixture(scope="module")
def auth(client: TestClient) -> dict[str, str]:
    return _register(client, "mt")


@pytest.fixture(scope="module")
def other_auth(client: TestClient) -> dict[str, str]:
    return _register(client, "mo")


@pytest.fixture(scope="module")
def txt_doc_id(client: TestClient, auth: dict[str, str]) -> str:
    files = {"file": ("notes.txt", io.BytesIO(b"hello media original"), "text/plain")}
    r = client.post("/api/documents", headers=auth, files=files)
    assert r.status_code == 200, r.text
    return r.json()["id"]


def _mint(client: TestClient, headers: dict[str, str], payload: dict):
    return client.post("/api/media/token", headers=headers, json=payload)


def _split(token: str) -> tuple[str, str]:
    payload_b64, _, signature = token.partition(".")
    return payload_b64, signature


def test_media_token_happy_path_document_file(client, auth, txt_doc_id):
    r = _mint(client, auth, {"kind": "document_file", "id": txt_doc_id})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["expires_in"] == 60
    assert body["url"].startswith("/api/media/")
    assert body["token"]
    got = client.get(body["url"])
    assert got.status_code == 200
    assert b"hello media original" in got.content
    assert "text/plain" in got.headers["content-type"]


def test_media_token_roundtrip_helpers():
    token = media_api.make_media_token("document_file", "doc1", "user1", ttl_seconds=60)
    kind, ref = media_api.verify_media_token(token)
    assert (kind, ref) == ("document_file", "doc1")
    assert media_api.verify_media_token("no-dot-at-all") is None
    assert media_api.verify_media_token(".deadbeef") is None


def _tampered_payload_token(token: str, mutate) -> str:
    payload_b64, signature = _split(token)
    payload = json.loads(media_api._b64url_decode(payload_b64))
    payload = mutate(payload)
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return f"{media_api._b64url_encode(raw)}.{signature}"


def test_tampered_payload_is_404(client, auth, txt_doc_id):
    cap = _mint(client, auth, {"kind": "document_file", "id": txt_doc_id}).json()

    def swap_kind(payload):
        payload["kind"] = "question_audio"
        return payload

    bad = _tampered_payload_token(cap["token"], swap_kind)
    resp = client.get(f"/api/media/{bad}")
    assert resp.status_code == 404


def test_tampered_signature_is_404(client, auth, txt_doc_id):
    cap = _mint(client, auth, {"kind": "document_file", "id": txt_doc_id}).json()
    payload_b64, signature = _split(cap["token"])
    replacement = "A" if signature[-1] != "A" else "B"
    bad = f"{payload_b64}.{signature[:-1]}{replacement}"
    resp = client.get(f"/api/media/{bad}")
    assert resp.status_code == 404
    assert "expired or is invalid" in resp.json()["detail"]


def test_expired_media_token_is_404(client):
    token = media_api.make_media_token("document_file", "doc1", "user1", ttl_seconds=-1)
    resp = client.get(f"/api/media/{token}")
    assert resp.status_code == 404
    assert media_api.verify_media_token(token) is None


def test_invalid_media_token_is_404(client):
    resp = client.get("/api/media/definitely-not-a-real-token")
    assert resp.status_code == 404
    assert "detail" in resp.json()


def test_wrong_user_cannot_mint_document_token(client, other_auth, txt_doc_id):
    r = _mint(client, other_auth, {"kind": "document_file", "id": txt_doc_id})
    assert r.status_code == 404


def test_unknown_kind_is_rejected(client, auth, txt_doc_id):
    r = _mint(client, auth, {"kind": "hologram", "id": txt_doc_id})
    assert r.status_code == 400
    assert "Unsupported media kind" in r.json()["detail"]


def test_mint_requires_bearer_auth(client, txt_doc_id):
    r = client.post("/api/media/token", json={"kind": "document_file", "id": txt_doc_id})
    assert r.status_code == 401


@pytest.fixture(scope="module")
def viva_session_id(client: TestClient, auth: dict[str, str], txt_doc_id: str) -> str:
    files = {
        "file": (
            "bio.txt",
            io.BytesIO(LONG_TEXT.encode()),
            "text/plain",
        )
    }
    r = client.post("/api/documents", headers=auth, files=files)
    assert r.status_code == 200, r.text
    bio_id = r.json()["id"]
    start = client.post(f"/api/documents/{bio_id}/viva/start", headers=auth)
    assert start.status_code == 200, start.text
    return start.json()["session_id"]


def _fake_tts(monkeypatch) -> None:
    def fake_synthesize(text: str, out_path, max_words: int = 80):
        out_path.write_bytes(b"ID3" + bytes(96))
        return out_path

    monkeypatch.setattr("app.services.tts.synthesize_speech_bounded", fake_synthesize)


def test_question_audio_via_media_token(client, auth, viva_session_id, monkeypatch):
    _fake_tts(monkeypatch)
    r = _mint(client, auth, {"kind": "question_audio", "id": viva_session_id})
    assert r.status_code == 200, r.text
    cap = r.json()
    got = client.get(cap["url"])
    assert got.status_code == 200
    assert got.headers["content-type"].startswith("audio/mpeg")


def test_wrong_user_cannot_mint_viva_audio_token(client, other_auth, viva_session_id):
    r = _mint(client, other_auth, {"kind": "question_audio", "id": viva_session_id})
    assert r.status_code == 404


def test_no_jwt_accepted_via_query_on_document_file(client, auth, txt_doc_id):
    jwt = auth["Authorization"].split(" ", 1)[1]
    resp = client.get(f"/api/documents/{txt_doc_id}/file?token={jwt}")
    assert resp.status_code == 401


def test_no_jwt_accepted_via_query_on_question_audio(client, auth, viva_session_id, monkeypatch):
    _fake_tts(monkeypatch)
    jwt = auth["Authorization"].split(" ", 1)[1]
    resp = client.get(f"/api/viva/{viva_session_id}/question-audio?token={jwt}")
    assert resp.status_code == 401
