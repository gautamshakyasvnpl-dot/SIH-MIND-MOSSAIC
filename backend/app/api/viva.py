import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.documents import _get_owned_document
from app.api.tutor import ensure_chunks
from app.core.security import _bearer_scheme, get_current_user
from app.db import get_db
from app.models import Document, User, VivaSession, VivaTurn
from app.schemas import AnswerIn, VivaAnswerOut, VivaSessionOut, VivaStartOut, VivaStartRequest, VivaTurnOut

router = APIRouter(tags=["viva"])

VIVA_QUESTION_COUNT = 5


@router.post("/documents/{doc_id}/viva/start", response_model=VivaStartOut)
def start_viva(
    doc_id: str,
    body: VivaStartRequest | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> VivaStartOut:
    doc = _get_owned_document(db, doc_id, user)
    difficulty = (body.difficulty if body else None) or "medium"
    if difficulty not in {"easy", "medium", "hard"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="difficulty must be easy, medium or hard")

    chunks = ensure_chunks(db, doc)
    chunk_texts = [c.text for c in chunks]

    from app.services.tutor import make_viva_question

    asked: list[str] = []
    questions: list[str] = []
    while len(questions) < VIVA_QUESTION_COUNT:
        question = make_viva_question(chunk_texts, asked=asked, difficulty=difficulty)
        if question is None:
            break
        questions.append(question)
    if len(questions) < VIVA_QUESTION_COUNT:
        raise HTTPException(
            status_code=422,
            detail="This document does not contain enough material for a full five-question viva.",
        )

    session = VivaSession(id=uuid.uuid4().hex, user_id=user.id, document_id=doc.id)
    db.add(session)
    for i, question in enumerate(questions):
        db.add(VivaTurn(id=uuid.uuid4().hex, session_id=session.id, index=i, question=question))
    db.commit()
    return VivaStartOut(session_id=session.id, document_id=doc.id, question=questions[0], turn_count=1)


@router.post("/viva/{session_id}/answer", response_model=VivaAnswerOut)
def answer_viva(
    session_id: str, body: AnswerIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> VivaAnswerOut:
    session = db.get(VivaSession, session_id)
    if session is None or session.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    turns = (
        db.query(VivaTurn)
        .filter(VivaTurn.session_id == session.id)
        .order_by(VivaTurn.index.asc())
        .all()
    )
    current = next((t for t in turns if t.answer is None), None)
    if current is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This viva session is already complete; all five questions have been answered.",
        )

    chunks = ensure_chunks(db, db.get(Document, session.document_id))
    chunk_texts = [c.text for c in chunks]

    from app.services.retrieval import search
    from app.services.tutor import evaluate_answer

    ref_indices = search(chunk_texts, current.question, top_k=1)
    ref_text = chunk_texts[ref_indices[0]] if ref_indices else ""
    evaluation = evaluate_answer(current.question, ref_text, body.answer)

    current.answer = body.answer
    current.feedback = str(evaluation.get("feedback", ""))
    current.score = int(evaluation.get("score", 0))

    next_turn = turns[current.index + 1] if current.index + 1 < len(turns) else None
    next_question = next_turn.question if next_turn is not None else None
    db.commit()

    turn_count = VIVA_QUESTION_COUNT if next_question is None else min(current.index + 2, VIVA_QUESTION_COUNT)
    return VivaAnswerOut(
        feedback=current.feedback,
        score=current.score,
        next_question=next_question,
        done=next_question is None,
        turn_count=turn_count,
    )


@router.get("/viva/{session_id}", response_model=VivaSessionOut)
def get_viva_session(
    session_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> VivaSessionOut:
    session = db.get(VivaSession, session_id)
    if session is None or session.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    turns = (
        db.query(VivaTurn)
        .filter(VivaTurn.session_id == session.id)
        .order_by(VivaTurn.index.asc())
        .all()
    )
    open_position = next((i for i, t in enumerate(turns) if t.answer is None), None)
    visible = turns if open_position is None else turns[: open_position + 1]
    return VivaSessionOut(
        session_id=session.id,
        document_id=session.document_id,
        done=open_position is None,
        turns=[
            VivaTurnOut(index=t.index, question=t.question, answer=t.answer, feedback=t.feedback, score=t.score)
            for t in visible
        ],
    )


def question_audio_response(db: Session, session: VivaSession) -> FileResponse:
    from app.core.config import settings

    turn = (
        db.query(VivaTurn)
        .filter(VivaTurn.session_id == session.id, VivaTurn.answer.is_(None))
        .order_by(VivaTurn.index.asc())
        .first()
    )
    if turn is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='No open question')

    audio_dir = settings.audio_dir
    audio_dir.mkdir(parents=True, exist_ok=True)
    filename = f'viva_{session.id}_{turn.index}.mp3'
    out_path = audio_dir / filename
    if not out_path.exists():
        from app.services.tts import synthesize_speech_bounded

        try:
            synthesize_speech_bounded(turn.question, out_path, max_words=80)
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=f'Audio unavailable: {exc}') from exc
    return FileResponse(out_path, media_type='audio/mpeg', filename=filename)


@router.get('/viva/{session_id}/question-audio')
def question_audio(
    session_id: str,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
    db: Session = Depends(get_db),
) -> FileResponse:
    from app.core.security import verify_token

    if credentials is None or not credentials.credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')
    owner_id = verify_token(credentials.credentials)
    user = db.get(User, owner_id) if owner_id else None
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid or expired token')
    session = db.get(VivaSession, session_id)
    if session is None or session.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Session not found')
    return question_audio_response(db, session)
