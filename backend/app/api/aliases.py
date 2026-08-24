"""Literal-path aliases matching the master prompt's API design (§16).

Each alias delegates to the canonical route function or service so there
is exactly one implementation of the logic.
"""

import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.api.preferences import log_interaction
from app.api.reader import explain as explain_route
from app.core.security import get_current_user
from app.db import get_db
from app.models import LearnerProfile, User
from app.schemas import (
    CommunicationIn,
    CommunicationOut,
    ExplainIn,
    ExplainOut,
    InteractionIn,
    PreferencesOut,
    ProfilePut,
    QuizOut,
    QuizRequest,
)

router = APIRouter(tags=["aliases"])


@router.post("/adaptive/explain", response_model=ExplainOut)
def adaptive_explain(
    body: ExplainIn, user: User = Depends(get_current_user)
) -> ExplainOut:
    return explain_route(body, user)


@router.post("/adaptive/simplify", response_model=ExplainOut)
def adaptive_simplify(
    body: ExplainIn, user: User = Depends(get_current_user)
) -> ExplainOut:
    return explain_route(body.model_copy(update={"level": 2}), user)


@router.post("/adaptive/analogy", response_model=ExplainOut)
def adaptive_analogy(
    body: ExplainIn, user: User = Depends(get_current_user)
) -> ExplainOut:
    return explain_route(body.model_copy(update={"transform": "analogy"}), user)


@router.post("/feedback", response_model=PreferencesOut)
def feedback_alias(
    body: InteractionIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PreferencesOut:
    return log_interaction(body=body, user=user, db=db)


@router.get("/learner/profile")
def get_learner_profile_alias(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    row = db.get(LearnerProfile, user.id)
    return row.data if row else {}


@router.patch("/learner/profile")
def patch_learner_profile_alias(
    patch: dict,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    unknown = sorted(set(patch) - set(ProfilePut.model_fields))
    if unknown:
        raise HTTPException(
            status_code=422, detail=f"Unknown profile field(s): {', '.join(unknown)}"
        )
    try:
        validated = ProfilePut.model_validate(patch)
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail="Invalid profile patch values") from exc
    row = db.get(LearnerProfile, user.id)
    data = dict(row.data) if row else {}
    data.update(validated.model_dump(exclude_unset=True))
    if row is None:
        db.add(LearnerProfile(user_id=user.id, data=data))
    else:
        row.data = data
    db.commit()
    return data


@router.post("/voice/synthesize")
def voice_synthesize(
    body: dict,
    user: User = Depends(get_current_user),
) -> dict:
    del user
    text = str(body.get("text", "")).strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    from app.core.config import settings
    from app.services.tts import synthesize_speech_bounded

    out_dir = settings.audio_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.mp3"
    try:
        synthesize_speech_bounded(text[:4000], out_dir / filename)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=f"TTS failed: {exc}") from exc
    return {"audio_url": f"/api/audio/{filename}", "engine": "gtts"}


__all__ = ["router", "CommunicationIn", "CommunicationOut", "QuizOut", "QuizRequest"]
