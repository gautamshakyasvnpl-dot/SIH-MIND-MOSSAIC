import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile, status
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import _bearer_scheme, get_current_user, verify_token
from app.db import get_db
from app.models import Adaptation, Document, DocumentChunk, LearnerProfile, User, VivaSession, VivaTurn
from app.schemas import (
    DEFAULT_PROFILE,
    AdaptIn,
    AdaptOut,
    DocumentListOut,
    DocumentOut,
    RecommendOut,
)

router = APIRouter(prefix="/documents", tags=["documents"])

ALLOWED_EXTENSIONS = {".pptx", ".pdf", ".docx", ".txt"}
MAX_UPLOAD_BYTES = 20 * 1024 * 1024

MEDIA_TYPES = {
    ".pdf": "application/pdf",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".txt": "text/plain; charset=utf-8",
}


def _docs_dir() -> Path:
    path = settings.docs_dir
    path.mkdir(parents=True, exist_ok=True)
    return path


def _audio_filenames_from_adaptations(rows: list[Adaptation]) -> list[str]:
    names: list[str] = []
    for row in rows:
        results = (row.result or {}).get("results", [])
        if not isinstance(results, list):
            continue
        for item in results:
            if not isinstance(item, dict) or item.get("format") != "tts_audio":
                continue
            content = item.get("content")
            if not isinstance(content, str) or not content.startswith("/api/audio/"):
                continue
            name = Path(content[len("/api/audio/"):]).name
            if name and name not in names:
                names.append(name)
    return names


def _get_owned_document(db: Session, doc_id: str, user: User) -> Document:
    doc = db.get(Document, doc_id)
    if doc is None or doc.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return doc


