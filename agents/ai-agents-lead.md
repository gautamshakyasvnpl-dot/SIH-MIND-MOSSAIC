# Brief: ai-agents-lead

Read `AGENTS.md` first — it is law. Consult installed skill `.agents/skills/langgraph-docs/SKILL.md` for current LangGraph API usage (StateGraph, TypedDict state, nodes/edges).

## Mission (Week 1)
The intelligence layer: LLM client with graceful degradation + document adapter service + LangGraph profiler graph.

## Ownership
`backend/app/services/adapter.py`, `backend/app/services/llm_client.py`, `backend/app/agents/**` (+ `__init__.py` files).

## llm_client.py
- Wrap `langchain_google_genai.ChatGoogleGenerativeAI` (model "gemini-2.0-flash" or env override `GEMINI_MODEL`).
- `def is_llm_available() -> bool` — true only if `GEMINI_API_KEY` set.
- `def simplify_text(text: str, chunk_size: str, pace: str) -> str | None` — returns None on any failure (no key, exception, timeout). Prompt: simplify for a neurodivergent learner; respect chunk_size (small≈≤40 words/chunk, medium≈80, large≈150) and pace (gentle = shorter sentences, more connective explanations); preserve meaning, no added facts; output only the simplified text.

## adapter.py (exact signature in AGENTS.md)
```python
def adapt_document(text: str, profile: dict) -> dict
```
- simplified_text: try LLM path → {"format","status":"ok","content",...,"explanation"} mentioning profile settings; on None → deterministic fallback: sentence-split via regex, join into chunks per chunk_size word budget, take first 5 chunks, explanation states heuristic mode. Set top-level "used_llm".
- tts_audio: import `app.services.tts.synthesize_speech`; out to Path("uploads/audio")/{uuid}.mp3 relative-safe (create dirs); content = f"/api/audio/{filename}"; explanation notes local gTTS synthesis; status "ok"; on RuntimeError → status "error" with explanation (do NOT fail the whole request).
- Always return both requested formats; unknown format → status "error".

## agents/profiler.py
LangGraph StateGraph implementing the contract:
```python
class ProfilerState(TypedDict):
    answers: dict        # raw onboarding answers
    profile: dict        # current LearnerProfile
    suggestion: dict     # merged profile suggestion
```
Nodes: `infer` (map questionnaire answers → profile fields deterministically: e.g., prefers listening→audio modality; struggles reading long text→small chunks+dyslexia font; overwhelmed by motion→reduce_motion) then optional `refine` node that calls llm_client ONLY to adjust `pace`/explanations when available. Edges: START→infer→(refine|END). Export:
```python
def build_profiler_graph(): ...  # compiled graph, .invoke(state) -> state
def run_profiler(answers: dict, current: dict) -> dict:  # convenience returning merged suggestion
```
Deterministic mapping must be complete enough that tests pass without network.

## Self-check
`backend\.venv\Scripts\python -c "from app.agents.profiler import build_profiler_graph, run_profiler; from app.services.adapter import adapt_document; print(run_profiler({'likes_listening': True}, {}))"` from backend dir (services/tts may not exist yet at your time — code the import inside function or guarded so module import never fails without siblings).
