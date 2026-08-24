from datetime import datetime as dt, timezone as tz

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.api.documents import _audio_filenames_from_adaptations
from app.core.config import settings
from app.core.consent import require_consent
from app.core.security import _bearer_scheme, get_current_user, verify_token
from app.db import get_db
from app.models import (
    Adaptation,
    Checkin,
    Consent,
    Document,
    DocumentChunk,
    InteractionEvent,
    LearnerProfile,
    PreferenceScore,
    Sprint,
    Task,
    User,
    VivaSession,
    VivaTurn,
)
from app.schemas import AnalyticsOut, MemoryConcept, MemoryOut

router = APIRouter(tags=["privacy"])


@router.get("/me/export")
def export_my_data(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
):
    user_id = verify_token(credentials.credentials) if credentials else None
    user = db.get(User, user_id) if user_id else None
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    profile_row = db.get(LearnerProfile, user.id)
    score_row = db.get(PreferenceScore, user.id)
    consent_row = db.get(Consent, user.id)
    events = db.query(InteractionEvent).filter(InteractionEvent.user_id == user.id).all()
    checkins = db.query(Checkin).filter(Checkin.user_id == user.id).all()
    docs = db.query(Document).filter(Document.user_id == user.id).all()
    doc_ids = [d.id for d in docs]
    adaptations = (
        db.query(Adaptation).filter(Adaptation.document_id.in_(doc_ids)).all()
        if doc_ids
        else []
    )
    tasks = db.query(Task).filter(Task.user_id == user.id).all()
    task_ids = [t.id for t in tasks]
    sprints = (
        db.query(Sprint).filter(Sprint.task_id.in_(task_ids)).order_by(Sprint.index.asc()).all()
        if task_ids
        else []
    )
    sessions = db.query(VivaSession).filter(VivaSession.user_id == user.id).all()
    session_ids = [s.id for s in sessions]
    turns = (
        db.query(VivaTurn).filter(VivaTurn.session_id.in_(session_ids)).order_by(VivaTurn.index.asc()).all()
        if session_ids
        else []
    )

    def iso(value: object) -> str:
        return value.isoformat() if isinstance(value, dt) else ""

    return {
        "exported_at": dt.now(tz.utc).replace(tzinfo=None).isoformat(),
        "profile": {"user": {"email": user.email, "display_name": user.display_name},
                    "learner_profile": profile_row.data if profile_row else {},
                    "preference_scores": score_row.scores if score_row else {}},
        "consents": {"voice": consent_row.voice if consent_row else False,
                     "telemetry": consent_row.telemetry if consent_row else False,
                     "memory": consent_row.memory if consent_row else False},
        "documents": [{"id": d.id, "filename": d.filename, "doc_type": d.doc_type,
                       "char_count": d.char_count, "created_at": d.created_at.isoformat(),
                       "text_content": d.text_content} for d in docs],
        "adaptations": [{"id": a.id, "document_id": a.document_id,
                         "created_at": a.created_at.isoformat(),
                         "results": (a.result or {}).get("results", [])} for a in adaptations],
        "tasks": [{"id": t.id, "title": t.title, "due_date": t.due_date.isoformat() if t.due_date else None,
                   "notes": t.notes, "status": t.status, "created_at": t.created_at.isoformat(),
                   "sprints": [{"id": s.id, "index": s.index, "description": s.description,
                                "minutes": s.minutes, "done": s.done}
                               for s in sprints if s.task_id == t.id]} for t in tasks],
        "viva_sessions": [{"id": v.id, "document_id": v.document_id, "created_at": iso(v.created_at),
                           "turns": [{"index": tn.index, "question": tn.question, "answer": tn.answer,
                                      "feedback": tn.feedback, "score": tn.score}
                                     for tn in turns if tn.session_id == v.id]} for v in sessions],
        "interaction_events": [{"event": e.event, "concept": e.concept,
                                "created_at": e.created_at.isoformat(),
                                "meta": e.meta} for e in events],
        "wellbeing_checkins": [{"mood": c.mood, "note": c.note,
                                "created_at": c.created_at.isoformat()} for c in checkins],
    }


def _collect_user_files(db: Session, user: User) -> list:
    paths: list = []
    docs = db.query(Document).filter(Document.user_id == user.id).all()
    adaptations = (
        db.query(Adaptation)
        .join(Document, Adaptation.document_id == Document.id)
        .filter(Document.user_id == user.id)
        .all()
    )
    for name in _audio_filenames_from_adaptations(adaptations):
        paths.append(settings.audio_dir / name)
    sessions = db.query(VivaSession).filter(VivaSession.user_id == user.id).all()
    for s in sessions:
        for turn in db.query(VivaTurn).filter(VivaTurn.session_id == s.id).all():
            paths.append(settings.audio_dir / f"viva_{s.id}_{turn.index}.mp3")
    for d in docs:
        paths.append(settings.docs_dir / f"{d.id}_{d.filename}")
    return paths


