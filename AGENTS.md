# AGENTS.md — SahAIk Project Guide (READ FIRST)

**Project:** SahAIk — AI-Powered Inclusive Learning & Wellbeing Platform for Neurodivergent Learners (SIH 2026, GGSIPU2605)
**Spec:** `docs/superpowers/specs/2026-08-21-sahaik-design.md`
**Current phase:** WEEK 1 vertical slice — auth → profiler onboarding → upload PPTX/PDF/DOCX → simplified text + TTS output.

## Golden rules

1. **Ownership map below is law.** Only edit files you own. Never edit `package.json`, `requirements.txt`, or another member's directory. If you need a change outside your ownership, note it in your final report instead.
2. **No code comments** unless explaining a non-obvious invariant. Type hints mandatory (Python), strict TypeScript.
3. **Graceful degradation:** every LLM feature MUST work with no `GEMINI_API_KEY` set — fall back to deterministic logic and set `"used_llm": false`. Never crash because an external API is missing.
4. **Accessibility is not optional:** semantic HTML, labeled controls, keyboard operability, visible focus, contrast ≥ 4.5:1, respect reduced-motion.
5. Run the verification commands for your area before reporting done.

## Commands

Backend (venv already created at `backend/.venv`):
```
backend\.venv\Scripts\python -m pip install -r backend\requirements.txt   # already done
backend\.venv\Scripts\python -m pytest backend/tests -q                   # tests
backend\.venv\Scripts\python -m uvicorn app.main:app --reload --app-dir backend  # run API :8000
```

Frontend (node_modules already installed):
```
cd frontend; npm run dev     # :5173
cd frontend; npm run build   # type-check + production build
```

Env vars (optional): `GEMINI_API_KEY`, `DATABASE_URL` (default `sqlite:///./sahaik.db`), `JWT_SECRET`.

## Week-1 API contract (v1) — implement EXACTLY

Base path `/api`. JSON responses. Errors: `{"detail": "..."}` with proper status codes.

### Auth
- `POST /api/auth/register` `{email, password, display_name}` → `{token, user}` where user = `{id, email, display_name}`
- `POST /api/auth/login` `{email, password}` → `{token, user}`
- `GET /api/auth/me` (Bearer token) → `{id, email, display_name}`
JWT HS256 via python-jose, 7-day expiry. Passwords hashed with stdlib `hashlib.pbkdf2_hmac` (sha256, 200k iters, random salt, store `salt$hash`). Duplicate email → 409.

### Profile (LearnerProfile v1 schema — canonical)
```json
{
  "modality_affinity": "text | audio | visual",
  "chunk_size": "small | medium | large",
  "font_style": "default | dyslexia_friendly",
  "line_spacing": "normal | wide",
  "reduce_motion": false,
  "audio_autoplay": false,
  "pace": "gentle | standard",
  "noise_sensitive": false,
  "onboarding_complete": false
}
```
- `GET /api/profile` → profile (create defaults on first access)
- `PUT /api/profile` body = partial or full profile → merged stored profile

### Consents
- `GET /api/consents` → `{voice: bool, telemetry: bool, memory: bool}`
- `POST /api/consents` same shape → stored (upsert)

### Documents
- `POST /api/documents` multipart `file` (.pptx/.pdf/.docx/.txt, ≤20 MB) → `{id, filename, doc_type, char_count, created_at}`
- `GET /api/documents` → `{items: [doc...]}`
- `GET /api/documents/{id}` → doc; 404 if not owner's
- `DELETE /api/documents/{id}` → 204

### Adaptations
- `POST /api/documents/{id}/adapt` `{"formats": ["simplified_text", "tts_audio"]}` → 
```json
{"document_id": "...", "used_llm": true,
 "results": [
   {"format": "simplified_text", "status": "ok", "content": "...", "explanation": "why this rendering"},
   {"format": "tts_audio", "status": "ok", "content": "/api/audio/<filename>.mp3", "explanation": "..."}
 ]}
```
- `GET /api/audio/{filename}` serves mp3 from `backend/uploads/audio/`
- `GET /api/documents/{id}/adaptations` → latest adaptation result

## Service contracts (exact signatures)

`backend/app/services/extraction.py` (ML lead):
```python
def extract_text(filename: str, data: bytes) -> str:
    """Dispatch by extension: .pptx .pdf .docx .txt. Raise ValueError on unsupported/empty."""
def doc_type(filename: str) -> str: ...
```

`backend/app/services/tts.py` (ML lead):
```python
def synthesize_speech(text: str, out_path: Path) -> Path:
    """Write MP3 to out_path (gTTS). Raise RuntimeError on failure."""
```

`backend/app/services/adapter.py` (AI-Agents lead):
```python
def adapt_document(text: str, profile: dict) -> dict:
    """Returns {"results": [...], "used_llm": bool} per the adaptation response contract.
    simplified_text: LLM simplify respecting chunk_size/pace; fallback = heuristic
    sentence-split + first-N-chunks join. tts_audio always produced locally."""
class ProfilerState(TypedDict): ...  # LangGraph state in agents/profiler.py
def build_profiler_graph(): ...      # StateGraph: answers -> LearnerProfile merge suggestion
```

