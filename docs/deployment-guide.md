# NEUROLEARN (repo codename SahAIk) — Deployment Guide

Scope: local development (exact commands) and Docker Compose deployment. Every step is labelled with how it was verified: **verified** = executed and observed, **static-only** = checked without executing (see §5 for the honest verification-status box).

## 1. Local development — verified

Prerequisites: Python 3.11+ (venv expected at `backend/.venv`), Node.js 18+.

Backend:
```
backend\.venv\Scripts\python -m pip install -r backend\requirements.txt
backend\.venv\Scripts\python backend\scripts\seed_demo.py                        # demo account + seeded course
backend\.venv\Scripts\python -m pytest backend/tests -q                          # 183 passed offline
backend\.venv\Scripts\python -m uvicorn app.main:app --reload --app-dir backend  # run API :8000
```

Frontend:
```
cd frontend; npm run dev     # :5173
cd frontend; npm run build   # tsc strict + production build
cd frontend; npm run test    # vitest utility suite (11 tests)
```

The Vite dev server proxies nothing by default; the frontend calls the API directly at `import.meta.env.VITE_API_BASE || "http://localhost:8000"`. With both servers running: open `http://localhost:5173`, register (or log in as `demo@neurolearn.app` / `demo12345`), complete onboarding, upload a document (`.pptx`/`.pdf`/`.docx`/`.txt`, ≤ 20 MB), and adapt it.

Default storage is SQLite at `sqlite:///./sahaik.db`; uploaded documents land in `UPLOAD_DIR/docs` and generated MP3s in `UPLOAD_DIR/audio` (`UPLOAD_DIR` defaults to `uploads` relative to the working directory).

## 2. Environment variable checklist

| Variable | Local default | Production requirement |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./sahaik.db` | Set to a PostgreSQL URL before scaling beyond one worker. |
| `JWT_SECRET` | development default | **Required in production.** Strong random value; also keys the media-download HMACs; rotating it invalidates outstanding tokens and media links (7-day auth expiry). |
| `UPLOAD_DIR` | `uploads` | Point at a persistent mounted volume in any containerized/multi-instance deployment. |
| `ALLOWED_ORIGINS` | `http://localhost:5173` | Comma-separated CORS allowlist; set to your deployed frontend origin. Do not ship permissive origins. |
| `GEMINI_API_KEY` | unset — heuristic fallback active, `"used_llm": false` | Optional. The app must never fail in its absence (graceful degradation is a hard project rule). |
| `LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL` | unset / unset / `gpt-4o-mini` | Optional OpenAI-compatible provider override (read by `services/ai_provider.py`; takes priority over Gemini). |
| `VITE_API_BASE` | falls back to `http://localhost:8000` | Set at frontend build time to the public API origin. |

See [`.env.example`](../.env.example).

## 3. Local static hosting sketch

- Build once with the production API base set: `cd frontend && npm run build`.
- Deploy `frontend/dist/` to any static host with SPA rewriting of all routes to `index.html`.
- Configure `VITE_API_BASE` in the host's build environment so it is baked into the bundle.

## 4. Docker Compose

Artifacts: `backend/Dockerfile` (python:3.12-slim, uvicorn on :8000, 2 workers, `ENV UPLOAD_DIR=/data/uploads`), `frontend/Dockerfile` (node build stage → nginx serving `/usr/share/nginx/html`), `frontend/nginx.conf` (`try_files $uri $uri/ /index.html` SPA fallback so deep links like `/document/<id>/viva` survive refresh + 30-day immutable asset caching), and `docker-compose.yml`.

Compose topology (actual service names from `docker-compose.yml`):

| Service | Build context | Host port → container port | Notes |
|---|---|---|---|
| `api` | `./backend` | `8000 → 8000` | Env: `DATABASE_URL=sqlite:////data/sahaik.db`, `UPLOAD_DIR=/data/uploads`, `ALLOWED_ORIGINS` (from host env, default `http://localhost:5173`), `JWT_SECRET` (default `change-me-in-production` — override!), optional `GEMINI_API_KEY`. Named volume `sahaik-data` mounted at `/data`. |
| `web` | `./frontend` | `5173 → 80` | Build arg `VITE_API_BASE=http://localhost:8000`; nginx serves the SPA. Depends on `api`. |

```bash
docker compose up --build
# API on http://localhost:8000, UI on http://localhost:5173
```

The named volume `sahaik-data` persists both the SQLite file and uploads across container restarts; set `JWT_SECRET` in production or point `DATABASE_URL` at managed Postgres instead.

## 5. Verification status — read this before trusting §4

| Step | Status |
|---|---|
| `docker-compose.yml` YAML parse; COPY source paths and `nginx.conf` existence inside image contexts | **Statically verified** (audit machine has no Docker daemon) |
| Backend/frontend test suites behind the images (`pytest` 183 offline, vitest 11/11) | **Verified** outside Docker against the same source |
| `docker compose build` (image builds) | **NOT executed** — requires a Docker machine |
| `docker compose up` + container smoke: register → upload → adapt → fetch audio through published ports | **NOT executed** |
| Restart-persistence check (SQLite + uploads surviving `docker compose down/up` via `sahaik-data`) | **NOT executed** |

**Required first-run checklist on a Docker machine:** (1) `docker compose build`; (2) `docker compose up -d`; (3) register via the UI on :5173 and upload/adapt a sample `.txt`; (4) play the returned MP3; (5) `docker compose down && docker compose up -d` and confirm the account, document and audio still resolve. Treat the first successful pass as the deployment smoke test.

## 6. Known limitations

- **SQLite default:** fine for demo/single-node evaluation; use PostgreSQL under load (config-only change via `DATABASE_URL`). No Alembic migrations yet — schema is created by `create_all` on boot.
- **Local disk media:** uploads/MP3s live under `UPLOAD_DIR`; not replicated across instances.
- **gTTS network dependency:** TTS synthesis calls an external Google endpoint; fully offline environments will see the TTS step fail rather than degrade silently.
- **No CI/CD pipeline yet:** verification is currently the documented pytest/vitest/build/wcag_audit commands run locally.
- **Container stack unproven end-to-end** until the §5 Docker-machine checklist passes.