@router.delete("/me")
def delete_my_account(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    file_paths = _collect_user_files(db, user)

    session_ids = [
        row[0]
        for row in db.query(VivaSession.id).filter(VivaSession.user_id == user.id).all()
    ]
    if session_ids:
        db.query(VivaTurn).filter(VivaTurn.session_id.in_(session_ids)).delete(synchronize_session=False)
        db.query(VivaSession).filter(VivaSession.user_id == user.id).delete(synchronize_session=False)

    task_ids = [row[0] for row in db.query(Task.id).filter(Task.user_id == user.id).all()]
    if task_ids:
        db.query(Sprint).filter(Sprint.task_id.in_(task_ids)).delete(synchronize_session=False)
        db.query(Task).filter(Task.user_id == user.id).delete(synchronize_session=False)

    doc_ids = [row[0] for row in db.query(Document.id).filter(Document.user_id == user.id).all()]
    if doc_ids:
        db.query(DocumentChunk).filter(DocumentChunk.document_id.in_(doc_ids)).delete(synchronize_session=False)
        db.query(Adaptation).filter(Adaptation.document_id.in_(doc_ids)).delete(synchronize_session=False)
        db.query(Document).filter(Document.user_id == user.id).delete(synchronize_session=False)

    db.query(Checkin).filter(Checkin.user_id == user.id).delete(synchronize_session=False)
    db.query(InteractionEvent).filter(InteractionEvent.user_id == user.id).delete(synchronize_session=False)
    db.query(PreferenceScore).filter(PreferenceScore.user_id == user.id).delete(synchronize_session=False)
    db.query(LearnerProfile).filter(LearnerProfile.user_id == user.id).delete(synchronize_session=False)
    db.query(Consent).filter(Consent.user_id == user.id).delete(synchronize_session=False)
    db.delete(user)
    db.commit()

    for path in file_paths:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"detail": "Your account and all associated data have been deleted."},
    )


@router.delete("/interactions", response_model=dict)
def delete_history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    deleted_events = (
        db.query(InteractionEvent)
        .filter(InteractionEvent.user_id == user.id)
        .delete()
    )
    row = db.get(PreferenceScore, user.id)
    from app.services.preferences import DEFAULT_SCORES

    if row is not None:
        row.scores = dict(DEFAULT_SCORES)
        row.updated_at = dt.now(tz.utc).replace(tzinfo=None)
    db.commit()
    return {"deleted_events": deleted_events, "scores_reset": True}


def _analytics(db: Session, user: User) -> dict:
    events = db.query(InteractionEvent).filter(InteractionEvent.user_id == user.id).all()
    by_event: dict[str, int] = {}
    for e in events:
        by_event[e.event] = by_event.get(e.event, 0) + 1
    now = dt.now(tz.utc).replace(tzinfo=None)
    recent = sum(
        1
        for e in events
        if e.created_at and (now - e.created_at).total_seconds() < 86400
    )
    quiz_correct = by_event.get("quiz_correct", 0)
    quiz_wrong = by_event.get("quiz_incorrect", 0)
    adaptive_signals = {
        "feedback_too_long", "requested_simpler", "explain_deeper",
        "explain_deeper_stepwise", "requested_example", "opened_concept_map",
        "read_aloud", "played_audio",
    }
    return {
        "documents_count": db.query(Document).filter(Document.user_id == user.id).count(),
        "adaptive_changes_total": sum(n for k, n in by_event.items() if k in adaptive_signals),
        "adaptive_changes_last_24h": sum(
            1 for e in events
            if e.event in adaptive_signals and e.created_at
            and (now - e.created_at).total_seconds() < 86400
        ),
        "interactions_total": len(events),
        "quiz_correct": quiz_correct,
        "quiz_incorrect": quiz_wrong,
        "top_interactions": sorted(by_event.items(), key=lambda kv: -kv[1])[:6],
    }


@router.get("/analytics", response_model=AnalyticsOut)
def get_analytics(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return AnalyticsOut(**_analytics(db, user))


@router.get("/preferences/memory", response_model=MemoryOut)
def learning_memory(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    require_consent(user, "memory", db)
    events = (
        db.query(InteractionEvent)
        .filter(
            InteractionEvent.user_id == user.id,
            InteractionEvent.concept.isnot(None),
            InteractionEvent.event.in_(["quiz_incorrect", "requested_simpler", "feedback_need_example"]),
        )
        .all()
    )
    counts: dict[str, int] = {}
    for e in events:
        counts[e.concept] = counts.get(e.concept, 0) + 1
    struggled = [
        MemoryConcept(concept=c, misses=n)
        for c, n in sorted(counts.items(), key=lambda kv: -kv[1])[:5]
    ]
    suggestions = [
        f"Review \"{c.concept}\" with an example first — you missed it {c.misses} time(s)."
        for c in struggled
    ]
    return MemoryOut(struggled_concepts=struggled, suggestions=suggestions)
