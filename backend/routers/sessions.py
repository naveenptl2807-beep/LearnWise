"""
API router for session management, quiz submission, and adaptive progression.
Provides endpoints for starting learning sessions, submitting cycle quizzes,
generating next cycles, and retrieving session history.
"""

from typing import Any, Union
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ai_module.difficulty import LEVEL_ORDER, calculate_next_level
from backend.database import get_db
from backend.models import (
    CYCLE_STATUS_IN_PROGRESS,
    CYCLE_STATUS_SUBMITTED,
    SESSION_STATUS_IN_PROGRESS,
    SESSION_STATUS_MASTERED,
)
from backend.repository import (
    create_next_cycle,
    create_session_with_initial_cycle,
    get_cycle,
    get_session,
    grade_and_submit_cycle,
    list_sessions,
)
from backend.schemas import (
    AnswerItem,
    NextStepInfo,
    QuestionResultItem,
    QuizSubmissionRequest,
    QuizSubmissionResponse,
    SessionCreateRequest,
    SessionCreateResponse,
    SessionDetailResponse,
    SessionSummaryItem,
)
from backend.services.ai_service import AIServiceError, generate_and_validate_cycle_content

router = APIRouter(prefix="/api/sessions", tags=["Sessions"])


@router.post(
    "",
    response_model=SessionCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new learning session",
)
def create_session(
    payload: SessionCreateRequest,
    db: Session = Depends(get_db),
) -> SessionCreateResponse:
    """
    Creates a new learning session and generates the first learning cycle.
    Validates input, invokes the AI module, persists the cycle and answer key,
    and returns sanitized public learning content.
    """
    initial_difficulty = payload.initial_difficulty or "Beginner"

    # Step 1: Generate & strictly validate learning cycle via AI module
    try:
        explanation, notes, quiz_questions, answer_key = (
            generate_and_validate_cycle_content(
                topic=payload.topic,
                difficulty_level=initial_difficulty,
            )
        )
    except AIServiceError as err:
        # Provider or schema validation failure: return 502 without creating an orphan session
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(err),
        ) from err

    # Step 2: Persist session and initial cycle in a single transaction
    try:
        session, cycle = create_session_with_initial_cycle(
            db=db,
            topic=payload.topic,
            difficulty_level=initial_difficulty,
            explanation=explanation,
            notes=notes,
            quiz_questions=quiz_questions,
            answer_key=answer_key,
        )
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to persist learning session in database.",
        ) from exc

    return SessionCreateResponse(
        session_id=session.id,
        topic=session.topic,
        current_difficulty=session.current_difficulty,
        status=session.status,
        is_mastered=session.status == SESSION_STATUS_MASTERED,
        current_cycle_number=session.current_cycle_number,
        cycle=cycle.to_public_dict(),
    )


