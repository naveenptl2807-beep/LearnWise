"""
Unit tests for SessionModel and LearningCycleModel persistence, relational constraints,
and repository operations.
Covers uniqueness constraints, foreign key enforcement, restart persistence, and data privacy.
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

# Ensure project root is available in sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.database import Base, init_db, _enforce_sqlite_foreign_keys
from backend.models import (
    CYCLE_STATUS_IN_PROGRESS,
    CYCLE_STATUS_SUBMITTED,
    SESSION_STATUS_IN_PROGRESS,
    SESSION_STATUS_MASTERED,
    LearningCycleModel,
    SessionModel,
)
from backend.repository import (
    create_cycle,
    create_session,
    get_active_cycle,
    get_cycle,
    get_session,
    list_sessions,
    submit_cycle,
    update_session_difficulty,
)


class TestSessionAndCycleModels(unittest.TestCase):
    """Test suite for Session and Learning Cycle database operations."""

    def setUp(self):
        """Creates an isolated temporary SQLite database for each test run."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_persistence.db"
        self.db_url = f"sqlite:///{self.db_path.as_posix()}"

        self.engine = create_engine(
            self.db_url,
            connect_args={"check_same_thread": False},
        )
        event.listen(self.engine, "connect", _enforce_sqlite_foreign_keys)
        init_db(engine_override=self.engine)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

    def tearDown(self):
        """Cleans up the database engine and temporary file system."""
        self.engine.dispose()
        self.temp_dir.cleanup()

    def _sample_quiz(self) -> tuple[list[dict], list[str]]:
        """Helper generating 12 mock quiz questions and corresponding answer key."""
        questions = [
            {
                "question_index": i,
                "question": f"Sample Question {i+1}?",
                "options": ["Choice A", "Choice B", "Choice C", "Choice D"],
            }
            for i in range(12)
        ]
        answer_key = ["Choice A"] * 12
        return questions, answer_key

    def test_1_create_and_retrieve_session(self):
        """Verify creating and retrieving a session with correct initial state."""
        db = self.SessionLocal()
        try:
            session = create_session(db, topic="Python Memory Management", initial_difficulty="Beginner")
            self.assertTrue(session.id.startswith("sess_"))
            self.assertEqual(session.topic, "Python Memory Management")
            self.assertEqual(session.current_difficulty, "Beginner")
            self.assertEqual(session.status, SESSION_STATUS_IN_PROGRESS)
            self.assertEqual(session.current_cycle_number, 1)

            # Retrieve via repository
            fetched = get_session(db, session.id)
            self.assertIsNotNone(fetched)
            self.assertEqual(fetched.topic, "Python Memory Management")
            session_dict = fetched.to_dict()
            self.assertFalse(session_dict["is_mastered"])
            self.assertEqual(session_dict["session_id"], session.id)
        finally:
            db.close()

    def test_2_create_cycle_linked_to_session(self):
        """Verify creating a learning cycle linked to a parent session."""
        db = self.SessionLocal()
        try:
            session = create_session(db, topic="Binary Search Trees")
            questions, answer_key = self._sample_quiz()
            notes = ["Note 1: Logarithmic time", "Note 2: Left child smaller", "Note 3: Balanced trees"]

            cycle = create_cycle(
                db=db,
                session_id=session.id,
                cycle_number=1,
                difficulty_level="Beginner",
                explanation="A binary search tree is a node-based data structure...",
                notes=notes,
                quiz_questions=questions,
                answer_key=answer_key,
            )

            self.assertTrue(cycle.id.startswith("cycle_"))
            self.assertEqual(cycle.session_id, session.id)
            self.assertEqual(len(cycle.quiz_questions), 12)
            self.assertEqual(len(cycle.answer_key), 12)
            self.assertEqual(cycle.status, CYCLE_STATUS_IN_PROGRESS)

            # Check relationship from session
            db.refresh(session)
            self.assertEqual(len(session.cycles), 1)
            self.assertEqual(session.cycles[0].id, cycle.id)

            # Verify public dictionary NEVER exposes answer_key
            public_data = cycle.to_public_dict()
            self.assertNotIn("answer_key", public_data)
            self.assertIn("quiz", public_data)
            self.assertEqual(len(public_data["quiz"]), 12)
        finally:
            db.close()

    def test_3_reject_duplicate_cycle_numbers_for_same_session(self):
        """Verify uniqueness constraint on (session_id, cycle_number)."""
        db = self.SessionLocal()
        try:
            session = create_session(db, topic="Dynamic Programming")
            questions, answer_key = self._sample_quiz()

            create_cycle(
                db=db,
                session_id=session.id,
                cycle_number=1,
                difficulty_level="Beginner",
                explanation="Explanation 1",
                notes=["Note 1", "Note 2", "Note 3"],
                quiz_questions=questions,
                answer_key=answer_key,
            )

            # Attempt to create duplicate cycle #1 for the same session
            with self.assertRaises(IntegrityError):
                duplicate_cycle = LearningCycleModel(
                    session_id=session.id,
                    cycle_number=1,
                    difficulty_level="Beginner",
                    explanation="Explanation duplicate",
                    notes=["Note 1", "Note 2", "Note 3"],
                    quiz_questions=questions,
                    answer_key=answer_key,
                )
                db.add(duplicate_cycle)
                db.commit()
            db.rollback()
        finally:
            db.close()

    def test_4_preserve_data_after_reopening_connection(self):
        """Verify data persistence survives engine closing and reconnecting."""
        db = self.SessionLocal()
        session_id = None
        cycle_id = None
        try:
            session = create_session(db, topic="Graph Algorithms")
            questions, answer_key = self._sample_quiz()
            cycle = create_cycle(
                db=db,
                session_id=session.id,
                cycle_number=1,
                difficulty_level="Beginner",
                explanation="Graph representation",
                notes=["N1", "N2", "N3"],
                quiz_questions=questions,
                answer_key=answer_key,
            )
            session_id = session.id
            cycle_id = cycle.id
        finally:
            db.close()

        # Simulate full backend shutdown: close connections and dispose engine
        self.engine.dispose()

        # Reopen a brand-new engine pointing to the exact same SQLite file
        new_engine = create_engine(
            self.db_url,
            connect_args={"check_same_thread": False},
        )
        NewSessionLocal = sessionmaker(bind=new_engine)
        new_db = NewSessionLocal()
        try:
            persisted_session = new_db.query(SessionModel).filter_by(id=session_id).first()
            self.assertIsNotNone(persisted_session)
            self.assertEqual(persisted_session.topic, "Graph Algorithms")
            self.assertEqual(len(persisted_session.cycles), 1)

            persisted_cycle = new_db.query(LearningCycleModel).filter_by(id=cycle_id).first()
            self.assertIsNotNone(persisted_cycle)
            self.assertEqual(len(persisted_cycle.quiz_questions), 12)
            self.assertEqual(persisted_cycle.answer_key, ["Choice A"] * 12)
        finally:
            new_db.close()
            new_engine.dispose()

    def test_5_enforce_foreign_key_constraints(self):
        """Verify foreign key enforcement rejects cycles with invalid session_id."""
        db = self.SessionLocal()
        try:
            questions, answer_key = self._sample_quiz()
            orphan_cycle = LearningCycleModel(
                session_id="non_existent_sess_12345",
                cycle_number=1,
                difficulty_level="Beginner",
                explanation="Orphan cycle",
                notes=["N1", "N2", "N3"],
                quiz_questions=questions,
                answer_key=answer_key,
            )
            db.add(orphan_cycle)
            with self.assertRaises(IntegrityError):
                db.commit()
            db.rollback()
        finally:
            db.close()

    def test_6_preserve_existing_data_during_repeated_initialization(self):
        """Verify repeated init_db calls are idempotent and non-destructive."""
        db = self.SessionLocal()
        try:
            session = create_session(db, topic="Sorting Algorithms")
            session_id = session.id
        finally:
            db.close()

        # Re-run initialization 3 times (simulating restarts)
        init_db(engine_override=self.engine)
        init_db(engine_override=self.engine)
        init_db(engine_override=self.engine)

        db = self.SessionLocal()
        try:
            fetched = get_session(db, session_id)
            self.assertIsNotNone(fetched)
            self.assertEqual(fetched.topic, "Sorting Algorithms")
        finally:
            db.close()

    def test_7_handling_in_progress_and_mastered_session_statuses(self):
        """Verify progression transitions, score recording, and topic mastery state."""
        db = self.SessionLocal()
        try:
            session = create_session(db, topic="Concurrency and Asyncio", initial_difficulty="Advanced")
            self.assertEqual(session.status, SESSION_STATUS_IN_PROGRESS)
            self.assertFalse(session.to_dict()["is_mastered"])

            questions, answer_key = self._sample_quiz()
            cycle = create_cycle(
                db=db,
                session_id=session.id,
                cycle_number=1,
                difficulty_level="Advanced",
                explanation="Advanced event loop internals",
                notes=["N1", "N2", "N3"],
                quiz_questions=questions,
                answer_key=answer_key,
            )

            # Learner submits perfect score (100%) at Advanced
            submitted_answers = ["Choice A"] * 12
            graded_cycle = submit_cycle(
                db=db,
                cycle=cycle,
                submitted_answers=submitted_answers,
                score_percentage=100.0,
            )
            self.assertEqual(graded_cycle.status, CYCLE_STATUS_SUBMITTED)
            self.assertEqual(graded_cycle.score_percentage, 100.0)

            # Master topic
            updated_session = update_session_difficulty(
                db=db,
                session=session,
                next_difficulty="Advanced",
                is_mastered=True,
            )
            self.assertEqual(updated_session.status, SESSION_STATUS_MASTERED)
            self.assertTrue(updated_session.to_dict()["is_mastered"])
            # Current cycle number should remain 1 when mastered (no further cycles needed)
            self.assertEqual(updated_session.current_cycle_number, 1)
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()

