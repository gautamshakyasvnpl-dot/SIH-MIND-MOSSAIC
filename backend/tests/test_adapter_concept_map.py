from app.services.adapter import adapt_document

SAMPLE = (
    "Photosynthesis converts light energy into chemical energy. "
    "Plants absorb sunlight through chlorophyll in their leaves. "
    "The process produces glucose and releases oxygen into the air. "
    "Respiration then breaks glucose down to release energy for cells. "
    "Together these reactions power plant growth and biomass."
)


def test_concept_map_fallback_is_mermaid_graph():
    out = adapt_document(SAMPLE, {}, formats=["concept_map"])
    assert out["used_llm"] is False
    assert len(out["results"]) == 1
    item = out["results"][0]
    assert item["format"] == "concept_map" and item["status"] == "ok"
    diagram = str(item["content"])
    lines = [ln.strip() for ln in diagram.splitlines()]
    assert lines[0] == "graph TD"
    edges = [ln for ln in lines if "-->" in ln]
    node_defs = [ln for ln in lines if "[" in ln and '"' in ln]
    assert len(edges) >= 1
    assert len(node_defs) >= 2


def test_concept_map_root_is_first_sentence_topic():
    out = adapt_document(SAMPLE, {}, formats=["concept_map"])
    content = str(out["results"][0]["content"])
    first_node = [ln for ln in content.splitlines() if ln.startswith("N0")][0]
    assert "Photosynthesis converts" in first_node


def test_formats_filter_controls_outputs_and_skips_tts():
    out = adapt_document(SAMPLE, {"chunk_size": "small"}, formats=["simplified_text", "concept_map"])
    formats = {r["format"] for r in out["results"]}
    assert formats == {"simplified_text", "concept_map"}
    full = adapt_document(SAMPLE, {})
    assert {r["format"] for r in full["results"]} == {"simplified_text", "tts_audio"}


def test_unknown_format_token_yields_error_entry():
    out = adapt_document(SAMPLE, {}, formats=["hologram"])
    assert len(out["results"]) == 1
    item = out["results"][0]
    assert item["format"] == "hologram"
    assert item["status"] == "error"
    assert isinstance(item["explanation"], str) and item["explanation"].strip()
    assert out["used_llm"] is False


def test_unknown_token_errors_while_concept_map_still_works():
    out = adapt_document(SAMPLE, {}, formats=["hologram", "concept_map"])
    items = {r["format"]: r for r in out["results"]}
    assert items["concept_map"]["status"] == "ok"
    assert str(items["concept_map"]["content"]).startswith("graph TD")
    assert items["hologram"]["status"] == "error"
    assert items["hologram"]["content"] is None


def test_default_call_without_formats_keeps_week1_contract():
    out = adapt_document(SAMPLE, {})
    assert {r["format"] for r in out["results"]} == {"simplified_text", "tts_audio"}


def test_empty_text_still_yields_valid_single_node_map():
    out = adapt_document("", {}, formats=["concept_map"])
    diagram = str(out["results"][0]["content"])
    assert diagram.startswith("graph TD")
