import os

from app.services import ai_provider

_WORD_BUDGETS: dict[str, int] = {"small": 40, "medium": 80, "large": 150}


def is_llm_available() -> bool:
    return ai_provider.is_llm_available()


def _build_model():
    from langchain_google_genai import ChatGoogleGenerativeAI

    return ChatGoogleGenerativeAI(
        model=os.environ.get("GEMINI_MODEL", "gemini-2.0-flash"),
        google_api_key=os.environ["GEMINI_API_KEY"],
    )


def simplify_text(text: str, chunk_size: str, pace: str) -> str | None:
    if not is_llm_available() or not text.strip():
        return None
    budget = _WORD_BUDGETS.get(chunk_size, _WORD_BUDGETS["medium"])
    sentence_style = "very short" if pace == "gentle" else "clear and concise"
    prompt = (
        "Simplify the following text for a neurodivergent learner.\n"
        f"- Use {sentence_style} sentences ({pace} pace).\n"
        f"- Split the answer into chunks of at most {budget} words, separated by blank lines.\n"
        "- Preserve the original meaning exactly; do not add new facts or opinions.\n"
        "- Output only the simplified text.\n\n"
        f"Text:\n{text}"
    )
    try:
        return ai_provider.get_provider().invoke(prompt)
    except Exception:
        return None


def suggest_pace(answers: dict, current: dict) -> str | None:
    if not is_llm_available():
        return None
    prompt = (
        "A neurodivergent learner answered onboarding questions.\n"
        f"Answers: {answers}\n"
        f"Current profile: {current}\n"
        "Decide their reading pace. Reply with exactly one word: gentle or standard."
    )
    try:
        content = ai_provider.get_provider().invoke(prompt) or ""
        pace = str(content).strip().lower()
        return pace if pace in ("gentle", "standard") else None
    except Exception:
        return None


def concept_map(text: str) -> str | None:
    """Mermaid 'graph TD' diagram for the document; None when unavailable."""
    if not is_llm_available() or not text.strip():
        return None
    from app.services.guard import data_block

    prompt = (
        "Build a concept map for a neurodivergent learner from this text.\n"
        "- Reply ONLY with a Mermaid flowchart starting with 'graph TD'.\n"
        "- Maximum 8 nodes; each node label is 2-6 words.\n"
        "- Show how the main ideas connect, rooted at the central topic.\n\n"
        f"{data_block(text[:6000])}"
    )
    try:
        content = ai_provider.get_provider().invoke(prompt)
        if isinstance(content, str) and "graph" in content.lower():
            return content.strip()
        return None
    except Exception:
        return None
