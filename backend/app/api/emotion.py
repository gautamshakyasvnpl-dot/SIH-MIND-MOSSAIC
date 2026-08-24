import os

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db import get_db
from app.models import User
from app.schemas import EmotionOut, FaceMoodOut
from app.services.vision import detect_face_mood

router = APIRouter(prefix="/emotion", tags=["emotion"])

MAX_BYTES = 5 * 1024 * 1024
ALLOWED = {".jpg", ".jpeg", ".png", ".webp"}


@router.post("/face", response_model=FaceMoodOut)
def face_mood(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FaceMoodOut:
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext and ext not in ALLOWED:
        raise HTTPException(status_code=400, detail="Unsupported image format")
    data = file.file.read(MAX_BYTES + 1)
    if not data:
        raise HTTPException(status_code=400, detail="Empty upload")
    if len(data) > MAX_BYTES:
        raise HTTPException(status_code=400, detail="Image exceeds 5 MB")
    detected = detect_face_mood(data)
    if detected is None:
        return FaceMoodOut(emotion=None, engine="")
    if not detected.get("label"):
        return FaceMoodOut(
            emotion=None,
            engine="fer2013_gnb",
            detail="Not confident enough - try again with more light on your face.",
        )
    return FaceMoodOut(
        emotion=EmotionOut(label=detected["label"], score=float(detected["score"])),
        engine="fer2013_gnb",
        runner_up=detected.get("runner_up") or None,
    )
