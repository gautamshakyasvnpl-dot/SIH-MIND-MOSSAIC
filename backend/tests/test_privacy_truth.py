import io
import uuid
from pathlib import Path

import gtts
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings  # noqa: E402
from app.db import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402
from app.models import (  # noqa: E402
    Checkin,
    Consent,
    Document,
    DocumentChunk,
    InteractionEvent,
    LearnerProfile,
    PreferenceScore,
    Sprint,
    Task,
    User,
    VivaSession,
    VivaTurn,
)


def _fake_save(self: gtts.gTTS, saveaddr: object) -> None:
    Path(str(saveaddr)).write_bytes(b"ID3MOCK")


RICH_TEXT = (
    "Photosynthesis converts light energy into chemical energy. "
    "Plants absorb sunlight through chlorophyll in their leaves. "
    "The process produces glucose and releases oxygen into the air. "
    "Cellular respiration releases energy from glucose in living cells."
)

EXPORT_KEYS = {
    "exported_at",
    "profile",
    "consents",
    "documents",
    "adaptations",
    "tasks",
    "viva_sessions",
    "interaction_events",
    "wellbeing_checkins",
}


@pytest.fixture(scope="module")
def client() -> TestClient:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def token(client: TestClient) -> str:
    email = f"truth_{uuid.uuid4().hex[:8]}@test.com"
    r = client.post(
        "/api/auth/register",
        json={"email": email, "password": "password123", "display_name": "Truth"},
    )
    assert r.status_code == 200, r.text
    return r.json()["token"]


@pytest.fixture(scope="module")
def auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_face_routes_absent_text_emotion_present(client: TestClient, auth: dict[str, str]) -> None:
    r = client.post(
        "/api/emotion/face",
        headers=auth,
        files={"file": ("face.png", io.BytesIO(b"\x89PNG fake"), "image/png")},
    )
    assert r.status_code == 404

    r = client.get("/openapi.json")
    assert r.status_code == 200
    assert not any("/api/emotion" in p for p in r.json()["paths"])

    r = client.post("/api/checkins", headers=auth, json={"mood": 3, "note": "feeling okay today"})
    assert r.status_code == 200, r.text


