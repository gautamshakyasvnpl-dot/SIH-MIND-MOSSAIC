from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, StrictBool, StrictInt, field_validator, model_validator

ModalityAffinity = Literal["text", "audio", "visual"]
ChunkSize = Literal["small", "medium", "large"]
FontStyle = Literal["default", "dyslexia_friendly"]
LineSpacing = Literal["normal", "wide"]
Pace = Literal["gentle", "standard"]


def _normalize_email(value: str) -> str:
    return value.strip().lower()


class RegisterIn(BaseModel):
    email: str
    password: str
    display_name: str

    @field_validator("email")
    @classmethod
    def normalize_and_check_email(cls, value: str) -> str:
        normalized = _normalize_email(value)
        if not normalized or "@" not in normalized:
            raise ValueError("A valid email address is required")
        return normalized

    @field_validator("password")
    @classmethod
    def password_min_length(cls, value: str) -> str:
        if len(value.strip()) < 8:
            raise ValueError("Password must be at least 8 characters")
        return value


class LoginIn(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return _normalize_email(value)


class UserOut(BaseModel):
    id: str
    email: str
    display_name: str


class TokenOut(BaseModel):
    token: str
    user: UserOut


class ProfileOut(BaseModel):
    modality_affinity: ModalityAffinity = "text"
    chunk_size: ChunkSize = "medium"
    font_style: FontStyle = "default"
    line_spacing: LineSpacing = "normal"
    reduce_motion: bool = False
    audio_autoplay: bool = False
    pace: Pace = "standard"
    noise_sensitive: bool = False
    onboarding_complete: bool = False


DEFAULT_PROFILE: dict[str, Any] = ProfileOut().model_dump()


class ProfilePut(BaseModel):
    modality_affinity: ModalityAffinity | None = None
    chunk_size: ChunkSize | None = None
    font_style: FontStyle | None = None
    line_spacing: LineSpacing | None = None
    reduce_motion: StrictBool | None = None
    audio_autoplay: StrictBool | None = None
    pace: Pace | None = None
    noise_sensitive: StrictBool | None = None
    onboarding_complete: StrictBool | None = None

    @model_validator(mode="after")
    def reject_explicit_nulls(self) -> "ProfilePut":
        for name in sorted(self.model_fields_set):
            if getattr(self, name) is None:
                raise ValueError(f"{name} cannot be null; omit the field to keep the stored value")
        return self


class ConsentsIn(BaseModel):
    voice: StrictBool | None = None
    telemetry: StrictBool | None = None
    memory: StrictBool | None = None

    @model_validator(mode="after")
    def reject_explicit_nulls(self) -> "ConsentsIn":
        for name in sorted(self.model_fields_set):
            if getattr(self, name) is None:
                raise ValueError(f"{name} cannot be null; omit the field to keep the stored value")
        return self


class ConsentsOut(BaseModel):
    voice: bool = False
    telemetry: bool = False
    memory: bool = False


class DocumentOut(BaseModel):
    id: str
    filename: str
    doc_type: str
    char_count: int
    created_at: datetime


class DocumentListOut(BaseModel):
    items: list[DocumentOut]


class AdaptIn(BaseModel):
    formats: list[str]


class AdaptResultItem(BaseModel):
    format: str
    status: str
    content: Any = None
    explanation: str | None = None


class AdaptOut(BaseModel):
    document_id: str
    used_llm: bool = False
    results: list[AdaptResultItem]


class AskIn(BaseModel):
    question: str


class AskSource(BaseModel):
    chunk_index: int
    snippet: str


class AskOut(BaseModel):
    document_id: str
    answer: str
    used_llm: bool = False
    sources: list[AskSource]


class TaskIn(BaseModel):
    title: str
    due_date: date | None = None
    notes: str | None = None


class SprintOut(BaseModel):
    id: str
    index: int
    description: str
    minutes: int
    done: bool


class TaskOut(BaseModel):
    id: str
    title: str
    due_date: date | None
    notes: str | None
    status: str
    created_at: datetime
    sprints: list[SprintOut]


class TaskListOut(BaseModel):
    items: list[TaskOut]


class AnswerIn(BaseModel):
    answer: str


class VivaStartOut(BaseModel):
    session_id: str
    document_id: str
    question: str
    turn_count: int


class VivaAnswerOut(BaseModel):
    feedback: str
    score: int
    next_question: str | None
    done: bool
    turn_count: int


class VivaTurnOut(BaseModel):
    index: int
    question: str
    answer: str | None
    feedback: str | None
    score: int | None


class VivaSessionOut(BaseModel):
    session_id: str
    document_id: str
    done: bool
    turns: list[VivaTurnOut]


class EmotionOut(BaseModel):
    label: str
    score: float


class FaceMoodOut(BaseModel):
    emotion: EmotionOut | None = None
    engine: str
    runner_up: str | None = None
    detail: str | None = None


class CheckinIn(BaseModel):
    mood: StrictInt
    note: str | None = None

    @field_validator("mood")
    @classmethod
    def mood_in_range(cls, value: int) -> int:
        if not 1 <= value <= 5:
            raise ValueError("mood must be an integer from 1 to 5")
        return value


class CheckinOut(BaseModel):
    id: str
    mood: int
    note: str | None
    suggestion: str
    created_at: datetime


class CheckinListOut(BaseModel):
    items: list[CheckinOut]


class RecommendOut(BaseModel):
    format: str
    reason: str


class InteractionIn(BaseModel):
    event: str
    document_id: str | None = None
    concept: str | None = None
    metadata: dict[str, Any] | None = None


class ChangeOut(BaseModel):
    key: str
    old: float
    new: float
    explanation: str


class InteractionOut(BaseModel):
    id: str
    event: str
    concept: str | None = None
    document_id: str | None = None
    created_at: datetime


class PreferencesOut(BaseModel):
    scores: dict[str, float]
    labels: dict[str, str]
    profile_lines: list[str]
    recent_events: list[InteractionOut] = []


class PreferencesUpdate(BaseModel):
    scores: dict[str, float]


class ReaderCardOut(BaseModel):
    index: int
    title: str
    simple: str
    technical: str
    example: str | None = None
    has_visual: bool = False
    concept: str | None = None


class ReaderHints(BaseModel):
    start_level: int
    show_example_first: bool
    suggest_concept_map: bool
    suggest_quiz_after_cards: int
    prefer_audio: bool
    hints_explanation: list[str]


class ReaderOut(BaseModel):
    document_id: str
    filename: str
    cards: list[ReaderCardOut]
    presentation: ReaderHints


class ExplainIn(BaseModel):
    text: str
    level: int
    context: str | None = None
    transform: str | None = None
    target_lang: str = "Hindi"


class ExplainOut(BaseModel):
    level: int
    text: str
    engine: str


class QuizItem(BaseModel):
    id: str
    question: str
    options: list[str]
    answer_index: int
    concept: str | None = None


class QuizRequest(BaseModel):
    count: int = 3


class QuizOut(BaseModel):
    items: list[QuizItem]
    note: str = "Practice mode: answers are shown after you pick. This is self-study, not a test."


class CommunicationIn(BaseModel):
    mode: str
    topic: str = ""
    raw: str = ""
    recipient: str = ""
    deadline: str = ""


class CommunicationOut(BaseModel):
    mode: str
    engine: str
    result: Any


class PlanIn(BaseModel):
    items: list[str]


class PlanOut(BaseModel):
    high: list[str]
    medium: list[str]
    low: list[str]
    note: str = "A lighter plan, not a verdict. Reorder freely."


class AnalyticsOut(BaseModel):
    documents_count: int
    adaptive_changes_total: int
    adaptive_changes_last_24h: int
    interactions_total: int
    quiz_correct: int
    quiz_incorrect: int
    top_interactions: list[tuple[str, int]]


class MemoryConcept(BaseModel):
    concept: str
    misses: int


class MemoryOut(BaseModel):
    struggled_concepts: list[MemoryConcept]
    suggestions: list[str]


class VivaStartRequest(BaseModel):
    difficulty: str | None = None


class SttOut(BaseModel):
    text: str
    engine: str


class MediaTokenIn(BaseModel):
    kind: str
    id: str
    index: int | None = None


class MediaTokenOut(BaseModel):
    token: str
    expires_in: int
    url: str
