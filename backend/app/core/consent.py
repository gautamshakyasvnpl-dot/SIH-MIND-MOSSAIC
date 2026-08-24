from typing import Literal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import Consent, User

ConsentKind = Literal["voice", "telemetry", "memory"]

CONSENT_DETAILS: dict[str, str] = {
    "voice": "Voice features are turned off in your consent settings. Enable voice consent in Preferences to use this.",
    "telemetry": "Learning analytics are turned off in your consent settings. Enable telemetry consent in Preferences to use this.",
    "memory": "Learning memory is turned off in your consent settings. Enable memory consent in Preferences to use this.",
}


def load_or_create_consent(db: Session, user_id: str) -> Consent:
    row = db.get(Consent, user_id)
    if row is None:
        row = Consent(user_id=user_id)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def require_consent(current_user: User, kind: ConsentKind, db: Session) -> Consent:
    if kind not in CONSENT_DETAILS:
        raise ValueError(f"Unknown consent kind: {kind}")
    row = load_or_create_consent(db, current_user.id)
    if not getattr(row, kind):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=CONSENT_DETAILS[kind],
        )
    return row
