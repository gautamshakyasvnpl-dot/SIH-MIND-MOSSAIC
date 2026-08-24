import io
import uuid
from pathlib import Path

import gtts
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings  # noqa: E402
from app.db import SessionLocal  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Adaptation, Document, DocumentChunk, VivaSession, VivaTurn  # noqa: E402


@pytest.fixture(scope="module")
def client() -> TestClient:
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def auth(client: TestClient) -> dict[str, str]:
    email = f"stor_{uuid.uuid4().hex[:8]}@test.com"
    r = client.post(
        "/api/auth/register",
        json={"email": email, "password": "password123", "display_name": "ST"},
    )
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


def _fake_save(self: gtts.gTTS, saveaddr: object) -> None:
    Path(str(saveaddr)).write_bytes(b"ID3MOCK")


CORRUPT_CASES = [
    ("broken.pptx", b"this is definitely not a zip archive"),
    ("broken.pdf", b"%PDF-1.4 this is not really a pdf body"),
    ("broken.docx", b"this is definitely not a zip archive"),
]


@pytest.mark.parametrize("filename,payload", CORRUPT_CASES)
def test_corrupt_office_pdf_uploads_return_400(
    client: TestClient,
    auth: dict[str, str],
    filename: str,
    payload: bytes,
) -> None:
    before = {p.name for p in settings.docs_dir.glob("*")} if settings.docs_dir.exists() else set()
    r = client.post(
        "/api/documents",
        headers=auth,
        files={"file": (filename, io.BytesIO(payload), "application/octet-stream")},
    )
    assert r.status_code == 400, r.text
    detail = r.json()["detail"].lower()
    assert "could not read this file" in detail
    for ext in (".pptx", ".pdf", ".docx", ".txt"):
        assert ext in detail
    after = {p.name for p in settings.docs_dir.glob("*")} if settings.docs_dir.exists() else set()
    assert before == after


def test_empty_txt_still_lenient_decoded_then_rejected(
    client: TestClient, auth: dict[str, str]
) -> None:
    r = client.post(
        "/api/documents",
        headers=auth,
        files={"file": ("tiny.txt", io.BytesIO(b"hi"), "text/plain")},
    )
    assert r.status_code == 400, r.text


