import uuid
from datetime import date, datetime
import datetime as _dt
from typing import Any

from sqlalchemy import JSON, Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def _uuid_str() -> str:
    return uuid.uuid4().hex


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid_str)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(255))
    password_hash: Mapped[str] = mapped_column(String(255))


class LearnerProfile(Base):
    __tablename__ = "learner_profiles"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class Consent(Base):
    __tablename__ = "consents"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    voice: Mapped[bool] = mapped_column(Boolean, default=False)
    telemetry: Mapped[bool] = mapped_column(Boolean, default=False)
    memory: Mapped[bool] = mapped_column(Boolean, default=False)


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid_str)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    filename: Mapped[str] = mapped_column(String(512))
    doc_type: Mapped[str] = mapped_column(String(32))
    char_count: Mapped[int] = mapped_column(Integer, default=0)
    text_content: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: _dt.datetime.now(_dt.timezone.utc).replace(tzinfo=None))


class Adaptation(Base):
    __tablename__ = "adaptations"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid_str)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True)
    result: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: _dt.datetime.now(_dt.timezone.utc).replace(tzinfo=None))


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid_str)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float] | None] = mapped_column(JSON, nullable=True, default=None)


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid_str)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(512))
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(16), default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: _dt.datetime.now(_dt.timezone.utc).replace(tzinfo=None))


class Sprint(Base):
    __tablename__ = "sprints"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid_str)
    task_id: Mapped[str] = mapped_column(ForeignKey("tasks.id"), index=True)
    index: Mapped[int] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(Text)
    minutes: Mapped[int] = mapped_column(Integer, default=25)
    done: Mapped[bool] = mapped_column(Boolean, default=False)


class VivaSession(Base):
    __tablename__ = "viva_sessions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid_str)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: _dt.datetime.now(_dt.timezone.utc).replace(tzinfo=None))


class VivaTurn(Base):
    __tablename__ = "viva_turns"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid_str)
    session_id: Mapped[str] = mapped_column(ForeignKey("viva_sessions.id"), index=True)
    index: Mapped[int] = mapped_column(Integer)
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)


class Checkin(Base):
    __tablename__ = 'checkins'

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid_str)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    mood: Mapped[int] = mapped_column(Integer)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[_dt.datetime] = mapped_column(
        DateTime, default=lambda: _dt.datetime.now(_dt.timezone.utc).replace(tzinfo=None)
    )


class InteractionEvent(Base):
    __tablename__ = 'interaction_events'

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid_str)
    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), index=True)
    document_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)
    event: Mapped[str] = mapped_column(String(48))
    concept: Mapped[str | None] = mapped_column(Text, nullable=True)
    meta: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[_dt.datetime] = mapped_column(
        DateTime, default=lambda: _dt.datetime.now(_dt.timezone.utc).replace(tzinfo=None)
    )


class PreferenceScore(Base):
    __tablename__ = 'preference_scores'

    user_id: Mapped[str] = mapped_column(ForeignKey('users.id'), primary_key=True)
    scores: Mapped[dict[str, float]] = mapped_column(JSON, default=dict)
    updated_at: Mapped[_dt.datetime] = mapped_column(
        DateTime, default=lambda: _dt.datetime.now(_dt.timezone.utc).replace(tzinfo=None)
    )