@router.post(
    "/{session_id}/cycles/{cycle_number}/submit",
    response_model=QuizSubmissionResponse,
    summary="Submit quiz answers for a specific cycle",
)
def submit_cycle_quiz(
    session_id: str,
    cycle_number: int,
    payload: QuizSubmissionRequest,
    db: Session = Depends(get_db),
) -> QuizSubmissionResponse:
    """
    Submits and grades quiz answers for the specified learning cycle.
    Evaluates submitted answers against the trusted server-side answer key,
    computes score percentage, updates pedagogical progression via calculate_next_level,
    and determines topic mastery.
    """
    # 1. Fetch and validate session and cycle existence
    session = get_session(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )

    cycle = get_cycle(db, session_id, cycle_number)
    if not cycle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cycle {cycle_number} not found for session '{session_id}'.",
        )

    # 2. Prevent duplicate submissions on an already-graded cycle
    if cycle.status == CYCLE_STATUS_SUBMITTED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cycle {cycle_number} has already been submitted.",
        )

    if session.status == SESSION_STATUS_MASTERED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Session is already mastered. No further quiz submissions allowed.",
        )

    # 3. Normalize submitted answers into a strictly ordered list of 12 strings
    raw_answers = payload.answers
    submitted_choices: list[str] = [None] * 12

    has_indexed_items = any(isinstance(a, AnswerItem) or (isinstance(a, dict) and "question_index" in a) for a in raw_answers)

    if has_indexed_items:
        seen_indices = set()
        for item in raw_answers:
            if isinstance(item, AnswerItem):
                q_idx = item.question_index
                val = item.selected_option
            elif isinstance(item, dict):
                q_idx = item.get("question_index")
                val = item.get("selected_option", "")
            else:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Mixed answer formats detected. Provide either all indexed objects or an ordered list.",
                )

            if q_idx is None or not (0 <= q_idx <= 11):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Question index {q_idx} is out of bounds (must be between 0 and 11).",
                )
            if q_idx in seen_indices:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Duplicate answer provided for question index {q_idx}.",
                )
            seen_indices.add(q_idx)
            submitted_choices[q_idx] = str(val).strip()

        if len(seen_indices) != 12:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Expected answers for all 12 questions, but received {len(seen_indices)} unique indices.",
            )
    else:
        for idx, item in enumerate(raw_answers):
            val = item.selected_option if isinstance(item, AnswerItem) else str(item)
            submitted_choices[idx] = val.strip()

    # 4. Validate that each chosen option belongs to the question's available options
    quiz_questions = cycle.quiz_questions
    for idx, chosen in enumerate(submitted_choices):
        valid_options = quiz_questions[idx]["options"]
        if chosen not in valid_options:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Selected option '{chosen}' for question {idx} is not one of the available choices: {valid_options}",
            )

    # 5. Grade answers against the trusted server-side answer key
    answer_key = cycle.answer_key
    correct_count = 0
    results: list[QuestionResultItem] = []

    for idx in range(12):
        is_correct = (submitted_choices[idx] == answer_key[idx])
        if is_correct:
            correct_count += 1
        results.append(
            QuestionResultItem(
                question_index=idx,
                question=quiz_questions[idx]["question"],
                selected_option=submitted_choices[idx],
                correct_answer=answer_key[idx],
                is_correct=is_correct,
            )
        )

    score_percentage = round((correct_count / 12.0) * 100.0, 2)

    # 6. Apply difficulty progression & mastery policy
    next_difficulty = calculate_next_level(
        current_level=cycle.difficulty_level,
        score_percentage=score_percentage,
    )
    is_mastered = (cycle.difficulty_level == "Advanced" and score_percentage == 100.0)

    # 7. Persist evaluation and progression in an atomic transaction
    try:
        session, cycle = grade_and_submit_cycle(
            db=db,
            session=session,
            cycle=cycle,
            submitted_answers=submitted_choices,
            score_percentage=score_percentage,
            next_difficulty=next_difficulty,
            is_mastered=is_mastered,
        )
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record quiz submission in database.",
        ) from exc

    # 8. Construct user feedback & next step descriptor
    if is_mastered:
        feedback = (
            f"Mastery Achieved! You achieved a perfect score of 100% on an Advanced cycle. "
            f"Topic '{session.topic}' is now fully mastered!"
        )
        next_step = NextStepInfo(
            action="TOPIC_COMPLETED",
            message="Topic mastered. No further learning cycles required.",
        )
    else:
        if next_difficulty != cycle.difficulty_level:
            if LEVEL_ORDER.index(next_difficulty) > LEVEL_ORDER.index(cycle.difficulty_level):
                feedback = (
                    f"Outstanding! You scored {score_percentage}% ({correct_count}/12). "
                    f"You have been promoted to {next_difficulty} difficulty."
                )
            else:
                feedback = (
                    f"You scored {score_percentage}% ({correct_count}/12). "
                    f"Stepping down to {next_difficulty} difficulty for concept reinforcement."
                )
        else:
            feedback = (
                f"Good effort! You scored {score_percentage}% ({correct_count}/12). "
                f"Maintaining {next_difficulty} difficulty for additional practice."
            )

        next_step = NextStepInfo(
            action="FETCH_NEXT_CYCLE",
            message=f"Proceed to generate cycle {session.current_cycle_number + 1} at {next_difficulty} difficulty.",
            endpoint=f"/api/sessions/{session.id}/cycles",
            method="POST",
        )

    return QuizSubmissionResponse(
        session_id=session.id,
        cycle_number=cycle.cycle_number,
        difficulty_level=cycle.difficulty_level,
        score_percentage=score_percentage,
        correct_count=correct_count,
        total_questions=12,
        next_difficulty=next_difficulty,
        is_mastered=is_mastered,
        status=cycle.status,
        feedback=feedback,
        results=results,
        next_step=next_step,
    )


