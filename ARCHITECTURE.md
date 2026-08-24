# ARCHITECTURE — NEUROLEARN

```
                    ┌──────────────────────┐
                    │       Student        │
                    └──────────┬───────────┘
                               ▼
              React + TS (Vite) — "warm study desk" UI
     Landing · Onboarding · Dashboard · Adaptive Reader · Focus
     SprintBoard · VivaStudio · Wellbeing · Personalization · Communicate
                               │  fetch + Bearer JWT
                               ▼
                     FastAPI (/api routers)
   ┌────────────┬────────────┬───┴────────┬─────────────┬────────────┐
   ▼            ▼            ▼            ▼             ▼            ▼
 Auth/Profile  Documents   Adaptive      Tutor/RAG    Wellbeing   Communication
 Consents      extraction  Engine        chunking     checkins    templates
 Emotion       adaptation  preferences   retrieval    plan        viva coach
 STT           reader      interactions  LLM ladder               sprints
               quiz
   └────────────┴────────────┴──────┬──────┴─────────────┴────────────┘
                                    ▼
                SQLite (dev) / PostgreSQL (prod) via SQLAlchemy
        users · profiles · consents · documents(+files) · chunks
        tasks/sprints · viva sessions/turns · checkins · interaction_events
        preference_scores · adaptations
                                    ▼
                 uploads/docs · uploads/audio (TTS mp3)
```

## The adaptive loop (core innovation)

```
USER ACTION (feedback button, level change, quiz answer, audio, map…)
   → POST /api/interactions {event}
   → services/preferences.apply_signal: new = clamp(0.7*old + 0.3*target)
   → preference_scores row updated (+ explanation string generated)
   → GET /documents/{id}/reader → presentation_hints(scores)
   → NEXT CARD renders with new start_level / example-first / quiz cadence
   → "Why am I seeing this?" panel lists the exact reasons
```

Scores are labelled **learning-preference confidence**, never diagnoses.
Users can drag every score manually in the Personalization Center; manual
values then feed the same loop.

## Explanation ladder

`POST /api/documents/explain` maps one card to levels 1–5 deterministically:
L1 one sentence → L2 clause-reduced simple → L3 analogy scaffold →
L4 full text → L5 detail + math relations. Engine label: `heuristic-ladder`.

## RAG pipeline

upload → `extraction.py` (pptx/pdf/docx/txt) → `chunking.py` (~120w, 20 overlap)
→ embeddings when keyed (`retrieval.embed_texts`, stored on DocumentChunk.embedding)
→ `search_with_embeddings` cosine, else TF-IDF cosine fallback
→ grounded prompt or extractive fallback → cited answer.

## AI provider isolation

All vendor calls live in `services/llm_client.py` (LangChain Gemini) +
`api/stt.py` + `retrieval.py` embedding helpers. Swapping vendors means
editing one module; every call has a deterministic fallback and honest
labelling (`used_llm`, `engine="template"` / `"heuristic-ladder"`).

## Local ML models (no key needed)

- Text emotion: multinomial NB trained on MELD → `data/emotion_nb.json`
- Face mood: diagonal GNB trained on FER2013 → `data/face_centroids.json`
Both retrainable via `backend/scripts/train_*.py`; both fail soft to None.

## Safety & privacy boundaries

No diagnosis language anywhere; wellbeing copy routes to human counselling;
crisis-safe suggestion for mood ≤ 2 is unconditional. Frames/audio for emotion
checks are processed in memory and never persisted. Documents are owner-scoped
on every route; original files deletable; preferences user-editable.