def test_upload_dir_override_audio_roundtrip(
    client: TestClient,
    auth: dict[str, str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(gtts.gTTS, "save", _fake_save)
    monkeypatch.setattr(settings, "UPLOAD_DIR", tmp_path)

    text = ("Photosynthesis captures sunlight for plants. " * 20).strip()
    r = client.post(
        "/api/documents",
        headers=auth,
        files={"file": ("roundtrip.txt", io.BytesIO(text.encode()), "text/plain")},
    )
    assert r.status_code == 200, r.text
    doc_id = r.json()["id"]

    r = client.post(
        f"/api/documents/{doc_id}/adapt",
        headers=auth,
        json={"formats": ["simplified_text", "tts_audio"]},
    )
    assert r.status_code == 200, r.text
    results = r.json()["results"]
    tts = next(i for i in results if i["format"] == "tts_audio")
    assert tts["status"] == "ok"
    url = str(tts["content"])
    assert url.startswith("/api/audio/")
    filename = url.rsplit("/", 1)[-1]

    audio_file = tmp_path / "audio" / filename
    assert audio_file.is_file(), f"expected audio under overridden UPLOAD_DIR: {audio_file}"
    assert audio_file.read_bytes().startswith(b"ID3")

    served = client.get(url)
    assert served.status_code == 200, served.text
    assert served.content.startswith(b"ID3")


def test_delete_document_cascades_rows_and_files(
    client: TestClient,
    auth: dict[str, str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(gtts.gTTS, "save", _fake_save)
    monkeypatch.setattr(settings, "UPLOAD_DIR", tmp_path)

    text = (
        "Photosynthesis converts light energy into chemical energy. "
        "Plants absorb sunlight through chlorophyll in their leaves. "
        "The process produces glucose and releases oxygen into the air."
    )
    r = client.post(
        "/api/documents",
        headers=auth,
        files={"file": ("cascade.txt", io.BytesIO(text.encode()), "text/plain")},
    )
    assert r.status_code == 200, r.text
    doc_id = r.json()["id"]

    r = client.post(
        f"/api/documents/{doc_id}/ask",
        headers=auth,
        json={"question": "What does photosynthesis produce?"},
    )
    assert r.status_code == 200, r.text
    assert len(r.json()["sources"]) >= 1

    r = client.post(f"/api/documents/{doc_id}/viva/start", headers=auth)
    assert r.status_code == 200, r.text
    session_id = r.json()["session_id"]

    r = client.post(
        f"/api/documents/{doc_id}/adapt",
        headers=auth,
        json={"formats": ["tts_audio"]},
    )
    assert r.status_code == 200, r.text
    tts = next(i for i in r.json()["results"] if i["format"] == "tts_audio")
    assert tts["status"] == "ok"
    audio_name = str(tts["content"]).rsplit("/", 1)[-1]

    stored_doc = tmp_path / "docs" / f"{doc_id}_cascade.txt"
    stored_audio = tmp_path / "audio" / audio_name
    assert stored_doc.is_file()
    assert stored_audio.is_file()

    with SessionLocal() as db:
        pre_chunks = db.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).count()
        pre_adaptations = db.query(Adaptation).filter(Adaptation.document_id == doc_id).count()
        pre_sessions = db.query(VivaSession).filter(VivaSession.document_id == doc_id).count()
        pre_turns = db.query(VivaTurn).filter(VivaTurn.session_id == session_id).count()
        assert db.query(Document).filter(Document.id == doc_id).count() == 1
    assert pre_chunks >= 1
    assert pre_adaptations >= 1
    assert pre_sessions == 1
    assert pre_turns >= 1

    r = client.delete(f"/api/documents/{doc_id}", headers=auth)
    assert r.status_code == 204, r.text

    with SessionLocal() as db:
        assert db.query(Document).filter(Document.id == doc_id).count() == 0
        assert db.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).count() == 0
        assert db.query(Adaptation).filter(Adaptation.document_id == doc_id).count() == 0
        assert db.query(VivaSession).filter(VivaSession.document_id == doc_id).count() == 0
        assert db.query(VivaTurn).filter(VivaTurn.session_id == session_id).count() == 0
    assert not stored_doc.exists()
    assert not stored_audio.exists()

    r = client.get(f"/api/documents/{doc_id}", headers=auth)
    assert r.status_code == 404
    r = client.get(f"/api/documents/{doc_id}/adaptations", headers=auth)
    assert r.status_code == 404


def test_bounded_tts_fast_success_no_false_timeout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.services.tts import synthesize_speech_bounded

    monkeypatch.setattr(gtts.gTTS, "save", _fake_save)
    out_path = tmp_path / "fast.mp3"
    result = synthesize_speech_bounded("hello bounded world", out_path, timeout_s=10.0)
    assert result == out_path
    assert out_path.read_bytes().startswith(b"ID3")
    assert not out_path.with_suffix(".tmp.mp3").exists()


def test_bounded_tts_raises_on_injected_hang(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import time

    from app.services.tts import synthesize_speech_bounded

    def hanging_save(self: gtts.gTTS, saveaddr: object) -> None:
        time.sleep(1.5)

    monkeypatch.setattr(gtts.gTTS, "save", hanging_save)
    started = time.monotonic()
    with pytest.raises(RuntimeError, match="too long"):
        synthesize_speech_bounded("hang please", tmp_path / "hang.mp3", timeout_s=0.2)
    elapsed = time.monotonic() - started
    assert elapsed < 1.0


def test_bounded_tts_raises_on_synthesis_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.services.tts import synthesize_speech_bounded

    def failing_save(self: gtts.gTTS, saveaddr: object) -> None:
        raise OSError("disk quota exceeded")

    monkeypatch.setattr(gtts.gTTS, "save", failing_save)
    with pytest.raises(RuntimeError, match="disk quota exceeded"):
        synthesize_speech_bounded("boom", tmp_path / "fail.mp3", timeout_s=5.0)
    assert not (tmp_path / "fail.tmp.mp3").exists()


def test_tts_error_keeps_http_200_with_error_entry(
    client: TestClient,
    auth: dict[str, str],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_mkdir = Path.mkdir

    def patched_mkdir(self: Path, mode: int = 0o777, parents: bool = False, exist_ok: bool = False) -> None:
        if self.name == "audio":
            raise PermissionError("audio dir unwritable")
        real_mkdir(self, mode=mode, parents=parents, exist_ok=exist_ok)

    monkeypatch.setattr(Path, "mkdir", patched_mkdir)
    monkeypatch.setattr(settings, "UPLOAD_DIR", tmp_path)

    r = client.post(
        "/api/documents",
        headers=auth,
        files={"file": ("fsfail.txt", io.BytesIO(("Readable sentence for fs failure." * 3).encode()), "text/plain")},
    )
    assert r.status_code == 200, r.text
    doc_id = r.json()["id"]

    r = client.post(
        f"/api/documents/{doc_id}/adapt",
        headers=auth,
        json={"formats": ["tts_audio"]},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert isinstance(body["used_llm"], bool)
    tts = next(i for i in body["results"] if i["format"] == "tts_audio")
    assert tts["status"] == "error"
    assert tts["content"] is None
    assert "explanation" in tts and tts["explanation"]
