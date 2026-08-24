"""AI provider abstraction.

Selection order (first configured wins):
1. OpenAI-compatible endpoint  -> LLM_API_KEY + LLM_BASE_URL (+ LLM_MODEL)
2. Google Gemini via LangChain -> GEMINI_API_KEY
3. NullProvider                -> always returns None (heuristics take over)

All failures degrade to None; callers fall back to deterministic logic and
label output honestly (used_llm=false / engine=heuristic).
"""

import json
import os
import urllib.request
from typing import Protocol


class AIProvider(Protocol):
    name: str

    def invoke(self, prompt: str) -> str | None: ...


class NullProvider:
    name = "none"

    def invoke(self, prompt: str) -> str | None:
        return None


class OpenAICompatibleProvider:
    name = "openai-compatible"

    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    def invoke(self, prompt: str) -> str | None:
        payload = json.dumps(
            {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.4,
            }
        ).encode()
        req = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                data = json.loads(resp.read().decode())
            content = data["choices"][0]["message"]["content"]
            return content.strip() if isinstance(content, str) and content.strip() else None
        except Exception:
            return None


class GeminiProvider:
    name = "gemini"

    def invoke(self, prompt: str) -> str | None:
        try:
            from app.services.llm_client import _build_model

            response = _build_model().invoke(prompt)
            content = getattr(response, "content", None)
            return content.strip() if isinstance(content, str) and content.strip() else None
        except Exception:
            return None


def get_provider() -> AIProvider:
    llm_key = os.environ.get("LLM_API_KEY", "").strip()
    llm_base = os.environ.get("LLM_BASE_URL", "").strip()
    if llm_key and llm_base:
        return OpenAICompatibleProvider(
            llm_key, llm_base, os.environ.get("LLM_MODEL", "gpt-4o-mini")
        )
    if os.environ.get("GEMINI_API_KEY", "").strip():
        return GeminiProvider()
    return NullProvider()


def is_llm_available() -> bool:
    return not isinstance(get_provider(), NullProvider)
