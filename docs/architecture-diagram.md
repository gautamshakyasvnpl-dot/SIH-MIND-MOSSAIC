# NEUROLEARN (repo codename SahAIk) — Architecture

Status legend: **✅ shipped** = implemented and exercised by the offline test suite. **Research code** = present in the repo but NOT mounted in the running app. **Deferred** = specified as future work, not part of the release.

Source of truth: [`superpowers/specs/2026-08-21-sahaik-design.md`](superpowers/specs/2026-08-21-sahaik-design.md) §3; runtime truth: `backend/app/main.py` router registrations.

## 1. System context — actual topology

```mermaid
flowchart TB
    learner["Neurodivergent learner<br/>browser client"]

    subgraph fe["React 18 SPA (Vite, TS strict)"]
        routes["Routes: /landing /login /register /onboarding<br/>/dashboard /library /document/:id (+ /reader /viva)<br/>/tasks /wellbeing /preferences /communicate /focus/:id?"]
        sensory["Sensory settings + consent panel<br/>data-attributes on documentElement"]
    end

    subgraph be["FastAPI backend - routers under /api"]
        api["auth · profile · consents · documents<br/>reader · tutor · viva · tasks · checkins<br/>stt · audio · media · preferences<br/>privacy · communication · aliases"]
        sec["core/security JWT+PBKDF2<br/>core/ratelimit sliding window<br/>core/consent enforcement"]
    end

    subgraph svc["Services - pure functions"]
        extraction["extraction<br/>pptx/pdf/docx/txt"]
        tts["tts (gTTS→MP3)"]
        chunking["chunking ~120w / 20w overlap"]
        retrieval["retrieval TF-IDF cosine<br/><b>pgvector swap-in point</b>"]
        tutor["tutor grounded answers"]
        guard["guard prompt-injection fence"]
        prefs["preferences adaptive scores"]
        rec["recommender format + reason"]
        well["wellbeing mood suggestions"]
        media["media tokens 60s HMAC"]
        adapter["adapter simplify + explain"]
    end

    subgraph prov["AI provider chain (ai_provider.py)"]
        openai["OpenAI-compatible endpoint<br/>LLM_API_KEY / LLM_BASE_URL"]
        gemini["Gemini via LangChain<br/>GEMINI_API_KEY"]
        nullp["Null provider<br/>heuristic fallbacks, used_llm:false"]
    end

    subgraph data["Data layer"]
        db[("SQLAlchemy DB<br/>SQLite default, Postgres via DATABASE_URL")]
        uploads[("UPLOAD_DIR volume<br/>docs/ + audio/")]
    end

    research["services/emotion (text) + services/vision (face)<br/>api/emotion router UNMOUNTED - research code"]

    learner -->|"HTTPS"| fe
    fe -->|"REST JSON, Bearer JWT<br/>media via 60s signed tokens"| api
    api --> sec
    api --> svc
    svc --> prov
    openai -.->|"absent"| gemini -.->|"absent"| nullp
    svc --> db
    svc --> uploads
    research -.->|"not registered in main.py"| be
```

Notes:

- The frontend calls the API at `import.meta.env.VITE_API_BASE || "http://localhost:8000"`; the JWT is stored in `localStorage["sahaik_token"]`. No JWT is ever placed in a URL: document/viva-question downloads require a short-lived (60-second) stateless HMAC token from `POST /api/media/token`, and the privacy export requires the Bearer header.
- Graceful degradation is a hard rule: with no API key configured every LLM-assisted feature falls back to deterministic logic and reports `"used_llm": false` (or an honest empty payload for STT). The provider chain tries OpenAI-compatible → Gemini → Null.
- Camera-based facial-emotion recognition is excluded from the product (spec §2.4): the `/emotion/face` route exists only as unmounted research code and its absence from OpenAPI is covered by a test.

## 2. Request flow through the service layer

There is no cross-agent orchestrator in the shipped product (explicitly out of scope at feature freeze); each route calls its services directly. LangGraph wrappers exist for profiler/tutor/ef-coach/viva-coach in `app/agents/`, kept thin over the pure service functions.