Routes may import ONLY these functions from services. Backend lead wires thin handlers.

## Ownership map (Week 1)

| Member | Owns |
|---|---|
| frontend-lead | `frontend/src/**` EXCEPT files owned by ux-lead; pages/routes/components/wiring |
| ux-lead | `frontend/src/styles/**`, `frontend/src/context/SensorySettings.tsx`, `docs/accessibility/**`, consent+SUS templates in `docs/user-testing/**` |
| backend-lead | `backend/app/main.py`, `backend/app/core/**`, `backend/app/db.py`, `backend/app/models.py`, `backend/app/api/**`, `backend/app/schemas.py` |
| ai-agents-lead | `backend/app/services/{adapter,llm_client}.py`, `backend/app/agents/**` |
| ml-lead | `backend/app/services/{extraction,tts}.py`, `backend/tests/**`, `backend/tests/fixtures/**` |
| docs-lead | `README.md`, `docs/architecture-diagram.md`, `docs/deployment-guide.md`, `docs/demo-video-script.md`, `docs/user-testing/user-testing-report.md` |

Shared (created by orchestrator, do not modify): `AGENTS.md`, `agents/*.md`, `backend/requirements.txt`, `frontend/package.json`, vite/tsconfig, `.gitignore`, spec docs.

## Frontend internal contracts

Fetch wrapper: JWT from `localStorage["sahaik_token"]`; base URL `import.meta.env.VITE_API_BASE || "http://localhost:8000"`.

ux-lead exports (frontend-lead consumes):
```tsx
// frontend/src/context/SensorySettings.tsx
export function SensorySettingsProvider({children}: {children: ReactNode})
export function useSensorySettings(): {prefs: SensoryPrefs, update: (p: Partial<SensoryPrefs>) => void}
// SensoryPrefs mirrors display fields of LearnerProfile; persists to localStorage "sahaik_sensory";
// applies data attributes to document.documentElement: data-font="default|dyslexia_friendly",
// data-spacing="normal|wide", data-motion="normal|reduced"
```
`frontend/src/styles/tokens.css`: variables `--color-bg --color-surface --color-text --color-primary --color-accent --radius --space-unit --font-body --font-dyslexic`; `[data-font="dyslexia_friendly"]`, `[data-spacing="wide"]`, `[data-motion="reduced"]` override blocks; global focus-visible ring; `@media (prefers-reduced-motion)`.

## Definition of done (Week 1)

- `pytest backend/tests -q` green (auth/profile/documents/extraction/tts-mock/adapter-fallback)
- `npm run build` green in frontend
- Manual E2E: register → onboarding → upload sample.pptx → adapt → see simplified text + play audio
- Accessibility checklist (ux-lead) passes on all four pages

---

# WEEK 2 ADDENDUM — Tutor RAG · EF Coach · Viva Coach (text mode)

Retrieval is **dependency-free TF-IDF cosine over document chunks** this week (pgvector/Gemini embeddings deferred to Week 3). All three features MUST degrade gracefully with no `GEMINI_API_KEY`.

## New API endpoints (implement EXACTLY, under `/api`, Bearer auth unless noted)

### Tutor (RAG)
- `POST /api/documents/{id}/ask` `{"question": "..."}` →
```json
{"document_id":"...","answer":"...","used_llm":false,
 "sources":[{"chunk_index":0,"snippet":"first ~160 chars"}]}
```
Chunks ensured lazily on first ask (chunking service, ~120-word chunks, 20-word overlap). LLM path: answer ONLY from provided chunks, cite nothing outside them. Fallback: extractive — top 2 sentences of best chunk.

### Tasks (EF Coach)
- `POST /api/tasks` `{"title":"...", "due_date":"2026-09-01"|null, "notes":"..."|null}` →
```json
{"id":"...","title":"...","due_date":null,"notes":null,"status":"open","created_at":"...",
 "sprints":[{"id":"...","index":0,"description":"...","minutes":25,"done":false}]}
```
Sprints: LLM breakdown respecting profile pace (gentle→15-min sprints) when available; deterministic fallback = 3–5 generic sprints (understand → draft → review → finalize) scaled to notes length.
- `GET /api/tasks` → `{"items":[task...]}` newest first
- `POST /api/tasks/{task_id}/sprints/{sprint_id}/toggle` → updated task (flips sprint.done; task status becomes "done" when all sprints done, else "open")
- `DELETE /api/tasks/{task_id}` → 204

### Viva Coach (text mode)
- `POST /api/documents/{id}/viva/start` → `{"session_id":"...","document_id":"...","question":"...","turn_count":1}`
- `POST /api/viva/{session_id}/answer` `{"answer":"..."}` →
```json
{"feedback":"...","score":1,"next_question":"..."|null,"done":false,"turn_count":2}
```
Sessions have exactly 5 questions. Score 0–2 (token-overlap heuristic fallback; LLM rubric when available). `done:true` + `next_question:null` after 5th answer.
- `GET /api/viva/{session_id}` → `{"session_id","document_id","done","turns":[{"index","question","answer","feedback","score"}]}`

