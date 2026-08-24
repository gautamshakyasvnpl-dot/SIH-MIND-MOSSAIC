from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.documents import _get_owned_document
from app.core.security import get_current_user
from app.db import get_db
from app.models import Document, User
from app.schemas import (
    ExplainIn,
    ExplainOut,
    QuizItem,
    QuizOut,
    ReaderCardOut,
    ReaderHints,
    ReaderOut,
    QuizRequest,
)
from app.services import preferences as prefs
from app.services import reader as reader_svc

router = APIRouter(prefix="/documents", tags=["reader"])


def _user_scores(db: Session, user: User) -> dict[str, float]:
    from app.api.preferences import _load_scores

    return _load_scores(db, user)


@router.get("/{doc_id}/reader", response_model=ReaderOut)
def get_reader(doc_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ReaderOut:
    doc = _get_owned_document(db, doc_id, user)
    cards = reader_svc.build_cards(doc.text_content or "")
    if not cards:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document has no extractable content to build cards from",
        )
    hints = prefs.presentation_hints(_user_scores(db, user))
    return ReaderOut(
        document_id=doc.id,
        filename=doc.filename,
        cards=[ReaderCardOut(**c) for c in cards],
        presentation=ReaderHints(**hints),
    )


@router.post("/explain", response_model=ExplainOut)
def explain(body: ExplainIn, user: User = Depends(get_current_user)) -> ExplainOut:
    del user
    transform = (body.transform or "level").strip().lower()

    if transform == "bullets":
        return ExplainOut(level=body.level, text=reader_svc.to_bullets(body.text), engine="heuristic-transform")
    if transform == "summary":
        return ExplainOut(level=body.level, text=reader_svc.summarize(body.text), engine="heuristic-transform")
    if transform == "analogy":
        _, text = reader_svc.explain_ladder(body.text, 3)
        return ExplainOut(level=3, text=text, engine="heuristic-ladder")
    if transform == "translate":
        from fastapi import HTTPException

        from app.services import ai_provider
        from app.services.guard import data_block

        provider = ai_provider.get_provider()
        if isinstance(provider, ai_provider.NullProvider):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Translation needs an AI key on the server (LLM_API_KEY or GEMINI_API_KEY).",
            )
        out = provider.invoke(
            f"Translate the following study material into {body.target_lang}. "
            f"Keep it simple and faithful. Reply only with the translation.\n\n{data_block(body.text)}"
        )
        if not out:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Translation failed this time.")
        return ExplainOut(level=body.level, text=out, engine=provider.name)

    level, text = reader_svc.explain_ladder(body.text, body.level, body.context or "")
    return ExplainOut(level=level, text=text, engine="heuristic-ladder")


@router.post("/{doc_id}/quiz", response_model=QuizOut)
def quiz(
    doc_id: str,
    body: QuizRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> QuizOut:
    doc = _get_owned_document(db, doc_id, user)
    items = reader_svc.make_quiz(doc.text_content or "", count=body.count)
    if not items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not enough content in this document to build a quiz",
        )
    return QuizOut(items=[QuizItem(**i) for i in items])
