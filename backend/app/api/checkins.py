import uuid
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db import get_db
from app.models import Checkin, User
from app.schemas import CheckinIn, CheckinListOut, CheckinOut
from app.services.emotion import detect_emotion
from app.services.wellbeing import suggest_for_mood

router = APIRouter(prefix="/checkins", tags=["checkins"])


def _build_checkin_out(
    checkin_id: str, mood: int, note: str | None, created_at: datetime
) -> CheckinOut:
    detected = detect_emotion(note) if note else None
    label = detected["label"] if detected else None
    return CheckinOut(
        id=checkin_id,
        mood=mood,
        note=note,
        suggestion=suggest_for_mood(mood, label),
        created_at=created_at,
    )


@router.post("", response_model=CheckinOut)
def create_checkin(
    body: CheckinIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CheckinOut:
    checkin = Checkin(
        id=uuid.uuid4().hex,
        user_id=user.id,
        mood=body.mood,
        note=body.note,
    )
    db.add(checkin)
    db.commit()
    db.refresh(checkin)
    return _build_checkin_out(checkin.id, checkin.mood, checkin.note, checkin.created_at)


@router.get("", response_model=CheckinListOut)
def list_checkins(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> CheckinListOut:
    rows = (
        db.query(Checkin)
        .filter(Checkin.user_id == user.id)
        .order_by(Checkin.created_at.desc())
        .limit(50)
        .all()
    )
    return CheckinListOut(
        items=[
            _build_checkin_out(r.id, r.mood, r.note, r.created_at) for r in rows
        ]
    )