## New service contracts (exact signatures)

`backend/app/services/chunking.py` (ml-lead):
```python
def chunk_text(text: str, target_words: int = 120, overlap_words: int = 20) -> list[str]: ...
```

`backend/app/services/retrieval.py` (ml-lead):
```python
def search(chunks: list[str], query: str, top_k: int = 2) -> list[int]:
    """Pure-python TF-IDF cosine indices, best first."""
```

`backend/app/services/tutor.py` (ai-agents-lead):
```python
def answer_question(chunks: list[str], question: str) -> dict:
    """{"answer","used_llm"} — LLM grounded answer or extractive fallback."""
def make_viva_question(chunks: list[str], asked: list[str]) -> str | None: ...
def evaluate_answer(question: str, reference_chunk: str, answer: str) -> dict:
    """{"feedback","score"} 0..2."""
def break_into_sprints(title: str, notes: str | None, pace: str) -> list[dict]:
    """[{description, minutes}] LLM or deterministic fallback."""
```
Routes import ONLY these + chunking/retrieval.

## Week-2 ownership deltas

| Member | Additional files |
|---|---|
| backend-lead | models: Task, Sprint, VivaSession, VivaTurn, DocumentChunk; routers: `tutor.py`, `tasks.py`, `viva.py`; schemas |
| ai-agents-lead | `services/tutor.py`, `agents/tutor.py`+`ef_coach.py`+`viva_coach.py` (thin LangGraph wrappers calling services; graph optional if stateless) |
| ml-lead | `services/chunking.py`, `services/retrieval.py`, tests: `test_chunking_retrieval.py`, `test_tutor_fallback.py`, extend api smoke (ask/task/viva round-trips) |
| frontend-lead | DocumentView: Ask panel; new pages `SprintBoard.tsx` (`/tasks`), `VivaStudio.tsx` (`/document/:id/viva`); nav links |
| docs-lead | README/architecture/deployment updated for new endpoints |

## Definition of done (Week 2)

- pytest green incl. new chunking/retrieval/tutor-fallback/api-smoke-v2 tests
- `npm run build` green
- E2E smoke v2: upload → ask (grounded answer + sources) → create task (sprints) → toggle sprint → viva start → answer ×5 → done
- **FEATURE FREEZE declared at end of Week 2**

---

# WEEK 3 ADDENDUM — Voice loop · Wellbeing · Recommender · A11y polish

(Freeze applies to Weeks 1-2 features; Week 3 adds the following only.)

## New API endpoints (implement EXACTLY, under `/api`, Bearer auth)

### Wellbeing check-ins
- `POST /api/checkins` `{"mood": 1..5, "note": "..."|null}` → `{"id","mood","note","suggestion","created_at"}`
- `GET /api/checkins` → `{"items":[...]}` newest first (cap 50)
Suggestion logic (deterministic, in `services/wellbeing.py`): mood ≤2 → grounding exercise text ("Try box breathing: in 4s, hold 4s, out 4s, hold 4s — four rounds.") + EOC/counselling escalation line; mood 3 → short break nudge; mood ≥4 → positive reinforcement. Crisis-safe copy only; no diagnosis language.

### Recommendation engine
- `GET /api/documents/{id}/recommend` → `{"format":"audio"|"simplified_text"|"original_text","reason":"..."}`
Rules (in `services/recommender.py`, pure function + thin route): profile modality_affinity audio→audio ("You told us you learn best by listening"); visual→simplified_text with concept-map note; text+chunk small→simplified_text; long doc (>4000 chars) & noise_sensitive false → prefer audio hint; always returns a reason string citing profile fields used.

### Speech-to-text (graceful)
- `POST /api/stt` multipart `file` (webm/wav/mp3 ≤15 MB) → `{"text": "...", "engine": "gemini"|""}`
Gemini inline-audio transcription when key set; without key → 200 `{"text":"","engine":""}` and frontend falls back to browser Web Speech API / typing. Never errors on missing key.

## New service contracts

```python
# services/wellbeing.py (backend-lead may inline; keep pure fn for tests)
def suggest_for_mood(mood: int) -> str: ...
```

## Ownership deltas
| Member | Files |
|---|---|
| backend-lead | Checkin model, `api/checkins.py`, `api/stt.py`, recommend route in documents router |
| ai-agents-lead | none required this week (recommender is rule-based) |
| ml-lead | tests: `test_wellbeing_recommend.py`, extend smoke v3 |
| frontend-lead | `/wellbeing` page, voice dictation hook (`useDictation` via Web Speech API), recommendation chip on DocumentView, nav links |

## Definition of done (Week 3)

- pytest green incl. wellbeing/recommend/stt-fallback tests
- `npm run build` green
- E2E smoke v3: check-in low mood → suggestion contains breathing + escalation; recommend endpoint returns format+reason; stt without key returns empty text engine ""
- datetime.utcnow deprecation cleaned; skip-to-content link present
