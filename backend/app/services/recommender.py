def recommend_format(
    text: str,
    profile: dict,
    usage_history: dict[str, int] | None = None,
) -> dict:
    modality = str(profile.get("modality_affinity", "text"))
    chunk_size = str(profile.get("chunk_size", "medium"))
    noise_sensitive = bool(profile.get("noise_sensitive", False))
    long_doc = len(text or "") > 4000
    history = usage_history or {}

    base = _base_recommendation(modality, chunk_size, noise_sensitive, long_doc)

    most_used_format, most_used_count = max(
        ((fmt, n) for fmt, n in history.items() if fmt in {"audio", "simplified_text"}),
        key=lambda kv: kv[1],
        default=(None, 0),
    )
    if (
        most_used_format is not None
        and most_used_count >= 2
        and most_used_format != base["format"]
    ):
        return {
            "format": most_used_format,
            "reason": f"You have chosen {most_used_format.replace('_', ' ')} "
            f"{most_used_count} times before - sticking with what works for you. "
            f"Your profile suggests {base['format'].replace('_', ' ')}: {base['reason']}",
        }
    return base


def _base_recommendation(
    modality: str,
    chunk_size: str,
    noise_sensitive: bool,
    long_doc: bool,
) -> dict:
    if modality == "audio":
        return {
            "format": "audio",
            "reason": "You told us you learn best by listening "
            "(modality_affinity: audio), so we suggest the audio version of "
            "this document.",
        }
    noise_note = (
        " Audio was set aside because your profile flags noise sensitivity "
        "(noise_sensitive: true)."
        if noise_sensitive
        else ""
    )
    if modality == "visual":
        return {
            "format": "simplified_text",
            "reason": "You prefer visual learning (modality_affinity: visual); "
            "we render simplified text with clear structure that pairs well "
            "with concept maps." + noise_note,
        }
    if chunk_size == "small":
        return {
            "format": "simplified_text",
            "reason": "You chose small chunks (chunk_size: small), so we break "
            "this document into shorter, simpler sections." + noise_note,
        }
    if long_doc and not noise_sensitive:
        return {
            "format": "audio",
            "reason": "This document is long (over 4000 characters) and your "
            "profile has noise_sensitive off - listening may be easier than "
            "reading it all.",
        }
    fields = f"modality_affinity: {modality}, chunk_size: {chunk_size}"
    if noise_sensitive:
        fields += ", noise_sensitive: true"
    length_note = (
        " We kept the full text despite its length because audio could feel "
        "overwhelming with your noise sensitivity."
        if long_doc and noise_sensitive
        else "; ask for simplified text or audio any time."
    )
    return {
        "format": "original_text",
        "reason": f"With your profile ({fields}) reading this document as-is "
        f"suits you best{length_note}",
    }