@router.post(
    "/{session_id}/submit",
    response_model=QuizSubmissionResponse,
    summary="Submit quiz answers for the active cycle",
)
def submit_active_cycle_quiz(
    session_id: str,
    payload: QuizSubmissionRequest,
    db: Session = Depends(get_db),
) -> QuizSubmissionResponse:
    """
    Convenience endpoint delegating submission to the session's active cycle.
    """
    session = get_session(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )
    return submit_cycle_quiz(
        session_id=session_id,
        cycle_number=session.current_cycle_number,
        payload=payload,
        db=db,
    )


@router.post(
    "/{session_id}/cycles",
    response_model=SessionCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate the next adaptive learning cycle",
)
def generate_next_cycle_endpoint(
    session_id: str,
    db: Session = Depends(get_db),
) -> SessionCreateResponse:
    """
    Explicitly triggers generation of the next adaptive cycle.
    Permitted only after the current cycle's quiz has been submitted.
    Uses the next difficulty determined by the difficulty progression engine.
    """
    session = get_session(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )

    # 1. Reject generation if session is already mastered
    if session.status == SESSION_STATUS_MASTERED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Session is already mastered. No further learning cycles can be generated.",
        )

    # 2. Ensure current cycle was submitted before allowing advancement
    current_cycle = get_cycle(db, session_id, session.current_cycle_number)
    if not current_cycle or current_cycle.status != CYCLE_STATUS_SUBMITTED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cycle {session.current_cycle_number} has not been submitted yet. Please complete the quiz before generating the next cycle.",
        )

    target_cycle_number = session.current_cycle_number + 1
    existing_next = get_cycle(db, session_id, target_cycle_number)
    if existing_next:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cycle {target_cycle_number} has already been generated.",
        )

    # 3. Generate & strictly validate next cycle content via AI module
    try:
        explanation, notes, quiz_questions, answer_key = (
            generate_and_validate_cycle_content(
                topic=session.topic,
                difficulty_level=session.current_difficulty,
            )
        )
    except AIServiceError as err:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(err),
        ) from err

    # 4. Atomically persist new cycle and advance session current_cycle_number
    try:
        new_cycle = create_next_cycle(
            db=db,
            session=session,
            difficulty_level=session.current_difficulty,
            explanation=explanation,
            notes=notes,
            quiz_questions=quiz_questions,
            answer_key=answer_key,
        )
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to persist next learning cycle.",
        ) from exc

    return SessionCreateResponse(
        session_id=session.id,
        topic=session.topic,
        current_difficulty=session.current_difficulty,
        status=session.status,
        is_mastered=False,
        current_cycle_number=session.current_cycle_number,
        cycle=new_cycle.to_public_dict(),
    )


@router.get(
    "/{session_id}",
    response_model=SessionDetailResponse,
    summary="Get session details and cycles",
)
def get_session_details(
    session_id: str,
    db: Session = Depends(get_db),
) -> SessionDetailResponse:
    """
    Retrieves a session's current state and its learning cycles in ascending cycle-number order.
    Excludes private answer keys from public serialization.
    """
    session = get_session(db, session_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session '{session_id}' not found.",
        )

    # Cycles are automatically ordered by cycle_number ascending via relationship
    public_cycles = [cycle.to_public_dict() for cycle in session.cycles]

    return SessionDetailResponse(
        session_id=session.id,
        topic=session.topic,
        current_difficulty=session.current_difficulty,
        status=session.status,
        is_mastered=session.status == SESSION_STATUS_MASTERED,
        current_cycle_number=session.current_cycle_number,
        created_at=session.created_at.isoformat() if session.created_at else None,
        updated_at=session.updated_at.isoformat() if session.updated_at else None,
        cycles=public_cycles,
    )


@router.get(
    "",
    response_model=list[SessionSummaryItem],
    summary="List all learning sessions",
)
def list_all_sessions(
    db: Session = Depends(get_db),
) -> list[SessionSummaryItem]:
    """
    Lists all saved learning sessions for resumption and history inspection.
    """
    sessions = list_sessions(db)
    return [
        SessionSummaryItem(
            session_id=s.id,
            topic=s.topic,
            current_difficulty=s.current_difficulty,
            status=s.status,
            is_mastered=s.status == SESSION_STATUS_MASTERED,
            current_cycle_number=s.current_cycle_number,
            created_at=s.created_at.isoformat() if s.created_at else None,
            updated_at=s.updated_at.isoformat() if s.updated_at else None,
        )
        for s in sessions
    ]
