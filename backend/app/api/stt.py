import os

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.consent import require_consent
from app.core.security import get_current_user
from app.db import get_db
from app.models import User
from app.schemas import SttOut

router = APIRouter(prefix="/stt", tags=["stt"])

MAX_BYTES = 15 * 1024 * 1024
ALLOWED = {".webm", ".wav", ".mp3"}


def _transcribe_gemini(data: bytes, mime: str) -> str | None:
    if not os.environ.get("GEMINI_API_KEY"):
        return None
    try:
        from google import genai

        client = genai.Client()
        response = client.models.generate_content(
            model=os.environ.get("GEMINI_MODEL", "gemini-2.0-flash"),
            contents=[
                {"inline_data": {"mime_type": mime or "audio/webm", "data": data}},
                "Transcribe this speech exactly. Output only the transcription.",
            ],
        )
        return (response.text or "").strip() or None
    except Exception:
        return None


@router.post("", response_model=SttOut)
def transcribe(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SttOut:
    require_consent(user, "voice", db)
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED:
        raise HTTPException(
            status_code=400,
            detail="Unsupported audio format. Please upload .webm, .wav or .mp3 up to 15 MB.",
        )
    data = file.file.read(MAX_BYTES + 1)
    if not data:
        raise HTTPException(status_code=400, detail="Empty upload")
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=400, detail="Audio exceeds 15 MB")
    text = _transcribe_gemini(data, file.content_type or "")
    if text is None:
        return SttOut(text="", engine="")
    return SttOut(text=text, engine="gemini")
