from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db import get_db
from app.models import LearnerProfile, User
from app.schemas import DEFAULT_PROFILE, ProfileOut, ProfilePut

router = APIRouter(prefix="/profile", tags=["profile"])


def load_or_create_profile(db: Session, user_id: str) -> LearnerProfile:
    row = db.get(LearnerProfile, user_id)
    if row is None:
        row = LearnerProfile(user_id=user_id, data=dict(DEFAULT_PROFILE))
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def merged_profile(row: LearnerProfile | None) -> dict[str, object]:
    data: dict[str, object] = dict(DEFAULT_PROFILE)
    if row is not None and isinstance(row.data, dict):
        data.update(row.data)
    return data


@router.get("", response_model=ProfileOut)
def get_profile(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, object]:
    row = load_or_create_profile(db, user.id)
    return merged_profile(row)


@router.put("", response_model=ProfileOut)
def put_profile(body: ProfilePut, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> dict[str, object]:
    row = load_or_create_profile(db, user.id)
    data = merged_profile(row)
    data.update(body.model_dump(exclude_unset=True))
    row.data = data
    db.commit()
    return data
