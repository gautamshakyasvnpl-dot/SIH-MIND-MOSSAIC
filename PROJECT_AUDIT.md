# PROJECT_AUDIT — NEUROLEARN (SIH 2026, GGSIPU2605)

Audit date: 2026-08-24 (post-repair). Baseline repo codename "SahAIk"; product display name is
NEUROLEARN (`frontend/src/lib/brand.ts` + FastAPI title are the places it lives).
Feature freeze declared 2026-08-23 and in force — see `docs/release-status.md`.

## Current architecture

- **Backend** `backend/app` — FastAPI + SQLAlchemy (SQLite default, Postgres via
  `DATABASE_URL`). Routers under `/api`: auth, profile, consents (ENFORCED:
  voice→stt, telemetry→interaction logging, memory→learning memory; default false,
  calm 403s), documents (+ `/file` [media-token], `/adapt`, `/recommend`, `/ask`,
  `/reader`, `/quiz`, `/viva`), audio, tutor, tasks, viva (exactly-five invariant),
  checkins (strict mood 1..5), stt (webm/wav/mp3 only; no-key → `{"text":"","engine":""}`),
  media tokens (60 s stateless HMAC-signed capability URLs — NO JWT in any query string),
  preferences/interactions, communication, me/export (Bearer-only, all owned categories),
  me/delete (full cascade, tested). Face-emotion router UNMOUNTED (404 + openapi-absence
  tested); text-emotion retained. Services are pure functions; LLM calls isolated in
  `services/ai_provider.py` + `llm_client.py` with graceful degradation everywhere.
- **Adaptive engine** `services/preferences.py` + `interaction_events` /
  `preference_scores` tables. Transparent update rule
  `new = 0.7*old + 0.3*signal`, clamped to [0.02, 0.98]; every change returns
  an explanation string. Telemetry consent required before signals are recorded.
- **Frontend** React 19 + TS + Vite. SensorySettingsProvider mounted at root;
  RequireAuth verifies JWTs via `/api/auth/me` with central 401 handling;
  route-level error boundaries; per-route titles + heading focus.
  Design system in `styles/tokens.css` ("warm study desk", marigold remediated to
  ≥4.5:1 text contrast) with sensory overrides via data-attributes, persisted in
  localStorage `sahaik_sensory` and synced from the server LearnerProfile.
  Consent panel (voice/telemetry/memory, default-off, equal weight) in onboarding +
  Preferences. Camera-FER absent from the UI entirely.
- **AI** Gemini via ai_provider chain when keys present (simplify, pace, grounded
  answers, embeddings); everything degrades deterministically with honest
  `engine=` / `used_llm=false`. Prompt-injection fencing (`services/guard.py`) wraps
  document chunks, learner questions, and sprint titles/notes in every LLM prompt.
  Local models: text-emotion NB (MELD-trained); face-mood code unmounted research.

## Verified state (2026-08-24)

- pytest **183 passed** offline (hermetic tmp DB/uploads; order-permutation and
  hostile-GEMINI-key runs green; zero new stray DB files)
- `npm run build` clean (tsc strict + vite); vitest **11/11** (utility-level)
- `pip check`: no broken requirements
- Static WCAG audit: all routed pages/components clean after marigold remediation
  (re-runnable: `backend/scripts/wcag_audit.py` → `docs/accessibility/wcag-audit-machine-run.md`)
- Docker compose/Dockerfiles statically validated ONLY (YAML parse, COPY/nginx paths,
  volume↔UPLOAD_DIR alignment). Docker not installed on this machine — image builds
  and container smoke NOT executed.

## Repair-phase contract fixes now in place

Profile null-rejection + enum validation · case-insensitive email uniqueness ·
register-only password minimum (legacy logins preserved) · strict-bool consents with
merge-not-reset semantics · viva exactly-five turns, done-timing, post-done rejection,
pathological-doc fast-fail · mood strict 1..5 (no clamping) · recommender
audio-affinity priority with field-citing reasons · STT extension allowlist ·
corrupt PPTX/PDF/DOCX → 400 · UPLOAD_DIR centralization end-to-end · cascade delete
of chunks/adaptations/viva/media on document delete · bounded-TTS false-timeout repair ·
chunker word-boundary splitting for punctuation-free/oversized input · grounded-miss
tutor fallback · sprint LLM-output validation (gentle=15 / standard=25) ·
unknown-format error entries (supported formats byte-identical).

## Missing modules / technical debt

| Item | Status | Notes |
|---|---|---|
| pgvector | deferred | JSON embedding column + cosine now; swap-in point is `retrieval.py` |
| Alembic migrations | none | `create_all` on boot suffices for demo; add before prod |
| Whisper STT | not used | Web Speech API + Gemini inline audio instead |
| Rate limiting | done | stdlib sliding-window (`core/ratelimit.py`) |
| Prompt-injection hardening | done | `guard.py` neutralisation + `<<<DATA>>>` fencing on all doc/user-data prompts incl. sprints |
| AI provider abstraction | done | OpenAI-compatible > Gemini > Null (`ai_provider.py`) |
| Privacy controls | done | export (all categories, Bearer-only), DELETE /api/me full cascade, media tokens replace JWT-in-query |
| Browser E2E | pending | requires Playwright install (package.json frozen) or human run-through |
| Human accessibility passes | pending | keyboard golden path, NVDA, zoom/reflow, OS high-contrast — see docs/accessibility checklist |
| User testing / SUS | pending | instruments ready; sessions not yet run |
| Demo video, pitch deck | pending | script aligned to real UI; recording gated on final checks |

## Security notes

PBKDF2-SHA256 (200k) hashing; HS256 JWTs; ownership checks on document/viva/task
routes; file-type+size validation; secrets server-side only; `.env.example` documents
every variable; short-lived signed media capabilities; account deletion cascade tested.

## Accessibility notes

Semantic HTML, labelled controls, visible focus rings, skip link, reduced-motion
honoured globally, dyslexia-friendly font mode, wide spacing mode, keyboard shortcuts,
dictation (Web Speech) with calm consent-gating, read-aloud, text contrast ≥4.5:1
(marigold 5.09–5.72:1 after remediation). Human screen-reader/reflow passes pending.
