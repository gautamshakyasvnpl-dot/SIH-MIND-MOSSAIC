"""Communication assistant: deterministic drafting templates.

Turns rough thoughts into structured drafts (email, message structure,
presentation outline). Labelled engine="template" — no AI pretence.
"""

import re


def _first_clause(text: str, max_words: int = 9) -> str:
    clause = re.split(r"[.!?\n]", (text or "").strip(), maxsplit=1)[0]
    words = clause.split()
    return " ".join(words[:max_words]) if words else "Update"


def draft_email(raw: str, recipient: str = "", deadline: str = "") -> str:
    raw = (raw or "").strip() or "I wanted to follow up on my progress."
    who = recipient.strip() or "Professor"
    subject = _first_clause(raw)
    deadline_line = f"\nCould you confirm whether {deadline.strip()} is workable?" if deadline else ""
    return (
        f"Subject: {subject}\n\n"
        f"Dear {who},\n\n"
        f"I am writing about the following: {raw}\n\n"
        "Situation: what led to this is briefly as described above.\n"
        "Request: could we agree on a way forward that works for both of us?\n"
        f"{deadline_line}\n"
        "Thank you for your time and understanding.\n\n"
        "Best regards,\n[Your name]"
    )


def structure_message(raw: str) -> dict[str, str]:
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n", (raw or "").strip()) if s.strip()]
    situation: list[str] = []
    explanation: list[str] = []
    request: list[str] = []
    deadline: list[str] = []
    cue_request = re.compile(r"\b(can we|could you|please|request|i would like|hope)\b", re.I)
    cue_deadline = re.compile(r"\b(by|before|deadline|due)\b[^.]*\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday|tomorrow|next week|\d{1,2}(:\d{2})?\s?(am|pm))", re.I)
    cue_explain = re.compile(r"\b(because|since|as a result|therefore|however|due to|but )\b", re.I)
    for s in sentences:
        if cue_deadline.search(s):
            deadline.append(s)
        elif cue_request.search(s):
            request.append(s)
        elif cue_explain.search(s):
            explanation.append(s)
        else:
            situation.append(s)
    return {
        "situation": " ".join(situation) or _first_clause(raw),
        "explanation": " ".join(explanation) or "(Add the reason here.)",
        "request": " ".join(request) or "(State clearly what you are asking for.)",
        "deadline": " ".join(deadline) or "(Confirm the date/time.)",
    }


def presentation_outline(topic: str, notes: str = "") -> dict[str, object]:
    topic = (topic or "").strip() or "My topic"
    stems = [
        s.strip()
        for s in re.split(r"(?<=[.!?])\s+|\n|;", (notes or "").strip())
        if len(s.strip().split()) >= 3
    ]
    key_points = stems[:4] or [
        f"Why {topic} matters in practice",
        f"The core idea behind {topic}",
        f"A worked example of {topic}",
        f"Common mistakes with {topic}",
    ]
    opening = (
        f"Good morning everyone. In the next few minutes I will walk you through "
        f"{topic}, why it matters for our course, and one worked example."
    )
    conclusion = (
        f"To conclude: {topic} comes down to its core idea, one clear example, "
        "and knowing where it is applied. Thank you - happy to take questions."
    )
    speaker_notes = [
        "Say this slowly; pause after each point.",
        "Point at the slide heading while introducing the section.",
        "If asked something unknown: 'Good question - let me check and follow up.'",
    ]
    return {
        "opening": opening,
        "key_points": key_points,
        "conclusion": conclusion,
        "speaker_notes": speaker_notes,
    }
