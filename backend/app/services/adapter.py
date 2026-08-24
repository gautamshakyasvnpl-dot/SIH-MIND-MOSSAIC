import re
import uuid
from typing import Any

from app.core.config import settings
from app.services import llm_client

_CHUNK_BUDGETS: dict[str, int] = {"small": 40, "medium": 80, "large": 150}
_SENTENCE_RE = re.compile(r"[.!?]+")
_FIRST_CHUNKS = 5


def _split_sentences(text: str) -> list[str]:
    parts = _SENTENCE_RE.split(text)
    tails = _SENTENCE_RE.findall(text)
    sentences: list[str] = []
    for body, tail in zip(parts, [*tails, ""]):
        sentence = (body + tail).strip()
        if sentence:
            sentences.append(sentence)
    return sentences


def _heuristic_simplify(text: str, chunk_size: str) -> str:
    budget = _CHUNK_BUDGETS.get(chunk_size, _CHUNK_BUDGETS["medium"])
    chunks: list[list[str]] = []
    current: list[str] = []
    word_count = 0
    for sentence in _split_sentences(text):
        words = len(sentence.split())
        if current and word_count + words > budget:
            chunks.append(current)
            current = []
            word_count = 0
        current.append(sentence)
        word_count += words
    if current:
        chunks.append(current)
    selected = chunks[:_FIRST_CHUNKS]
    return "\n\n".join(" ".join(chunk) for chunk in selected)


def _simplified_text_result(
    llm_content: str | None, chunk_size: str, pace: str
) -> dict[str, Any]:
    budget = _CHUNK_BUDGETS.get(chunk_size, _CHUNK_BUDGETS["medium"])
    sentence_style = (
        "very short sentences" if pace == "gentle" else "concise sentences"
    )
    if llm_content is not None:
        explanation = (
            f"LLM-simplified for a neurodivergent learner using profile settings "
            f"chunk_size={chunk_size} ({budget} words per chunk max) and pace={pace} "
            f"({sentence_style}); meaning preserved, no added facts."
        )
        return {
            "format": "simplified_text",
            "status": "ok",
            "content": llm_content,
            "explanation": explanation,
        }
    explanation = (
        f"Heuristic mode (no LLM available): deterministic sentence split grouped into chunks of up to "
        f"{budget} words per profile chunk_size={chunk_size}, pace={pace}; first {_FIRST_CHUNKS} chunks shown."
    )
    return {
        "format": "simplified_text",
        "status": "ok",
        "content": None,
        "explanation": explanation,
    }


def _tts_result(text: str) -> dict[str, Any]:
    filename = f"{uuid.uuid4().hex}.mp3"
    try:
        from app.services.tts import synthesize_speech_bounded

        out_dir = settings.audio_dir
        out_dir.mkdir(parents=True, exist_ok=True)
        synthesize_speech_bounded(text, out_dir / filename)
    except Exception as exc:
        return {
            "format": "tts_audio",
            "status": "error",
            "content": None,
            "explanation": f"Audio could not be generated: {exc}",
        }
    return {
        "format": "tts_audio",
        "status": "ok",
        "content": f"/api/audio/{filename}",
        "explanation": f"Audio synthesized locally with gTTS ({filename}) from the document text.",
    }


def _clean_label(sentence: str, max_words: int = 6) -> str:
    words = re.sub(r"[^\w\s-]", "", sentence).split()
    return " ".join(words[:max_words]) or "idea"


def _heuristic_concept_map(text: str) -> str:
    sentences = [s for s in _split_sentences(text) if len(s.split()) >= 4]
    if not sentences:
        sentences = _split_sentences(text) or ["Empty document"]
    root = _clean_label(sentences[0], 5)
    lines = ["graph TD", f'N0["{root}"]']
    children = sentences[1:6]
    if not children:
        children = sentences[-1:]
    for i, sentence in enumerate(children, start=1):
        label = _clean_label(sentence)
        lines.append(f'N{i}["{label}"]')
        lines.append(f"N0 --> N{i}")
    return "\n".join(lines)


def _concept_map_result(text: str, used_llm_flag: bool) -> dict[str, Any]:
    llm_map = llm_client.concept_map(text)
    if llm_map:
        return {
            "format": "concept_map",
            "status": "ok",
            "content": llm_map,
            "explanation": (
                "LLM-built Mermaid concept map (max 8 nodes) so visual learners "
                "can see how the main ideas connect before reading."
            ),
        }
    diagram = _heuristic_concept_map(text)
    return {
        "format": "concept_map",
        "status": "ok",
        "content": diagram,
        "explanation": (
            "Heuristic mode (no LLM available): the first sentence becomes the central "
            "topic and the next distinct sentences branch from it as a Mermaid graph."
        ),
    }


_KNOWN_FORMATS = ("simplified_text", "tts_audio", "concept_map")

_UNSUPPORTED_EXPLANATION = (
    "This format isn't supported yet, so nothing was generated for it. "
    "You can try simplified_text, tts_audio, or concept_map instead."
)


def adapt_document(text: str, profile: dict, formats: list[str] | None = None) -> dict:
    requested_tokens = list(formats or [])
    recognized = [f for f in requested_tokens if f in _KNOWN_FORMATS]
    unsupported = [f for f in requested_tokens if f not in _KNOWN_FORMATS]
    if recognized:
        requested = recognized
    elif unsupported:
        requested = []
    else:
        requested = ["simplified_text", "tts_audio"]

    chunk_size = str(profile.get("chunk_size", "medium"))
    pace = str(profile.get("pace", "standard"))
    results: list[dict[str, Any]] = []
    used_llm = False

    llm_content: str | None = None
    if "simplified_text" in requested:
        llm_content = llm_client.simplify_text(text, chunk_size, pace)
        used_llm = used_llm or llm_content is not None
        simplified_result = _simplified_text_result(llm_content, chunk_size, pace)
        if not used_llm:
            simplified_result["content"] = _heuristic_simplify(text, chunk_size)
        results.append(simplified_result)

    if "concept_map" in requested:
        map_result = _concept_map_result(text, used_llm)
        results.append(map_result)

    if "tts_audio" in requested:
        source_for_tts = llm_content if llm_content is not None else text
        results.append(_tts_result(source_for_tts))

    results.extend(
        {
            "format": token,
            "status": "error",
            "content": None,
            "explanation": _UNSUPPORTED_EXPLANATION,
        }
        for token in unsupported
    )

    return {"results": results, "used_llm": used_llm}
