# NEUROLEARN — Release Status & Feature Freeze Declaration

**Product:** NEUROLEARN (repository codename: SahAIk)
**Problem statement:** SIH 2026 GGSIPU2605
**Freeze declared:** 2026-08-23

## Scope of freeze

As of **2026-08-23**, feature development is frozen for all Week 1–3 scope. Every behavior listed below is fixed for the SIH 2026 submission: no API contract changes, no schema changes, and no behavioral changes to these flows will be made after this date. Remaining effort goes exclusively to verification, human testing, documentation, and submission logistics.

## Frozen acceptance surface — required Week 1–3 flows

All endpoints are under `/api` and use Bearer-token authentication unless noted. All LLM-assisted features degrade gracefully when `GEMINI_API_KEY` is unset.

1. **Authentication** — register / login / me (`POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`) using JWT Bearer tokens; duplicate email registration returns HTTP 409.
2. **Profiler onboarding → LearnerProfile v1** — `GET /api/profile` creates defaults on first access; `PUT /api/profile` accepts partial or full profile and stores the merged profile.
3. **Granular consents** — `GET /api/consents` / `POST /api/consents` for `voice`, `telemetry`, and `memory`, each defaulting to `false`.
4. **Document upload and library CRUD** — `POST /api/documents` accepts `.pptx` / `.pdf` / `.docx` / `.txt` up to 20 MB; list (`GET /api/documents`), fetch single document, and delete (`DELETE /api/documents/{id}`, 204) complete the library flow.
5. **Adaptation** — `POST /api/documents/{id}/adapt` produces `simplified_text` and `tts_audio`, each result carrying a status, content, a plain-language `explanation` of why that rendering was chosen, and the response-level `used_llm` flag.
6. **Audio serving** — `GET /api/audio/{filename}` serves generated MP3 files from the server's audio upload directory.
7. **Tutor grounded Q&A** — `POST /api/documents/{id}/ask` answers strictly from the document's chunks retrieved via dependency-free TF-IDF cosine similarity (~120-word chunks, 20-word overlap); responses include `sources` with chunk index and snippet; without an LLM key the answer is extractive from the best-matching chunk.
8. **EF Coach tasks → sprints** — `POST /api/tasks` breaks a task into sprints sized by profile pace (15-minute sprints on `gentle`, 25-minute on `standard`); sprint toggle via `POST /api/tasks/{task_id}/sprints/{sprint_id}/toggle` flips completion and drives task status (`done` when all sprints done); `DELETE /api/tasks/{task_id}` removes a task.
9. **Viva Coach text mode** — sessions contain exactly 5 questions (`POST /api/documents/{id}/viva/start`, then `POST /api/viva/{session_id}/answer`); each turn receives feedback and a 0–2 score; full transcript is available via `GET /api/viva/{session_id}`; the session reports `done: true` with `next_question: null` after the fifth answer.
10. **Wellbeing check-ins** — `POST /api/checkins` records mood 1..5 and returns a deterministic, crisis-safe suggestion; mood ≤ 2 returns the grounding exercise ("Try box breathing: in 4s, hold 4s, out 4s, hold 4s — four rounds.") plus an EOC/counselling escalation line; history via `GET /api/checkins` is newest-first capped at 50 entries.
11. **Modality recommendation engine** — `GET /api/documents/{id}/recommend` returns a `format` (`audio` | `simplified_text` | `original_text`) plus a `reason` string that explicitly cites which profile fields produced the recommendation.
12. **Speech-to-text graceful degradation** — `POST /api/stt` transcribes webm/wav/mp3 up to 15 MB when a Gemini key is configured; without a key it returns HTTP 200 `{"text":"","engine":""}` and never errors — typing remains always available in the UI.
13. **Accessibility sensory settings** — dyslexia-friendly font, wide line spacing, and reduced-motion preferences persist across sessions and are applied live to the document root as data attributes driving CSS token overrides.

## Explicitly out of scope — excluded from this release

The following items are frozen OUT and are not part of the submitted product:

- pgvector / embedding-model swap-in (TF-IDF retrieval remains the shipped implementation)
- Whisper LoRA fine-tuning
- A new agent orchestrator beyond the current service contracts
- Group-project boards
- Camera-based facial-emotion recognition — excluded from the release product on ethics grounds per approved spec §2.4
- Any additional ML features

## Verification status at freeze

> Historical record of the state at freeze date; superseded by the repair-phase results below.

- Automated backend test suite green: **115 passed** with no `GEMINI_API_KEY` set (all graceful-degradation paths exercised).
- Frontend production build green (`npm run build`) as of the audit.

## Open items (human work, not code)

These remain open and are tracked separately; none require further code changes to the frozen surface:

- Browser end-to-end manual smoke passes
- Human accessibility audit passes
- Real user-testing sessions
- Demo video recording
- Pitch deck finalization

## Repair phase completed — 2026-08-24

