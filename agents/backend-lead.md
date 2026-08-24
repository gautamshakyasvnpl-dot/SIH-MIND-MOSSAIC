# Brief: backend-lead

Read `AGENTS.md` first — it is law (ownership, contracts, style).

## Mission (Week 1)
FastAPI application implementing the full Week-1 API contract exactly as specified in AGENTS.md: auth (JWT), profile, consents, documents CRUD, adapt endpoint wiring services, audio file serving. CORS enabled for http://localhost:5173.

## Ownership
`backend/app/main.py`, `backend/app/core/**`, `backend/app/db.py`, `backend/app/models.py`, `backend/app/api/**`, `backend/app/schemas.py`. Nothing else.

## Architecture rules
- SQLAlchemy 2.0 declarative; `DATABASE_URL` env default `sqlite:///./sahaik.db`. Tables: users, learner_profiles (JSONB/JSON prefs column), consents, documents, adaptations.
- Pydantic v2 request/response models in schemas.py matching the contract JSON exactly.
- Auth: python-jose HS256 JWT, 7-day expiry, `JWT_SECRET` env default dev value; password = stdlib pbkdf2_hmac sha256 200k iters, stored `salt$hash`, salt via secrets.token_hex(16). Duplicate email 409. 401 on bad credentials/expired tokens.
- Documents: save uploads to `backend/uploads/docs/{uuid}_{filename}`; call `app.services.extraction.extract_text(filename, data)` (ml-lead implements; import lazily/guarded so app still boots if that module is mid-build? NO — it will exist at integration; code against the signature).
- Adapt endpoint: load doc text + caller's merged profile → call `app.services.adapter.adapt_document(text, profile)` → persist result row → return its dict directly.
- Audio serving: FileResponse from `backend/uploads/audio/`, content_type audio/mpeg.
- Create `backend/uploads/{docs,audio}/` dirs on startup if missing.

## Verify before reporting
1. `backend\.venv\Scripts\python -c "from app.main import app"` succeeds (workdir backend).
2. Start uvicorn briefly and curl /api/auth/register then /api/auth/me round-trip works.
Report: files created, endpoints implemented, verification output.
