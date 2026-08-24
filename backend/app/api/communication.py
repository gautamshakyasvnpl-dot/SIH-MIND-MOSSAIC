from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db import get_db
from app.models import User
from app.schemas import CommunicationIn, CommunicationOut, PlanIn, PlanOut
from app.services import communication as comm
from app.services.reader import prioritize

router = APIRouter(tags=["communication"])


@router.post("/communication", response_model=CommunicationOut)
def communicate(
    body: CommunicationIn, user: User = Depends(get_current_user)
) -> CommunicationOut:
    mode = body.mode.strip().lower()
    if mode == "email":
        return CommunicationOut(
            mode="email",
            engine="template",
            result=comm.draft_email(body.raw, body.recipient, body.deadline),
        )
    if mode == "structure":
        return CommunicationOut(
            mode="structure", engine="template", result=comm.structure_message(body.raw)
        )
    if mode == "presentation":
        return CommunicationOut(
            mode="presentation",
            engine="template",
            result=comm.presentation_outline(body.topic, body.raw),
        )
    from fastapi import HTTPException

    raise HTTPException(status_code=400, detail="mode must be email, structure or presentation")


@router.post("/wellbeing/plan", response_model=PlanOut)
def study_plan(
    body: PlanIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> PlanOut:
    del db
    parts = prioritize(body.items[:12])
    return PlanOut(**parts)
