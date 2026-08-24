from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.consent import load_or_create_consent
from app.core.security import get_current_user
from app.db import get_db
from app.models import Consent, User
from app.schemas import ConsentsIn, ConsentsOut

router = APIRouter(prefix="/consents", tags=["consents"])


@router.get("", response_model=ConsentsOut)
def get_consents(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ConsentsOut:
    row = load_or_create_consent(db, user.id)
    return ConsentsOut(voice=row.voice, telemetry=row.telemetry, memory=row.memory)


@router.post("", response_model=ConsentsOut)
def post_consents(body: ConsentsIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ConsentsOut:
    row = db.get(Consent, user.id)
    if row is None:
        row = Consent(user_id=user.id)
        db.add(row)
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return ConsentsOut(voice=row.voice, telemetry=row.telemetry, memory=row.memory)
