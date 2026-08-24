_GROUNDING = (
    "Try box breathing: in 4s, hold 4s, out 4s, hold 4s - four rounds. "
    "It is okay to pause your work afterwards."
)
_ESCALATION = (
    "If the feeling stays heavy, the Equal Opportunity Cell and student "
    "counselling services are there for you - reaching out is a strong move."
)
_BREAK_NUDGE = (
    "You are in the middle of the pack today - a five-minute screen break "
    "could reset your focus."
)
_POSITIVE = (
    "Glad you are doing well - a good moment to start one of your sprints."
)


_EMOTION_ACK: dict[str, str] = {
    "sadness": "Your note reads as heavy-hearted - naming it takes courage.",
    "fear": "Your note reads as anxious - that is a common response before study pressure.",
    "anger": "Your note reads as frustrated - it makes sense to feel that way sometimes.",
    "disgust": "Your note reads as put off - stepping back from what drained you is fair.",
    "joy": "Your note carries good energy - worth noticing and keeping.",
    "surprise": "Your note reads as startled - take a moment to let things settle.",
}


def suggest_for_mood(mood: int, emotion_label: str | None = None) -> str:
    mood = max(1, min(5, int(mood)))
    if mood <= 2:
        base = f"{_GROUNDING} {_ESCALATION}"
    elif mood == 3:
        base = _BREAK_NUDGE
    else:
        base = _POSITIVE
    ack = _EMOTION_ACK.get(emotion_label or "", "")
    return f"{ack} {base}".strip()