def test_export_contains_every_owned_category(
    client: TestClient,
    auth: dict[str, str],
    token: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(gtts.gTTS, "save", _fake_save)
    monkeypatch.setattr(settings, "UPLOAD_DIR", tmp_path)

    assert client.post("/api/consents", headers=auth, json={"voice": True, "telemetry": True, "memory": True}).status_code == 200

    r = client.put("/api/profile", headers=auth, json={"pace": "gentle"})
    assert r.status_code == 200, r.text

    files = {"file": ("truth.txt", io.BytesIO(RICH_TEXT.encode()), "text/plain")}
    doc_id = client.post("/api/documents", headers=auth, files=files).json()["id"]

    adapt = client.post(f"/api/documents/{doc_id}/adapt", headers=auth, json={"formats": ["simplified_text", "tts_audio"]})
    assert adapt.status_code == 200, adapt.text
    tts_items = [i for i in adapt.json()["results"] if i["format"] == "tts_audio"]
    assert tts_items and tts_items[0]["status"] == "ok"

    task = client.post("/api/tasks", headers=auth, json={"title": "Essay draft", "due_date": None, "notes": "intro body conclusion"})
    assert task.status_code == 200, task.text
    assert len(task.json()["sprints"]) >= 1

    viva = client.post(f"/api/documents/{doc_id}/viva/start", headers=auth)
    assert viva.status_code == 200, viva.text

    assert client.post("/api/checkins", headers=auth, json={"mood": 2, "note": "rough day"}).status_code == 200
    assert client.post("/api/interactions", headers=auth, json={"event": "requested_example"}).status_code == 200

    r = client.get("/api/me/export", headers=auth)
    assert r.status_code == 200, r.text
    body = r.json()
    assert EXPORT_KEYS <= set(body)
    assert body["consents"] == {"voice": True, "telemetry": True, "memory": True}
    assert body["profile"]["learner_profile"].get("pace") == "gentle"
    assert isinstance(body["profile"]["preference_scores"], dict) and body["profile"]["preference_scores"]
    docs = body["documents"]
    assert len(docs) == 1 and RICH_TEXT.startswith(docs[0]["text_content"][:40])
    adaptations = body["adaptations"]
    assert len(adaptations) == 1
    formats = {i["format"] for i in adaptations[0]["results"]}
    assert {"simplified_text", "tts_audio"} <= formats
    tasks = body["tasks"]
    assert len(tasks) == 1 and len(tasks[0]["sprints"]) >= 1
    vivas = body["viva_sessions"]
    assert len(vivas) == 1 and len(vivas[0]["turns"]) == 5
    assert any(c["note"] == "rough day" for c in body["wellbeing_checkins"])
    assert len(body["interaction_events"]) == 1


def test_export_bearer_only_and_query_token_rejected(client: TestClient, auth: dict[str, str], token: str) -> None:
    r = client.get("/api/me/export", headers=auth)
    assert r.status_code == 200

    no_auth = client.get("/api/me/export")
    assert no_auth.status_code == 401

    query_form = client.get(f"/api/me/export?token={token}")
    assert query_form.status_code == 401


def test_delete_me_full_cascade(
    client: TestClient,
    auth: dict[str, str],
    token: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(gtts.gTTS, "save", _fake_save)
    monkeypatch.setattr(settings, "UPLOAD_DIR", tmp_path)

    user_id = None
    with SessionLocal() as db:
        user = db.query(User).filter(User.email.endswith("@test.com")).all()
        assert user
        target = next(u for u in user if u.display_name == "Truth")
        user_id = target.id

    files = {"file": ("doomed.txt", io.BytesIO(RICH_TEXT.encode()), "text/plain")}
    doc_id = client.post("/api/documents", headers=auth, files=files).json()["id"]
    client.post(f"/api/documents/{doc_id}/ask", headers=auth, json={"question": "What does photosynthesis produce?"})
    viva = client.post(f"/api/documents/{doc_id}/viva/start", headers=auth).json()
    session_id = viva["session_id"]
    adapt = client.post(f"/api/documents/{doc_id}/adapt", headers=auth, json={"formats": ["tts_audio"]}).json()
    tts_item = next(i for i in adapt["results"] if i["format"] == "tts_audio")
    audio_name = str(tts_item["content"]).rsplit("/", 1)[-1]
    task = client.post("/api/tasks", headers=auth, json={"title": "Doomed task", "due_date": None, "notes": None}).json()
    client.post(f"/api/tasks/{task['id']}/sprints/{task['sprints'][0]['id']}/toggle", headers=auth)
    client.post("/api/checkins", headers=auth, json={"mood": 4, "note": None})
    client.post("/api/interactions", headers=auth, json={"event": "quiz_incorrect", "concept": "X"})
    client.post("/api/consents", headers=auth, json={"voice": True})

    stored_doc = settings.docs_dir / f"{doc_id}_doomed.txt"
    stored_adapt_audio = settings.audio_dir / audio_name
    stored_viva_audio = settings.audio_dir / f"viva_{session_id}_0.mp3"
    stored_viva_audio.write_bytes(b"ID3MOCK-VIVA")
    assert stored_doc.is_file()
    assert stored_adapt_audio.is_file()

    r = client.delete("/api/me", headers=auth)
    assert r.status_code == 200, r.text
    assert "detail" in r.json()

    with SessionLocal() as db:
        assert db.query(User).filter(User.id == user_id).count() == 0
        assert db.query(LearnerProfile).filter(LearnerProfile.user_id == user_id).count() == 0
        assert db.query(Consent).filter(Consent.user_id == user_id).count() == 0
        assert db.query(Document).filter(Document.user_id == user_id).count() == 0
        assert db.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).count() == 0
        assert db.query(VivaSession).filter(VivaSession.user_id == user_id).count() == 0
        assert db.query(VivaTurn).filter(VivaTurn.session_id == session_id).count() == 0
        assert db.query(Task).filter(Task.user_id == user_id).count() == 0
        assert db.query(Sprint).filter(Sprint.task_id == task["id"]).count() == 0
        assert db.query(Checkin).filter(Checkin.user_id == user_id).count() == 0
        assert db.query(InteractionEvent).filter(InteractionEvent.user_id == user_id).count() == 0
        assert db.query(PreferenceScore).filter(PreferenceScore.user_id == user_id).count() == 0

    assert not stored_doc.exists()
    assert not stored_adapt_audio.exists()
    assert not stored_viva_audio.exists()

    assert client.get("/api/auth/me", headers=auth).status_code == 401