```mermaid
flowchart LR
    route["FastAPI route handler<br/>owner check + rate limit + consent gate"]

    route --> adapt["adapt_document(text, profile)"]
    adapt --> guard2["guard.fence() before any LLM prompt"]
    guard2 --> llm{"API key set?"}
    llm -->|yes| provider["ai_provider chain"]
    llm -->|no| heur["deterministic fallback"]
    adapt --> tts2["tts.synthesize_speech → MP3"]

    route --> ask["ask: ensure chunks → retrieval.search (TF-IDF) → tutor.answer_question<br/>answer restricted to retrieved chunks + sources[]"]
    route --> viva["viva: exactly 5 questions → evaluate_answer 0–2 → done after 5th"]
    route --> sprints["break_into_sprints(title, notes, pace) 15-min gentle / 25-min standard"]
    route --> checkin["suggest_for_mood(mood) box breathing ≤2 / break nudge 3 / praise ≥4"]
    route --> recommend["recommender: format + reason citing profile fields"]
    route --> readerflow["reader hints + quiz + memory<br/>(0.7·old + 0.3·signal, clamped [0.02,0.98])"]
```

Every LLM-assisted response carries a human-readable `explanation` and the honest `used_llm` flag; consent-denied features return calm HTTP 403s.

## 3. Component status table

| Component | Role | Status |
|---|---|---|
| React SPA (14 routed pages incl. Adaptive Reader, SprintBoard, VivaStudio, Wellbeing, Preferences, Communicate, FocusMode) | User-facing flows | ✅ shipped |
| Sensory settings + granular consent panel (voice/telemetry/memory, default off) | Accessibility & privacy | ✅ shipped |
| FastAPI REST API (`/api`) | All flows | ✅ shipped |
| JWT auth (HS256, 7-day) + PBKDF2 password hashing + IP/user rate limiting | Security | ✅ shipped |
| Consent enforcement server-side (403s) | Privacy | ✅ shipped |
| Extraction service (.pptx/.pdf/.docx/.txt) | Text extraction | ✅ shipped |
| TTS service (gTTS → MP3) | Audio output | ✅ shipped |
| Adapter (LLM simplify + heuristic fallback, explanations) | Content adaptation | ✅ shipped |
| Chunking (~120 words, 20-word overlap) + TF-IDF retrieval | Tutor grounding | ✅ shipped (`retrieval.py` = pgvector swap-in point) |
| Prompt-injection guard (pattern neutralisation + `<<<DATA>>>` fencing) | LLM safety | ✅ shipped |
| Tutor grounded Q&A with cited sources | RAG | ✅ shipped |
| EF Coach sprints | Executive function | ✅ shipped |
| Viva Coach text mode (exactly 5 questions) | Practice | ✅ shipped |
| Wellbeing check-ins + crisis-safe suggestions | Emotional wellbeing | ✅ shipped |
| Recommender (format + reason citing profile fields) | Modality ranking | ✅ shipped |
| Adaptive preference engine (transparent score rule, memory, analytics) | Personalization | ✅ shipped |
| Privacy suite (export, history wipe, DELETE /api/me cascade) | Data rights | ✅ shipped |
| Media tokens (60-second HMAC-signed URLs) | Secure downloads | ✅ shipped |
| OCR page-image upload (Gemini vision) | Inclusive input | ✅ shipped (honest 400 without key) |
| PostgreSQL + pgvector | Production data layer, embeddings | Deferred |
| Whisper LoRA fine-tune on TORGO | Atypical-speech-tolerant STT | Deferred |
| Orchestrator Coach (hub-and-spoke routing) | Cross-agent coordination | Deferred (out of freeze scope) |
| Text-emotion NB model (`services/emotion.py`) | Tone analysis of self-reported notes | ✅ shipped |
| Face-mood GNB model + `/emotion` router (`services/vision.py`) | Camera FER | Research code — **unmounted**, excluded by design (spec §2.4) |

## 4. Privacy and consent architecture

- Granular consent toggles per feature: `voice`, `telemetry`, `memory` (`GET/POST /api/consents`), all defaulting to **false**; enforcement lives server-side (`core/consent.py`) — voice gates STT/dictation surfaces, telemetry gates interaction logging, memory gates struggled-concept history.
- Plain-language AI disclosure on every agent surface.
- Explainability: every adaptation/recommendation/preference change returns a human-readable reason string shown in the UI.
- No camera-based facial-expression recognition anywhere in the running product (spec §2.4).
- Data rights implemented and tested: `GET /api/me/export` (full dump, Bearer-header download), `DELETE /api/interactions`, `DELETE /api/me` full cascade; media links expire after 60 seconds and carry signatures, not credentials.