The freeze declaration above remains fully in force. The repair phase changed no contracts; it fixed defects against them and hardened verification. State now verified:

**Automated verification**

- Backend: **pytest 183 passed, offline** (no `GEMINI_API_KEY` set), with hermetic per-test temporary databases and upload directories; hostile-key permutations exercised; all graceful-degradation paths covered.
- Frontend: strict TypeScript production build green (`npm run build`); vitest utility suite **11/11 passing**. Component-level and browser E2E automation is still not present.
- Docker artifacts validated **statically only** (YAML parse, COPY/nginx path existence) on a machine without Docker — image builds, `compose up`, and container smoke have not been executed.
- Accessibility: static contrast audit passes on every text pair after the marigold palette remediation (measured range 5.09–5.72:1, requirement ≥ 4.5:1); re-runnable via `backend/scripts/wcag_audit.py` → `docs/accessibility/wcag-audit-machine-run.md`. Keyboard-only, NVDA screen-reader, and 400%-reflow human passes remain pending.

**Contract fixes now in place**

- Consent enforcement is live server-side with calm HTTP 403s: `voice` gates STT/dictation surfaces, `telemetry` gates interaction logging, `memory` gates the learning-memory surface. All three default to false.
- Camera-based facial-emotion recognition is absent from the release UI **and** the backend router is unmounted (requests 404; absence asserted against the OpenAPI schema in tests). Text-emotion analysis of self-reported notes remains.
- Viva sessions guarantee exactly five questions: completion (`done: true`, `next_question: null`) occurs only after the fifth answer, and answers after a done session are rejected.
- The recommender returns audio for audio-affinity profiles with a reason string citing the profile fields used.
- STT accepts webm/wav/mp3 up to 15 MB; without a configured key it returns HTTP 200 `{"text":"","engine":""}` rather than erroring.
- Media downloads use short-lived (60-second) stateless HMAC-signed tokens; no JWT appears in any URL. The data export downloads only with a Bearer header. `DELETE /api/me` performs a full cascade delete (profile, consents, documents and extracted text, adaptations, audio, tasks/sprints, viva sessions, check-ins, interactions) and is covered by tests.
- File storage is centralized on `UPLOAD_DIR` (default `uploads`; the compose file mounts the named volume at `/data` with `UPLOAD_DIR=/data/uploads`).

## Release-completion verification round " 2026-08-24 (post-freeze, no contract changes)

Full baseline re-run and a live isolated end-to-end journey were executed after the onboarding legend layout fix (`3a4949c`). Results:

**Automated baseline (all green)**

- `pip check` clean.
- `pytest backend/tests -q`: **183 passed** (offline, no `GEMINI_API_KEY`).
- `npm run test`: **11 passed**. `npm run build`: strict production build green.
- `backend/scripts/wcag_audit.py`: all audited routes **PASS**.

**Live isolated API journey (temporary DB + uploads, port-isolated server, 24/24 checks pass)**

Register " onboarding profile PUT " consents default off (voice/telemetry/memory) " preferences persist across requests " TXT upload " corrupt `.docx` / unsupported `.exe` / >20 MB file each rejected calmly (4xx) " simplified text with `used_llm: false` + explanation " **TTS with real network gTTS: MP3 generated and served with `audio/*` content type** (first live network TTS validation; offline graceful path still covered by tests) " grounded ask with in-document source snippets " gentle-pace task creates only 15-minute sprints " toggling every sprint flips task to done " viva start " exactly five answers " `done:true` + `next_question:null` " sixth answer rejected " transcript shows five scored turns " mood-1 check-in returns box-breathing + escalation copy without diagnostic language " audio-affinity recommendation cites profile fields " STT with voice consent granted and no key returns HTTP 200 `{"text":"","engine":""}` " voice consent off returns calm 403 gate (consent enforcement observed live) " media token `{kind:"document_file", id}` serves the MP3 while a forged token is rejected (404, non-enumerating) " `/api/me/export` contains identity + profile " `DELETE /api/interactions` clears history " `DELETE /api/me` cascades and the old token is unauthorized afterwards (401). Test user/documents/media existed only in an isolated temp store, removed afterwards.

**Documentation truth sweep**

- `docs/architecture-diagram.md`: React 19 claim corrected to React 18 (matches frozen manifest 18.3.1).
- `docs/pitch-deck-outline.md`: headline corrected to "**183 tests. 53 endpoints**" (was "53 tests. 25 endpoints"; 53 is the actual count of route operations); unfulfilled co-design claim replaced with honest accessibility/user-testing status.
- `README.md`: license section now points to the complete MIT `LICENSE` instead of calling it pending.

Still pending (human or external, unchanged): browser E2E automation, keyboard/NVDA/reflow/high-contrast human passes, real EOC user-testing sessions + SUS, Docker engine validation, public deployment URL, demo video recording, final pitch deck build, polished architecture export.
