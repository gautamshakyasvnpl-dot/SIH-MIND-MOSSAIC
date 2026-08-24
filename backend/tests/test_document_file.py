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
    email = f"file_{uuid.uuid4().hex[:8]}@test.com"
    r = client.post(
        "/api/auth/register",
        json={"email": email, "password": "password123", "display_name": "F"},
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


@pytest.fixture(scope="module")
def txt_doc_id(client: TestClient, auth: dict[str, str]) -> str:
    files = {"file": ("notes.txt", io.BytesIO("hello original".encode()), "text/plain")}
    r = client.post("/api/documents", headers=auth, files=files)
    assert r.status_code == 200, r.text
    body = r.json()
    assert set(body) == {"id", "filename", "doc_type", "char_count", "created_at"}
    return body["id"]


def test_file_route_serves_original_inline(client, auth, txt_doc_id):
    r = client.get(f"/api/documents/{txt_doc_id}/file", headers=auth)
    assert r.status_code == 200, r.text
    assert b"hello original" in r.content
    assert "text/plain" in r.headers["content-type"]
    assert r.headers["content-disposition"].startswith("inline")


def test_file_route_rejects_jwt_via_query_param(client, txt_doc_id):
    email = f"qt_{uuid.uuid4().hex[:8]}@test.com"
    r = client.post(
        "/api/auth/register",
        json={"email": email, "password": "password123", "display_name": "Q"},
    )
    tok = r.json()["token"]
    resp = client.get(f"/api/documents/{txt_doc_id}/file?token={tok}")
    assert resp.status_code == 401


def test_file_route_requires_auth(client, txt_doc_id):
    r = client.get(f"/api/documents/{txt_doc_id}/file")
    assert r.status_code == 401


def test_file_route_hides_other_users_docs(client, txt_doc_id):
    email = f"other_{uuid.uuid4().hex[:8]}@test.com"
    r = client.post(
        "/api/auth/register",
        json={"email": email, "password": "password123", "display_name": "O"},
    )
    other_auth = {"Authorization": f"Bearer {r.json()['token']}"}
    r = client.get(f"/api/documents/{txt_doc_id}/file", headers=other_auth)
    assert r.status_code == 404

    assert client.get(f"/api/documents/{txt_doc_id}", headers=other_auth).status_code == 404
    assert client.delete(f"/api/documents/{txt_doc_id}", headers=other_auth).status_code == 404
