from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def _strip_additional_properties(schema: dict) -> None:
    """
    Strips 'additionalProperties' from the exported OpenAPI schema because Google Gen AI
    backend rejects the 'additional_properties' field while Pydantic still enforces
    strict extra='forbid' validation locally.
    """
    schema.pop("additionalProperties", None)


class QuizQuestion(BaseModel):
    """
    Schema representing a multiple-choice quiz question.
    Strictly requires exactly four distinct options and a correct answer
    that matches one of the options.
    """
    model_config = ConfigDict(
        extra="forbid", json_schema_extra=_strip_additional_properties
    )

    question: str = Field(description="The question text")
    options: list[str] = Field(description="Exactly four distinct answer choices")
    correct_answer: str = Field(description="The exact text of the correct option")

    @field_validator("question", "correct_answer", mode="after")
    @classmethod
    def validate_non_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field must be a non-empty string.")
        return v

    @field_validator("options", mode="after")
    @classmethod
    def validate_options(cls, v: list[str]) -> list[str]:
        if len(v) != 4:
            raise ValueError(f"Options must contain exactly 4 choices, got {len(v)}.")
        if any(not opt or not opt.strip() for opt in v):
            raise ValueError("All options must be non-empty strings.")
        if len(set(v)) != 4:
            raise ValueError("All 4 options must be distinct.")
        return v

    @model_validator(mode="after")
    def validate_correct_answer_matches_option(self) -> "QuizQuestion":
        if self.correct_answer not in self.options:
            raise ValueError(
                f"correct_answer '{self.correct_answer}' does not match any of the provided options: {self.options}"
            )
        return self


class LearningModule(BaseModel):
    """
    Schema representing a structured learning module.
    Enforces non-empty content, restricted difficulty levels,
    between 3 and 5 summary notes, and exactly 12 quiz questions.
    """
    model_config = ConfigDict(
        extra="forbid", json_schema_extra=_strip_additional_properties
    )

    topic: str = Field(description="The subject or topic title")
    difficulty_level: Literal["Beginner", "Intermediate", "Advanced"] = Field(
        description="Target difficulty level: Beginner, Intermediate, or Advanced"
    )
    explanation: str = Field(description="Pedagogical explanation tailored to difficulty")
    notes: list[str] = Field(description="Summary bullet notes (3 to 5 items)")
    quiz: list[QuizQuestion] = Field(
        description="Practice quiz consisting of exactly 12 distinct, topic-relevant questions"
    )

    @field_validator("topic", "explanation", mode="after")
    @classmethod
    def validate_non_empty_text(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field must be a non-empty string.")
        return v

    @field_validator("notes", mode="after")
    @classmethod
    def validate_notes(cls, v: list[str]) -> list[str]:
        if not (3 <= len(v) <= 5):
            raise ValueError(f"Notes must contain between 3 and 5 items, got {len(v)}.")
        if any(not note or not note.strip() for note in v):
            raise ValueError("All notes must be non-empty strings.")
        return v

    @field_validator("quiz", mode="after")
    @classmethod
    def validate_quiz(cls, v: list[QuizQuestion]) -> list[QuizQuestion]:
        if len(v) != 12:
            raise ValueError(f"Quiz must contain exactly 12 questions, got {len(v)}.")
        return v
