# NEUROLEARN

AI-Powered Inclusive Learning & Wellbeing Platform for Neurodivergent Learners.
Repository codename: SahAIk (legacy name still visible in some code identifiers).

**Smart India Hackathon 2026** · Problem Statement ID **GGSIPU2605** · USAR, GGSIPU East Delhi Campus · Theme: Inclusive Education, Accessibility & Digital Health.

NEUROLEARN reshapes the same lecture material around how each student learns:
an **Adaptive Cognitive Experience Engine** turns feedback ("too long",
"need example", quiz results, audio/map usage) into transparent learning-
preference scores that visibly change the Adaptive Reader — with a
"Why am I seeing this?" panel explaining every change. Preferences, never
diagnoses. See [`ARCHITECTURE.md`](ARCHITECTURE.md),
[`docs/architecture-diagram.md`](docs/architecture-diagram.md) and
[`PROJECT_AUDIT.md`](PROJECT_AUDIT.md).

## Feature status (all Week 1–3 scope IMPLEMENTED)

- **Auth & onboarding:** register/login (`POST /api/auth/*`), profiler wizard → LearnerProfile v1, granular consents (`voice`, `telemetry`, `memory`, each **default off**) enforced server-side — voice gates STT/dictation, telemetry gates interaction logging, memory gates the struggled-concepts history. Consent-denied calls get calm HTTP 403s.
- **Documents:** upload `.pptx`/`.pdf`/`.docx`/`.txt` ≤ 20 MB; adaptation to simplified text + TTS MP3, every result carrying a plain-language `explanation` and a `used_llm` flag; OCR upload of page images via `POST /api/documents/image` (needs an LLM key).
- **Adaptive Reader:** preference scores updated by a transparent rule (`new = 0.7*old + 0.3*signal`, clamped [0.02, 0.98]) with an explanation returned on every change; example-first cards, concept map, quizzes; struggled concepts resurface automatically; "Why am I seeing this?" everywhere.
- **Tutor (grounded Q&A):** `POST /api/documents/{id}/ask` answers only from retrieved document chunks (~120-word chunks, 20-word overlap) with cited `sources`.
- **EF Coach:** tasks broken into sprints sized by pace (15-min gentle / 25-min standard); toggle sprints; task completes when all sprints do.
- **Viva Coach (text mode):** exactly **five** questions per session; feedback + 0–2 score per answer; transcript endpoint; done only after the fifth answer.
- **Wellbeing:** mood check-ins 1..5 with deterministic crisis-safe suggestions (mood ≤ 2 → box-breathing exercise + EOC/counselling escalation line); communication assistant + structured plans.
- **Recommender:** `GET /api/documents/{id}/recommend` returns format + reason citing the profile fields used (audio affinity always recommends audio).
- **Privacy suite:** full data export (`GET /api/me/export`), interaction-history wipe, and account deletion with complete cascade (`DELETE /api/me`). Media downloads use short-lived (60-second) HMAC-signed tokens — no JWT ever appears in a URL; the export download requires the Bearer header.
- **Hardening:** sliding-window rate limits, prompt-injection neutralisation/fencing on every LLM prompt carrying document text, CORS allowlist via env var.
- **Accessibility:** dyslexia-friendly font, wide spacing, reduced motion, skip link, keyboard shortcuts (Alt+1..5, M), Web-Speech dictation gated by voice consent, read-aloud.

### Not included in this release

- **Camera-based facial-emotion recognition** — excluded by design (spec §2.4). Absent from the UI and the backend router is not mounted (404; absence verified against OpenAPI). Text-emotion detection on self-reported notes remains.
- **pgvector / embedding-model retrieval** — deferred; TF-IDF cosine is the shipped implementation (swap-in point: `services/retrieval.py`).
- **Whisper LoRA fine-tuning** — deferred; STT is browser Web Speech API plus optional Gemini inline-audio transcription.

## Quickstart

Prerequisites: Python 3.11+ (venv expected at `backend/.venv`), Node.js 18+.

```bash
backend\.venv\Scripts\python -m pip install -r backend\requirements.txt
backend\.venv\Scripts\python backend\scripts\seed_demo.py        # demo account + seeded course
backend\.venv\Scripts\python -m uvicorn app.main:app --reload --app-dir backend  # API :8000
cd frontend && npm run dev                                        # UI :5173
```

Demo login: `demo@neurolearn.app` / `demo12345` (created by `seed_demo.py`, idempotent).

Manual E2E check: start both servers, register (or use the demo login), complete onboarding, upload a `.pptx`/`.pdf`/`.docx`/`.txt` file ≤ 20 MB, request adaptation, view simplified text and play the MP3.

## The demo loop (judges: 3 minutes)

1. Sign in → Dashboard → open a lecture's **Adaptive Reader**
2. Press **"Too long"** / **"Make simpler"** on a card → watch the level drop
3. Open **"Why am I seeing this?"** → the score change is explained
4. **Quiz me** → answer → Personalization Center updates live (`/preferences`)
5. Ask the document a question (**Ask** panel shows cited sources), practice a
   five-question viva, create a task on the sprint board, log a low-mood
   check-in (box-breathing suggestion), then export or delete your data in
   Preferences.

All AI features degrade gracefully without any API key (heuristic mode,
honest `used_llm:false` labels).

## Environment variables

All variables are optional; the application runs with safe defaults.

