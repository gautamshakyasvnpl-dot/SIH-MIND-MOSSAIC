import base64
import hashlib
import hmac
import json
import secrets
import time

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.documents import _document_file_response, _get_owned_document
from app.api.viva import question_audio_response
from app.core.config import settings
from app.core.security import get_current_user
from app.db import get_db
from app.models import Document, User, VivaSession
from app.schemas import MediaTokenIn, MediaTokenOut

router = APIRouter(prefix="/media", tags=["media"])

MEDIA_TOKEN_TTL_SECONDS = 60
_MEDIA_TOKEN_VERSION = 1


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _signature(payload_b64: str) -> str:
    mac = hmac.new(
        settings.JWT_SECRET.encode("utf-8"),
        payload_b64.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return _b64url_encode(mac)


def make_media_token(
    kind: str, ref: str, user_id: str, ttl_seconds: int = MEDIA_TOKEN_TTL_SECONDS
) -> str:
    payload = {
        "v": _MEDIA_TOKEN_VERSION,
        "kind": kind,
        "ref": ref,
        "uid": user_id,
        "exp": int(time.time()) + ttl_seconds,
        "nonce": secrets.token_urlsafe(8),
    }
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    return f"{payload_b64}.{_signature(payload_b64)}"


def verify_media_token(token: str) -> tuple[str, str] | None:
    payload_b64, sep, signature = token.partition(".")
    if not sep or not payload_b64 or not signature:
        return None
    try:
        payload_b64.encode("ascii")
        signature.encode("ascii")
    except UnicodeEncodeError:
        return None
    if len(signature) != 43 or not hmac.compare_digest(_signature(payload_b64), signature):
        return None
    try:
        payload = json.loads(_b64url_decode(payload_b64))
    except ValueError:
        return None
    if not isinstance(payload, dict) or payload.get("v") != _MEDIA_TOKEN_VERSION:
        return None
    if not isinstance(payload.get("exp"), int) or payload["exp"] <= time.time():
        return None
    kind = payload.get("kind")
    ref = payload.get("ref")
    if not isinstance(kind, str) or not isinstance(ref, str):
        return None
    return kind, ref


@router.post("/token", response_model=MediaTokenOut)
def issue_media_token(
    body: MediaTokenIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MediaTokenOut:
    if body.kind == "document_file":
        ref = _get_owned_document(db, body.id, user).id
    elif body.kind == "question_audio":
        session = db.get(VivaSession, body.id)
        if session is None or session.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        ref = session.id
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported media kind")

    token = make_media_token(body.kind, ref, user.id)
    return MediaTokenOut(token=token, expires_in=MEDIA_TOKEN_TTL_SECONDS, url=f"/api/media/{token}")


@router.get("/{token}")
def consume_media_token(token: str, db: Session = Depends(get_db)) -> FileResponse:
    verified = verify_media_token(token)
    if verified is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This media link has expired or is invalid.",
        )
    kind, ref = verified
    if kind == "document_file":
        doc = db.get(Document, ref)
        if doc is None or not doc.filename:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="This media link is no longer valid.")
        return _document_file_response(doc)

    session = db.get(VivaSession, ref)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="This media link is no longer valid.")
    return question_audio_response(db, session)
