"""
Database repository / data access layer.
Encapsulates CRUD operations, transactional persistence, and state consistency
for SessionModel and LearningCycleModel.
"""

from datetime import datetime, timezone
from typing import Any, Optional
from sqlalchemy.orm import Session

from backend.models import (
    CYCLE_STATUS_IN_PROGRESS,
    CYCLE_STATUS_SUBMITTED,
    SESSION_STATUS_IN_PROGRESS,
    SESSION_STATUS_MASTERED,
    LearningCycleModel,
    SessionModel,
    utc_now,
)


def create_session(
    db: Session, topic: str, initial_difficulty: str = "Beginner"
) -> SessionModel:
    """
    Creates and persists a new learning session in a transaction.
    """
    cleaned_topic = topic.strip()
    session = SessionModel(
        topic=cleaned_topic,
        current_difficulty=initial_difficulty,
        status=SESSION_STATUS_IN_PROGRESS,
        current_cycle_number=1,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def create_session_with_initial_cycle(
    db: Session,
    topic: str,
    difficulty_level: str,
    explanation: str,
    notes: list[str],
    quiz_questions: list[dict[str, Any]],
    answer_key: list[str],
) -> tuple[SessionModel, LearningCycleModel]:
    """
    Atomically creates a session and its initial cycle in a single database transaction.
    If cycle creation fails, the session is rolled back completely.
    """
    cleaned_topic = topic.strip()
    session = SessionModel(
        topic=cleaned_topic,
        current_difficulty=difficulty_level,
        status=SESSION_STATUS_IN_PROGRESS,
        current_cycle_number=1,
    )
    db.add(session)
    db.flush()  # Populates session.id without committing

    cycle = LearningCycleModel(
        session_id=session.id,
        cycle_number=1,
        difficulty_level=difficulty_level,
        explanation=explanation,
        notes=notes,
        quiz_questions=quiz_questions,
        answer_key=answer_key,
        status=CYCLE_STATUS_IN_PROGRESS,
    )
    db.add(cycle)
    db.commit()
    db.refresh(session)
    db.refresh(cycle)
    return session, cycle


def get_session(db: Session, session_id: str) -> Optional[SessionModel]:
    """Retrieves a session by primary key."""
    return db.query(SessionModel).filter(SessionModel.id == session_id).first()


def list_sessions(db: Session) -> list[SessionModel]:
    """Lists all saved sessions ordered by last update descending."""
    return db.query(SessionModel).order_by(SessionModel.updated_at.desc()).all()


def create_cycle(
    db: Session,
    session_id: str,
    cycle_number: int,
    difficulty_level: str,
    explanation: str,
    notes: list[str],
    quiz_questions: list[dict[str, Any]],
    answer_key: list[str],
) -> LearningCycleModel:
    """
    Creates and persists a learning cycle linked to a session.
    Strictly isolates the trusted answer_key in the private server-side column.
    """
    cycle = LearningCycleModel(
        session_id=session_id,
        cycle_number=cycle_number,
        difficulty_level=difficulty_level,
        explanation=explanation,
        notes=notes,
        quiz_questions=quiz_questions,
        answer_key=answer_key,
        status=CYCLE_STATUS_IN_PROGRESS,
    )
    db.add(cycle)
    db.commit()
    db.refresh(cycle)
    return cycle


def get_cycle(
    db: Session, session_id: str, cycle_number: int
) -> Optional[LearningCycleModel]:
    """Retrieves a specific cycle by session ID and cycle number."""
    return (
        db.query(LearningCycleModel)
        .filter(
            LearningCycleModel.session_id == session_id,
            LearningCycleModel.cycle_number == cycle_number,
        )
        .first()
    )


def get_active_cycle(db: Session, session_id: str) -> Optional[LearningCycleModel]:
    """
    Retrieves the currently active (unsubmitted or latest) cycle for a session.
    """
    session = get_session(db, session_id)
    if not session:
        return None
    return (
        db.query(LearningCycleModel)
        .filter(
            LearningCycleModel.session_id == session_id,
            LearningCycleModel.cycle_number == session.current_cycle_number,
        )
        .first()
    )


def submit_cycle(
    db: Session,
    cycle: LearningCycleModel,
    submitted_answers: list[Any],
    score_percentage: float,
) -> LearningCycleModel:
    """
    Updates a cycle with submitted answers and verified score percentage in a transaction.
    """
    cycle.submitted_answers = submitted_answers
    cycle.score_percentage = score_percentage
    cycle.status = CYCLE_STATUS_SUBMITTED
    cycle.submitted_at = utc_now()
    db.add(cycle)
    db.commit()
    db.refresh(cycle)
    return cycle


def update_session_difficulty(
    db: Session,
    session: SessionModel,
    next_difficulty: str,
    is_mastered: bool = False,
) -> SessionModel:
    """
    Updates a session's difficulty and mastery status in a transaction.
    Increments current_cycle_number when continuing.
    """
    session.current_difficulty = next_difficulty
    if is_mastered:
        session.status = SESSION_STATUS_MASTERED
    else:
        session.status = SESSION_STATUS_IN_PROGRESS
        session.current_cycle_number += 1

    session.updated_at = utc_now()
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def grade_and_submit_cycle(
    db: Session,
    session: SessionModel,
    cycle: LearningCycleModel,
    submitted_answers: list[str],
    score_percentage: float,
    next_difficulty: str,
    is_mastered: bool,
) -> tuple[SessionModel, LearningCycleModel]:
    """
    Atomically records quiz submission and updates session difficulty/mastery state
    in a single database transaction.
    """
    cycle.submitted_answers = submitted_answers
    cycle.score_percentage = score_percentage
    cycle.status = CYCLE_STATUS_SUBMITTED
    cycle.submitted_at = utc_now()

    if is_mastered:
        session.status = SESSION_STATUS_MASTERED
        session.current_difficulty = "Advanced"
    else:
        session.status = SESSION_STATUS_IN_PROGRESS
        session.current_difficulty = next_difficulty

    session.updated_at = utc_now()
    db.add(cycle)
    db.add(session)
    db.commit()
    db.refresh(cycle)
    db.refresh(session)
    return session, cycle


def create_next_cycle(
    db: Session,
    session: SessionModel,
    difficulty_level: str,
    explanation: str,
    notes: list[str],
    quiz_questions: list[dict[str, Any]],
    answer_key: list[str],
) -> LearningCycleModel:
    """
    Atomically creates the next learning cycle and increments session.current_cycle_number.
    """
    next_cycle_number = session.current_cycle_number + 1
    cycle = LearningCycleModel(
        session_id=session.id,
        cycle_number=next_cycle_number,
        difficulty_level=difficulty_level,
        explanation=explanation,
        notes=notes,
        quiz_questions=quiz_questions,
        answer_key=answer_key,
        status=CYCLE_STATUS_IN_PROGRESS,
    )
    session.current_cycle_number = next_cycle_number
    session.updated_at = utc_now()
    db.add(cycle)
    db.add(session)
    db.commit()
    db.refresh(cycle)
    db.refresh(session)
    return cycle