| Variable | Default | Effect |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./sahaik.db` | SQLAlchemy connection string; set to PostgreSQL for production. |
| `JWT_SECRET` | development default | HS256 signing key for auth tokens **and** media-download HMACs. Set a strong value outside local development. |
| `UPLOAD_DIR` | `uploads` | Root of all file storage — uploaded documents land in `$UPLOAD_DIR/docs`, generated MP3s in `$UPLOAD_DIR/audio`. Point it at a mounted volume in production. |
| `ALLOWED_ORIGINS` | `http://localhost:5173` | Comma-separated CORS allowlist consumed by the FastAPI CORSMiddleware. Set to the deployed frontend origin. |
| `GEMINI_API_KEY` | unset | Enables Gemini for simplification, grounded answers, OCR and inline-audio STT. Unset ⇒ deterministic heuristic fallbacks and `"used_llm": false`; the app never fails because this key is missing. |
| `LLM_API_KEY` / `LLM_BASE_URL` / `LLM_MODEL` | unset / unset / `gpt-4o-mini` | Optional OpenAI-compatible provider override, read by `services/ai_provider.py` (priority over Gemini). |
| `GEMINI_MODEL` / `GEMINI_EMBED_MODEL` | `gemini-2.0-flash` / `gemini-embedding-001` | Model overrides when the Gemini path is active. |
| `VITE_API_BASE` (frontend build) | `http://localhost:8000` | API origin baked into the bundle at build time. |

See [`.env.example`](.env.example) for a copyable template.

## API summary

Base path `/api`, JSON responses, Bearer JWT auth unless noted (HS256, 7-day expiry; passwords hashed with PBKDF2-HMAC-SHA256, 200k iterations, random salt).

- **Auth:** `POST /api/auth/register` · `POST /api/auth/login` · `GET /api/auth/me`
- **Profile & consents:** `GET|PUT /api/profile` · `GET|POST /api/consents`
- **Documents:** `POST /api/documents` · `POST /api/documents/image` · `GET /api/documents` · `GET /api/documents/{id}` · `GET /api/documents/{id}/file` · `DELETE /api/documents/{id}`
- **Adaptation & recommendation:** `POST /api/documents/{id}/adapt` · `GET /api/documents/{id}/adaptations` · `GET /api/documents/{id}/recommend`
- **Adaptive Reader:** `GET /api/documents/{id}/reader` · `POST /api/documents/explain` · `POST /api/documents/{id}/quiz`
- **Tutor:** `POST /api/documents/{id}/ask`
- **Viva Coach:** `POST /api/documents/{id}/viva/start` · `POST /api/viva/{session_id}/answer` · `GET /api/viva/{session_id}` · `GET /api/viva/{session_id}/question-audio`
- **Tasks (EF Coach):** `POST /api/tasks` · `GET /api/tasks` · `POST /api/tasks/{task_id}/sprints/{sprint_id}/toggle` · `DELETE /api/tasks/{task_id}`
- **Wellbeing:** `POST /api/checkins` · `GET /api/checkins` · `POST /api/wellbeing/plan` · `POST /api/communication`
- **Voice:** `POST /api/stt` (webm/wav/mp3 ≤ 15 MB; no key ⇒ `{"text":"","engine":""}`) · `POST /api/voice/synthesize`
- **Audio & media:** `GET /api/audio/{filename}` · `POST /api/media/token` · `GET /api/media/{token}` (60-second signed links)
- **Personalization engine:** `GET|PUT /api/preferences` · `POST /api/interactions` · `GET /api/interactions/recent` · `GET /api/preferences/memory`
- **Privacy & data rights:** `GET /api/me/export` · `DELETE /api/me` (full cascade) · `DELETE /api/interactions` · `GET /api/analytics`
- **Compatibility aliases:** `POST /api/adaptive/explain|simplify|analogy` · `POST /api/feedback` · `GET|PATCH /api/learner/profile`

## Verification

Current verified state (offline machine, no `GEMINI_API_KEY`):

- Backend tests: **183 passed** — hermetic temp DB/uploads per test; hostile-key permutations exercised; camera-FER route absence asserted against OpenAPI.
- Frontend: `tsc` strict production build green; **vitest 11/11** utility-level tests pass (no component/browser E2E suite exists yet).
- Accessibility: static WCAG audit — all text color pairs ≥ 4.5:1 (measured range 5.09–5.72:1) after palette remediation. Keyboard-only, screen-reader (NVDA) and 400%-reflow human passes are **still pending**.
- Docker artifacts validated statically only (YAML parse, COPY/nginx path existence) on a machine without Docker — image builds and container smoke have **not** been executed.

Reproduce:

```bash
backend\.venv\Scripts\python -m pytest backend/tests -q          # expect 183 passed
cd frontend && npm run build                                      # tsc strict + vite build
cd frontend && npm run test                                       # vitest, expect 11 passed
backend\.venv\Scripts\python backend\scripts\wcag_audit.py       # regenerates docs/accessibility/wcag-audit-machine-run.md
```

Live-server smoke harnesses exist at `backend/scripts/e2e_smoke*.py` for a running API + UI stack.

## Documentation

| Document | Purpose |
|---|---|
| [Design specification](docs/superpowers/specs/2026-08-21-sahaik-design.md) | Source of truth: research, architecture, ethics stance, delivery plan |
| [Release status](docs/release-status.md) | Feature-freeze declaration and repair-phase verification record |
| [Architecture diagram](docs/architecture-diagram.md) | Actual system topology with implementation status |
| [Deployment guide](docs/deployment-guide.md) | Local development, environment checklist, Docker Compose with honest verification status |
| [Demo video script](docs/demo-video-script.md) | 3-minute scripted walkthrough aligned to the real UI |
| [User testing report](docs/user-testing/user-testing-report.md) | Co-design methodology + findings (human sessions pending) |

## License

MIT License — see [LICENSE](LICENSE). Copyright remains with the NEUROLEARN team, USAR GGSIPU, SIH 2026.
