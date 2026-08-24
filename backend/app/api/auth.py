from fastapi import APIRouter, Depends, HTTPException, status

from app.core.ratelimit import ip_limited
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_current_user, hash_password, verify_password
from app.db import get_db
from app.models import User
from app.schemas import LoginIn, RegisterIn, TokenOut, UserOut

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenOut, dependencies=[ip_limited(60)])
def register(body: RegisterIn, db: Session = Depends(get_db)) -> TokenOut:
    existing = db.query(User).filter(func.lower(User.email) == body.email).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    user = User(email=body.email, display_name=body.display_name, password_hash=hash_password(body.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered") from exc
    db.refresh(user)
    return TokenOut(token=create_access_token(user.id), user=UserOut(id=user.id, email=user.email, display_name=user.display_name))


@router.post("/login", response_model=TokenOut, dependencies=[ip_limited(60)])
def login(body: LoginIn, db: Session = Depends(get_db)) -> TokenOut:
    user = db.query(User).filter(func.lower(User.email) == body.email).first()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return TokenOut(token=create_access_token(user.id), user=UserOut(id=user.id, email=user.email, display_name=user.display_name))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut(id=user.id, email=user.email, display_name=user.display_name)
