"""
SQLAlchemy models for Learning Sessions and Adaptive Cycles.
Defines persistent schema, relational constraints, foreign keys, and serialization helpers.
"""

from datetime import datetime, timezone
import uuid
from typing import Any, Optional
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from backend.database import Base

# Status Constants
SESSION_STATUS_IN_PROGRESS = "IN_PROGRESS"
SESSION_STATUS_MASTERED = "MASTERED"
VALID_SESSION_STATUSES = (SESSION_STATUS_IN_PROGRESS, SESSION_STATUS_MASTERED)

CYCLE_STATUS_IN_PROGRESS = "IN_PROGRESS"
CYCLE_STATUS_SUBMITTED = "SUBMITTED"
VALID_CYCLE_STATUSES = (CYCLE_STATUS_IN_PROGRESS, CYCLE_STATUS_SUBMITTED)

VALID_DIFFICULTIES = ("Beginner", "Intermediate", "Advanced")


def generate_session_id() -> str:
    """Generate a prefixed unique session identifier."""
    return f"sess_{uuid.uuid4().hex[:12]}"


def generate_cycle_id() -> str:
    """Generate a prefixed unique cycle identifier."""
    return f"cycle_{uuid.uuid4().hex[:12]}"


def utc_now() -> datetime:
    """Returns current UTC timestamp with timezone."""
    return datetime.now(timezone.utc)


class SessionModel(Base):
    """
    Represents a persistent learner session for a specific topic.
    Tracks overall progress, current difficulty level, cycle count, and mastery status.
    """
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True, default=generate_session_id, index=True)
    topic = Column(String(255), nullable=False, index=True)
    current_difficulty = Column(String(32), nullable=False, default="Beginner")
    status = Column(String(32), nullable=False, default=SESSION_STATUS_IN_PROGRESS, index=True)
    current_cycle_number = Column(Integer, nullable=False, default=1)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )

    # Relational cascade to cycles
    cycles = relationship(
        "LearningCycleModel",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="LearningCycleModel.cycle_number",
    )

    def to_dict(self) -> dict[str, Any]:
        """Serializes session summary to a dictionary."""
        return {
            "session_id": self.id,
            "topic": self.topic,
            "current_difficulty": self.current_difficulty,
            "status": self.status,
            "is_mastered": self.status == SESSION_STATUS_MASTERED,
            "current_cycle_number": self.current_cycle_number,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class LearningCycleModel(Base):
    """
    Represents a single pedagogical cycle within a learning session.
    Stores the lesson explanation, revision notes, 12 sanitized quiz questions,
    and the trusted server-side answer key in strict isolation.
    """
    __tablename__ = "learning_cycles"

    id = Column(String(36), primary_key=True, default=generate_cycle_id, index=True)
    session_id = Column(
        String(36),
        ForeignKey("sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    cycle_number = Column(Integer, nullable=False)
    difficulty_level = Column(String(32), nullable=False)
    explanation = Column(Text, nullable=False)

    # JSON-serialized content (3-5 notes and 12 sanitized questions)
    notes = Column(JSON, nullable=False)
    quiz_questions = Column(JSON, nullable=False)

    # Server-side ONLY trusted answer key (list of 12 strings or question-to-answer map)
    # Strictly isolated from public client representations
    answer_key = Column(JSON, nullable=False)

    # Evaluation fields
    status = Column(String(32), nullable=False, default=CYCLE_STATUS_IN_PROGRESS, index=True)
    score_percentage = Column(Float, nullable=True)
    submitted_answers = Column(JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    submitted_at = Column(DateTime(timezone=True), nullable=True)

    # Relationship to parent session
    session = relationship("SessionModel", back_populates="cycles")

    __table_args__ = (
        UniqueConstraint("session_id", "cycle_number", name="uq_session_cycle_number"),
    )

    def to_public_dict(self) -> dict[str, Any]:
        """
        Exports public representation for frontend clients.
        Strictly guarantees answer_key is excluded before quiz submission.
        """
        return {
            "cycle_id": self.id,
            "cycle_number": self.cycle_number,
            "difficulty_level": self.difficulty_level,
            "status": self.status,
            "explanation": self.explanation,
            "notes": self.notes,
            "quiz": self.quiz_questions,
            "score_percentage": self.score_percentage,
            "submitted_answers": self.submitted_answers,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
        }