@router.post("/image", response_model=DocumentOut)
async def upload_image(
    file: UploadFile,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DocumentOut:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".png", ".jpg", ".jpeg", ".webp"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image must be .png/.jpg/.jpeg/.webp")
    data = await file.read()
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image exceeds 10 MB limit")
    if not os.environ.get("GEMINI_API_KEY"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Photo/OCR extraction needs GEMINI_API_KEY configured. Text files work without it.",
        )
    import base64

    from google import genai

    client = genai.Client()
    mime = "image/jpeg" if suffix in {".jpg", ".jpeg"} else f"image{suffix}"
    try:
        response = client.models.generate_content(
            model=os.environ.get("GEMINI_MODEL", "gemini-2.0-flash"),
            contents=[
                {"inline_data": {"mime_type": mime, "data": base64.b64encode(data).decode()}},
                "Extract ALL text from this study material verbatim, preserving reading order. Output only the extracted text.",
            ],
        )
        text = (response.text or "").strip()
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"OCR failed: {exc}") from exc
    if not text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No readable text found in this image")

    doc_id = uuid.uuid4().hex
    safe_name = Path(file.filename or "photo.png").name
    _docs_dir().mkdir(parents=True, exist_ok=True)
    (_docs_dir() / f"{doc_id}_{safe_name}").write_bytes(data)
    doc = Document(
        id=doc_id,
        user_id=user.id,
        filename=safe_name,
        doc_type="image",
        char_count=len(text),
        text_content=text,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return DocumentOut(id=doc.id, filename=doc.filename, doc_type=doc.doc_type, char_count=doc.char_count, created_at=doc.created_at)


@router.post("", response_model=DocumentOut)
async def upload_document(file: UploadFile, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> DocumentOut:
    raw_name = file.filename or ""
    safe_name = Path(raw_name).name or "upload"
    suffix = Path(safe_name).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported file type: {suffix or 'unknown'}")
    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File exceeds 20 MB limit")

    from app.services.extraction import doc_type, extract_text

    try:
        text = extract_text(safe_name, data)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not read this file. Supported types: .pptx, .pdf, .docx, .txt.",
        ) from exc

    doc_id = uuid.uuid4().hex
    dest = _docs_dir() / f"{doc_id}_{safe_name}"
    dest.write_bytes(data)

    doc = Document(
        id=doc_id,
        user_id=user.id,
        filename=safe_name,
        doc_type=doc_type(safe_name),
        char_count=len(text),
        text_content=text,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return DocumentOut(id=doc.id, filename=doc.filename, doc_type=doc.doc_type, char_count=doc.char_count, created_at=doc.created_at)


@router.get("", response_model=DocumentListOut)
def list_documents(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> DocumentListOut:
    docs = db.query(Document).filter(Document.user_id == user.id).order_by(Document.created_at.desc()).all()
    items = [DocumentOut(id=d.id, filename=d.filename, doc_type=d.doc_type, char_count=d.char_count, created_at=d.created_at) for d in docs]
    return DocumentListOut(items=items)


@router.get("/{doc_id}", response_model=DocumentOut)
def get_document(doc_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> DocumentOut:
    doc = _get_owned_document(db, doc_id, user)
    return DocumentOut(id=doc.id, filename=doc.filename, doc_type=doc.doc_type, char_count=doc.char_count, created_at=doc.created_at)


def _document_file_response(doc: Document) -> FileResponse:
    suffix = Path(doc.filename).suffix.lower()
    stored_path = _docs_dir() / f"{doc.id}_{doc.filename}"
    if not stored_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Original file not found on server")
    media_type = MEDIA_TYPES.get(suffix, "application/octet-stream")
    inline_ok = suffix in {".pdf", ".txt"}
    disposition = f'inline; filename="{doc.filename}"' if inline_ok else f'attachment; filename="{doc.filename}"'
    return FileResponse(stored_path, media_type=media_type, headers={"Content-Disposition": disposition})


@router.get("/{doc_id}/file")
def get_document_file(
    doc_id: str,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> Response:
    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    user_id = verify_token(credentials.credentials)
    user = db.get(User, user_id) if user_id else None
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    doc = _get_owned_document(db, doc_id, user)
    return _document_file_response(doc)


@router.delete("/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(doc_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> Response:
    doc = _get_owned_document(db, doc_id, user)
    adaptation_rows = db.query(Adaptation).filter(Adaptation.document_id == doc.id).all()
    audio_names = _audio_filenames_from_adaptations(adaptation_rows)
    session_ids = [
        row[0]
        for row in db.query(VivaSession.id).filter(VivaSession.document_id == doc.id).all()
    ]

    if session_ids:
        db.query(VivaTurn).filter(VivaTurn.session_id.in_(session_ids)).delete(synchronize_session=False)
        db.query(VivaSession).filter(VivaSession.document_id == doc.id).delete(synchronize_session=False)
    db.query(DocumentChunk).filter(DocumentChunk.document_id == doc.id).delete(synchronize_session=False)
    db.query(Adaptation).filter(Adaptation.document_id == doc.id).delete(synchronize_session=False)
    stored_doc_path = settings.docs_dir / f"{doc.id}_{doc.filename}"
    db.delete(doc)
    db.commit()

    try:
        stored_doc_path.unlink(missing_ok=True)
    except OSError:
        pass
    for name in audio_names:
        try:
            (settings.audio_dir / name).unlink(missing_ok=True)
        except OSError:
            pass
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{doc_id}/adapt", response_model=AdaptOut)
def adapt_document(doc_id: str, body: AdaptIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, object]:
    doc = _get_owned_document(db, doc_id, user)
    profile_row = db.get(LearnerProfile, user.id)
    profile_data: dict[str, object] = dict(DEFAULT_PROFILE)
    if profile_row is not None and isinstance(profile_row.data, dict):
        profile_data.update(profile_row.data)

    from app.services.adapter import adapt_document as adapt_document_service

    result = adapt_document_service(doc.text_content, profile_data, formats=body.formats)
    row = Adaptation(document_id=doc.id, result=result)
    db.add(row)
    db.commit()

    return JSONResponse(
        content={
            "document_id": doc.id,
            "used_llm": bool(result.get("used_llm", False)),
            "results": result.get("results", []),
        }
    )


@router.get("/{doc_id}/adaptations", response_model=AdaptOut)
def latest_adaptation(doc_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, object]:
    doc = _get_owned_document(db, doc_id, user)
    row = (
        db.query(Adaptation)
        .filter(Adaptation.document_id == doc.id)
        .order_by(Adaptation.created_at.desc(), Adaptation.id.desc())
        .first()
    )
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No adaptations found for this document")
    return {
        "document_id": doc.id,
        "used_llm": bool(row.result.get("used_llm", False)),
        "results": row.result.get("results", []),
    }


@router.get("/{doc_id}/recommend", response_model=RecommendOut)
def recommend(
    doc_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RecommendOut:
    from app.services.recommender import recommend_format

    doc = _get_owned_document(db, doc_id, user)
    profile_row = db.get(LearnerProfile, user.id)
    profile: dict[str, object] = dict(DEFAULT_PROFILE)
    if profile_row is not None and isinstance(profile_row.data, dict):
        profile.update(profile_row.data)

    usage: dict[str, int] = {}
    for adaptation in (
        db.query(Adaptation)
        .join(Document, Adaptation.document_id == Document.id)
        .filter(Document.user_id == user.id)
        .all()
    ):
        for item in (adaptation.result or {}).get("results", []):
            fmt = str(item.get("format", ""))
            if item.get("status") == "ok" and fmt:
                usage[fmt] = usage.get(fmt, 0) + 1

    return RecommendOut(**recommend_format(doc.text_content or "", profile, usage))
