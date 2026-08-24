import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.documents import _get_owned_document
from app.core.ratelimit import ip_limited, user_limited
from app.core.security import get_current_user
from app.db import get_db
from app.models import Document, DocumentChunk, User
from app.schemas import AskIn, AskOut, AskSource

router = APIRouter(tags=["tutor"])


def ensure_chunks(db: Session, doc: Document) -> list[DocumentChunk]:
    chunks = (
        db.query(DocumentChunk)
        .filter(DocumentChunk.document_id == doc.id)
        .order_by(DocumentChunk.chunk_index.asc())
        .all()
    )
    if not chunks:
        from app.services.chunking import chunk_text

        texts = chunk_text(doc.text_content or "")
        chunks = [
            DocumentChunk(id=uuid.uuid4().hex, document_id=doc.id, chunk_index=i, text=t)
            for i, t in enumerate(texts)
        ]
        db.add_all(chunks)
        db.commit()

    if all(c.embedding is None for c in chunks):
        from app.services.retrieval import embed_texts

        vectors = embed_texts([c.text for c in chunks])
        if vectors is not None:
            for c, v in zip(chunks, vectors):
                c.embedding = v
            db.commit()
    return chunks


@router.post("/documents/{doc_id}/ask", response_model=AskOut, dependencies=[user_limited(120)])
def ask_question(
    doc_id: str, body: AskIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)
) -> AskOut:
    doc = _get_owned_document(db, doc_id, user)
    chunks = ensure_chunks(db, doc)
    chunk_texts = [c.text for c in chunks]
    if not chunk_texts:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Document has no extractable content")

    from app.services.retrieval import embed_texts, search_with_embeddings
    from app.services.tutor import answer_question

    query_vector: list[float] | None = None
    if all(c.embedding is not None for c in chunks):
        embedded = embed_texts([body.question])
        query_vector = embedded[0] if embedded else None

    top_indices = search_with_embeddings(
        [c.embedding for c in chunks], query_vector, chunk_texts, body.question, top_k=2
    )
    top_chunks = [chunk_texts[i] for i in top_indices]
    result = answer_question(top_chunks, body.question)
    sources = [AskSource(chunk_index=i, snippet=chunk_texts[i][:160]) for i in top_indices]
    return AskOut(
        document_id=doc.id,
        answer=str(result.get("answer", "")),
        used_llm=bool(result.get("used_llm", False)),
        sources=sources,
    )
