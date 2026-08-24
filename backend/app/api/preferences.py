import uuid
from datetime import datetime as dt, timezone as tz

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.consent import require_consent
from app.core.security import get_current_user
from app.db import get_db
from app.models import InteractionEvent, PreferenceScore, User
from app.schemas import (
    InteractionIn,
    InteractionOut,
    PreferencesOut,
    PreferencesUpdate,
)
from app.services import preferences as prefs

router = APIRouter(tags=["preferences"])


def _load_scores(db: Session, user: User) -> dict[str, float]:
    row = db.get(PreferenceScore, user.id)
    if row is None:
        return dict(prefs.DEFAULT_SCORES)
    return {**prefs.DEFAULT_SCORES, **(row.scores or {})}


def _save_scores(db: Session, user_id: str, scores: dict[str, float]) -> None:
    row = db.get(PreferenceScore, user_id)
    if row is None:
        db.add(PreferenceScore(user_id=user_id, scores=scores))
    else:
        row.scores = scores
        row.updated_at = dt.now(tz.utc).replace(tzinfo=None)
    db.commit()


@router.get("/preferences", response_model=PreferencesOut)
def get_preferences(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> PreferencesOut:
    if not db.get(PreferenceScore, user.id):
        _save_scores(db, user.id, prefs.bootstrap_from_profile({}))
    scores = _load_scores(db, user)
    recent = (
        db.query(InteractionEvent)
        .filter(InteractionEvent.user_id == user.id)
        .order_by(InteractionEvent.created_at.desc())
        .limit(12)
        .all()
    )
    return PreferencesOut(
        scores=scores,
        labels=prefs.LABELS,
        profile_lines=prefs.describe_profile(scores),
        recent_events=[
            InteractionOut(
                id=r.id,
                event=r.event,
                concept=r.concept,
                document_id=r.document_id,
                created_at=r.created_at,
            )
            for r in recent
        ],
    )


@router.put("/preferences", response_model=PreferencesOut)
def update_preferences(
    body: PreferencesUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PreferencesOut:
    current = _load_scores(db, user)
    for key, value in (body.scores or {}).items():
        if key in prefs.DEFAULT_SCORES and isinstance(value, (int, float)):
            current[key] = round(min(1.0, max(0.0, float(value))), 4)
    _save_scores(db, user.id, current)
    return get_preferences(user=user, db=db)


@router.post("/interactions", response_model=PreferencesOut)
def log_interaction(
    body: InteractionIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PreferencesOut:
    require_consent(user, "telemetry", db)
    if len(body.event) > 48 or not body.event.strip():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="Invalid event name")
    scores = _load_scores(db, user)
    updated, changes = prefs.apply_signal(scores, body.event, body.metadata)
    event = InteractionEvent(
        id=uuid.uuid4().hex,
        user_id=user.id,
        document_id=body.document_id,
        event=body.event.strip(),
        concept=body.concept,
        meta=body.metadata or {},
    )
    db.add(event)
    _save_scores(db, user.id, updated)
    out = get_preferences(user=user, db=db)
    if changes:
        out.profile_lines = [c["explanation"] for c in changes]
    return out


@router.get("/interactions/recent", response_model=list[InteractionOut])
def recent_interactions(
    limit: int = Query(default=12, ge=1, le=50),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[InteractionOut]:
    rows = (
        db.query(InteractionEvent)
        .filter(InteractionEvent.user_id == user.id)
        .order_by(InteractionEvent.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        InteractionOut(
            id=r.id,
            event=r.event,
            concept=r.concept,
            document_id=r.document_id,
            created_at=r.created_at,
        )
        for r in rows
    ]
