from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from app.services import llm_client


class ProfilerState(TypedDict):
    answers: dict
    profile: dict
    suggestion: dict


def _truthy(answers: dict, key: str) -> bool:
    return bool(answers.get(key))


def _infer(state: ProfilerState) -> ProfilerState:
    answers = state.get("answers") or {}
    merged = dict(state.get("profile") or {})

    if _truthy(answers, "likes_listening") or _truthy(answers, "prefers_audio"):
        merged["modality_affinity"] = "audio"
    if _truthy(answers, "prefers_images") or _truthy(answers, "prefers_visual"):
        merged["modality_affinity"] = "visual"
    if _truthy(answers, "slow_reader") or _truthy(answers, "dyslexia_friendly_font"):
        merged["font_style"] = "dyslexia_friendly"
        merged["line_spacing"] = "wide"
    if _truthy(answers, "overwhelmed_by_motion"):
        merged["reduce_motion"] = True
    if _truthy(answers, "short_attention"):
        merged["chunk_size"] = "small"
        merged["pace"] = "gentle"
    if _truthy(answers, "noise_sensitive"):
        merged["noise_sensitive"] = True

    suggestion = {**merged, "onboarding_complete": True}
    return {
        "answers": answers,
        "profile": state.get("profile") or {},
        "suggestion": suggestion,
    }


def _refine(state: ProfilerState) -> ProfilerState:
    suggestion = dict(state.get("suggestion") or {})
    adjusted = llm_client.suggest_pace(state.get("answers") or {}, suggestion)
    if adjusted:
        suggestion["pace"] = adjusted
    return {
        "answers": state.get("answers") or {},
        "profile": state.get("profile") or {},
        "suggestion": suggestion,
    }


def build_profiler_graph():
    graph = StateGraph(ProfilerState)
    graph.add_node("infer", _infer)
    graph.add_edge(START, "infer")
    if llm_client.is_llm_available():
        graph.add_node("refine", _refine)
        graph.add_edge("infer", "refine")
        graph.add_edge("refine", END)
    else:
        graph.add_edge("infer", END)
    return graph.compile()


def run_profiler(answers: dict, current: dict) -> dict:
    result = build_profiler_graph().invoke(
        {"answers": dict(answers), "profile": dict(current), "suggestion": {}}
    )
    return dict(result.get("suggestion") or {})
