"""
Pydantic schemas for Session and Cycle requests and responses.
Enforces validation rules, allowed difficulties, and public serialization boundaries.
"""

from typing import Any, Literal, Optional, Union
from pydantic import BaseModel, Field, field_validator


class SessionCreateRequest(BaseModel):
    """Request payload for starting a new learning session."""
    topic: str = Field(
        ...,
        description="The subject or topic to learn",
        min_length=1,
        max_length=255,
        examples=["Python Memory Management"]
    )
    initial_difficulty: Optional[Literal["Beginner", "Intermediate", "Advanced"]] = Field(
        default="Beginner",
        description="Optional starting difficulty tier: Beginner, Intermediate, or Advanced"
    )

    @field_validator("topic", mode="after")
    @classmethod
    def validate_topic_non_whitespace(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Topic cannot be empty or whitespace only.")
        return cleaned


class PublicQuizQuestion(BaseModel):
    """Public representation of a single quiz question without correct answer."""
    question_index: int = Field(description="Zero-based index (0 to 11)")
    question: str = Field(description="The question prompt")
    options: list[str] = Field(description="Exactly four answer choices")


class PublicLearningCycle(BaseModel):
    """Public representation of a pedagogical cycle."""
    cycle_id: str
    cycle_number: int
    difficulty_level: str
    status: str
    explanation: str
    notes: list[str]
    quiz: list[PublicQuizQuestion]
    score_percentage: Optional[float] = None
    submitted_answers: Optional[list[Any]] = None
    created_at: Optional[str] = None
    submitted_at: Optional[str] = None


class SessionCreateResponse(BaseModel):
    """Response payload returned upon successful session creation."""
    session_id: str
    topic: str
    current_difficulty: str
    status: str
    is_mastered: bool
    current_cycle_number: int
    cycle: PublicLearningCycle


class SessionDetailResponse(BaseModel):
    """Response payload for session state and history retrieval."""
    session_id: str
    topic: str
    current_difficulty: str
    status: str
    is_mastered: bool
    current_cycle_number: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    cycles: list[PublicLearningCycle]


class SessionSummaryItem(BaseModel):
    """Summary item for session listing."""
    session_id: str
    topic: str
    current_difficulty: str
    status: str
    is_mastered: bool
    current_cycle_number: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class AnswerItem(BaseModel):
    """Individual answer item with question index and selected option."""
    question_index: Optional[int] = Field(default=None, description="Zero-based question index (0 to 11)")
    selected_option: str = Field(..., description="Selected option text", min_length=1)


class QuizSubmissionRequest(BaseModel):
    """Request payload for submitting quiz answers for evaluation."""
    answers: list[Union[AnswerItem, str]] = Field(
        ...,
        description="Exactly 12 answer items, either as strings or objects with selected_option"
    )

    @field_validator("answers", mode="after")
    @classmethod
    def validate_answers_count(cls, v: list) -> list:
        if len(v) != 12:
            raise ValueError(f"Quiz submission requires exactly 12 answers, got {len(v)}.")
        return v


class QuestionResultItem(BaseModel):
    """Grading result for an individual quiz question."""
    question_index: int
    question: str
    selected_option: str
    correct_answer: str
    is_correct: bool


class NextStepInfo(BaseModel):
    """Guidance for next action in the learning loop."""
    action: str = Field(description="'FETCH_NEXT_CYCLE' or 'TOPIC_COMPLETED'")
    message: str = Field(description="Human-readable explanation of next step")
    endpoint: Optional[str] = Field(default=None, description="Next API endpoint URL if applicable")
    method: Optional[str] = Field(default=None, description="HTTP method for next step")


class QuizSubmissionResponse(BaseModel):
    """Complete evaluation response following quiz submission."""
    session_id: str
    cycle_number: int
    difficulty_level: str
    score_percentage: float
    correct_count: int
    total_questions: int = 12
    next_difficulty: str
    is_mastered: bool
    status: str
    feedback: str
    results: list[QuestionResultItem]
    next_step: NextStepInfo


