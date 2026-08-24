import sys
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def _long_text() -> str:
    sentences = [
        f"Sentence number {index} explains how plants convert sunlight into stored energy."
        for index in range(1, 13)
    ]
    return " ".join(sentences)


def test_adapter_falls_back_without_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    from app.services.adapter import adapt_document

    result = adapt_document(_long_text(), {"chunk_size": "small"})
    assert result["used_llm"] is False
    by_format = {item["format"]: item for item in result["results"]}
    assert set(by_format) == {"simplified_text", "tts_audio"}
    simplified = by_format["simplified_text"]
    assert simplified["status"] == "ok"
    assert isinstance(simplified["content"], str)
    assert simplified["content"].strip()
    explanation = simplified["explanation"].lower()
    assert "heuristic" in explanation or "setting" in explanation
