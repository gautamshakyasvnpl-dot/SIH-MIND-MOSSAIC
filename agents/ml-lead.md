# Brief: ml-lead

Read `AGENTS.md` first — it is law (ownership, contracts, style).

## Mission (Week 1)
Document text extraction + TTS synthesis + the backend test suite + sample fixtures.

## Ownership
`backend/app/services/extraction.py`, `backend/app/services/tts.py`, `backend/tests/**` (including fixtures).

## extraction.py (exact signatures in AGENTS.md)
- Dispatch by extension: `.pptx` via python-pptx (iterate slides shapes with text_frame; include notes off), `.pdf` via pypdf (page.extract_text()), `.docx` via python-docx (paragraphs), `.txt` utf-8 decode with errors="replace".
- Raise ValueError on unsupported extension or empty extracted text (<10 chars).
- `doc_type()` returns short type string: pptx|pdf|docx|txt.
- Strip excessive whitespace, normalize newlines.

## tts.py (exact signature in AGENTS.md)
- gTTS (lang from profile not available here — use "en"); write MP3 bytes to out_path atomically (tmp then replace). Raise RuntimeError on empty text or library failure.

## tests/** (pytest, must pass offline & without GEMINI_API_KEY)
- test_extraction.py: build tiny fixtures programmatically OR commit binary fixtures under tests/fixtures (sample.pptx, sample.pdf, sample.docx, sample.txt each containing ≥2 recognizable sentences like "Photosynthesis converts light energy into chemical energy."). Assert extract_text returns the sentence text for each; ValueError cases (bad ext, empty).
- test_tts_mocked.py: monkeypatch gTTS save to write b"ID3MOCK" and assert file written + RuntimeError raised for empty input.
- test_adapter_fallback.py: call adapter.adapt_document with no monkeypatched network; assert used_llm False, results contain simplified_text ok, chunking respects small vs large.
- test_api_smoke.py (integration): FastAPI TestClient over the real app — register→me→profile put/get merge→consent upsert→upload sample.txt→adapt→assert response schema keys. Use tmp DATABASE_URL (sqlite memory won't share across clients—use file in tmp_path). If app import needs cwd, use os.environ.setdefault("DATABASE_URL", ...) BEFORE importing app.main.

## Fixture generation
If committing binaries is unreliable, generate them in a session-scoped fixture using python-pptx/docx/reportlab-free minimal pdf (pypdf can't write; craft minimal PDF bytes by hand with a simple text object, or skip .pdf happy-path assert to "extract_text runs and returns str"). Prefer real asserts where cheap.

## Self-check
`backend\.venv\Scripts\python -m pytest backend/tests -q` → all green.
