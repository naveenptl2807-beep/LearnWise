"""
Automated integration tests for session endpoints and AI module integration.
Tests POST /api/sessions, GET /api/sessions/{session_id}, validation rules,
error handling on AI failures, and public/private data separation.
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

# Ensure project root is available in sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.database import Base, get_db, init_db, _enforce_sqlite_foreign_keys
from backend.main import app
from backend.models import LearningCycleModel, SessionModel


def _build_valid_mock_ai_output(topic: str = "Binary Search Trees", difficulty: str = "Beginner") -> dict:
    """Builds a compliant mock AI response containing 12 MCQs and 3 notes."""
    return {
        "topic": topic,
        "difficulty_level": difficulty,
        "explanation": f"In-depth pedagogical explanation of {topic} tailored to {difficulty} learners.",
        "notes": [
            f"Key concept 1 of {topic}.",
            f"Key concept 2 of {topic}.",
            f"Key concept 3 of {topic}.",
        ],
        "quiz": [
            {
                "question": f"Question {i + 1} regarding {topic}?",
                "options": [
                    f"Option {i + 1}A (Correct)",
                    f"Option {i + 1}B (Distractor)",
                    f"Option {i + 1}C (Distractor)",
                    f"Option {i + 1}D (Distractor)",
                ],
                "correct_answer": f"Option {i + 1}A (Correct)",
            }
            for i in range(12)
        ],
    }


class TestSessionEndpoints(unittest.TestCase):
    """Test suite for /api/sessions routes and AI integration."""

    def setUp(self):
        """Sets up an isolated SQLite database and test client for each test."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_sessions.db")
        self.db_url = f"sqlite:///{self.db_path.replace(os.sep, '/')}"

        self.test_engine = create_engine(
            self.db_url,
            connect_args={"check_same_thread": False},
        )
        event.listen(self.test_engine, "connect", _enforce_sqlite_foreign_keys)
        init_db(engine_override=self.test_engine)
        self.TestingSessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.test_engine
        )

        def override_get_db():
            db = self.TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()

        app.dependency_overrides[get_db] = override_get_db
        self.client = TestClient(app)

    def tearDown(self):
        """Cleans up dependency overrides and test database files."""
        app.dependency_overrides.clear()
        self.test_engine.dispose()
        self.temp_dir.cleanup()

    @patch("backend.services.ai_service.generate_adaptive_content")
    def test_session_creation_success(self, mock_ai_call):
        """Verify POST /api/sessions creates a session and cycle #1 with 12 MCQs."""
        mock_ai_call.return_value = _build_valid_mock_ai_output("Binary Search Trees", "Beginner")

        response = self.client.post("/api/sessions", json={"topic": "Binary Search Trees"})
        self.assertEqual(response.status_code, 201)

        data = response.json()
        self.assertTrue(data["session_id"].startswith("sess_"))
        self.assertEqual(data["topic"], "Binary Search Trees")
        self.assertEqual(data["current_difficulty"], "Beginner")
        self.assertEqual(data["status"], "IN_PROGRESS")
        self.assertFalse(data["is_mastered"])
        self.assertEqual(data["current_cycle_number"], 1)

        cycle = data["cycle"]
        self.assertEqual(cycle["cycle_number"], 1)
        self.assertEqual(cycle["difficulty_level"], "Beginner")
        self.assertEqual(cycle["status"], "IN_PROGRESS")
        self.assertTrue(len(cycle["explanation"]) > 0)
        self.assertEqual(len(cycle["notes"]), 3)
        self.assertEqual(len(cycle["quiz"]), 12)

    @patch("backend.services.ai_service.generate_adaptive_content")
    def test_session_creation_default_difficulty(self, mock_ai_call):
        """Verify omitting initial_difficulty defaults to 'Beginner'."""
        mock_ai_call.return_value = _build_valid_mock_ai_output("Python Decorators", "Beginner")

        response = self.client.post("/api/sessions", json={"topic": "Python Decorators"})
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["current_difficulty"], "Beginner")
        self.assertEqual(data["cycle"]["difficulty_level"], "Beginner")
        # Verify AI module was called with Beginner
        mock_ai_call.assert_called_once()
        self.assertEqual(mock_ai_call.call_args[1]["difficulty"], "Beginner")

    @patch("backend.services.ai_service.generate_adaptive_content")
    def test_session_creation_explicit_difficulty(self, mock_ai_call):
        """Verify initial_difficulty can be explicitly set to 'Advanced'."""
        mock_ai_call.return_value = _build_valid_mock_ai_output("Concurrency Models", "Advanced")

        response = self.client.post(
            "/api/sessions",
            json={"topic": "Concurrency Models", "initial_difficulty": "Advanced"},
        )
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertEqual(data["current_difficulty"], "Advanced")
        self.assertEqual(data["cycle"]["difficulty_level"], "Advanced")
        self.assertEqual(mock_ai_call.call_args[1]["difficulty"], "Advanced")

    def test_blank_and_whitespace_topic_rejected(self):
        """Verify empty and whitespace-only topics return HTTP 422."""
        for invalid_topic in ["", "   ", "\t\n"]:
            response = self.client.post("/api/sessions", json={"topic": invalid_topic})
            self.assertEqual(response.status_code, 422)

    def test_invalid_difficulty_rejected(self):
        """Verify unsupported difficulty strings return HTTP 422."""
        response = self.client.post(
            "/api/sessions",
            json={"topic": "Algorithms", "initial_difficulty": "Master"},
        )
        self.assertEqual(response.status_code, 422)

    def test_unknown_session_id_returns_404(self):
        """Verify GET /api/sessions/{session_id} returns 404 for unknown IDs."""
        response = self.client.get("/api/sessions/sess_non_existent_12345")
        self.assertEqual(response.status_code, 404)
        self.assertIn("not found", response.json()["detail"].lower())

    @patch("backend.services.ai_service.generate_adaptive_content")
    def test_get_session_returns_cycles_in_correct_order(self, mock_ai_call):
        """Verify GET /api/sessions/{id} returns learning cycles in ascending cycle_number order."""
        mock_ai_call.return_value = _build_valid_mock_ai_output("Operating Systems", "Beginner")
        post_resp = self.client.post("/api/sessions", json={"topic": "Operating Systems"})
        session_id = post_resp.json()["session_id"]

        # Insert cycle #2 manually in the database
        db = self.TestingSessionLocal()
        try:
            cycle2 = LearningCycleModel(
                session_id=session_id,
                cycle_number=2,
                difficulty_level="Intermediate",
                explanation="Intermediate operating system concepts",
                notes=["Process vs Thread", "Context switches", "Scheduling algorithms"],
                quiz_questions=[{"question_index": i, "question": f"Q{i}", "options": ["A", "B", "C", "D"]} for i in range(12)],
                answer_key=["A"] * 12,
                status="IN_PROGRESS",
            )
            db.add(cycle2)
            db.commit()
        finally:
            db.close()

        # Fetch session
        get_resp = self.client.get(f"/api/sessions/{session_id}")
        self.assertEqual(get_resp.status_code, 200)
        data = get_resp.json()
        self.assertEqual(data["session_id"], session_id)
        self.assertEqual(len(data["cycles"]), 2)
        self.assertEqual(data["cycles"][0]["cycle_number"], 1)
        self.assertEqual(data["cycles"][1]["cycle_number"], 2)

    @patch("backend.services.ai_service.generate_adaptive_content")
    def test_exactly_12_public_mcqs_with_4_options_each(self, mock_ai_call):
        """Verify each public cycle quiz contains exactly 12 questions with 4 options each."""
        mock_ai_call.return_value = _build_valid_mock_ai_output("Sorting Algorithms", "Beginner")
        response = self.client.post("/api/sessions", json={"topic": "Sorting Algorithms"})
        self.assertEqual(response.status_code, 201)

        quiz = response.json()["cycle"]["quiz"]
        self.assertEqual(len(quiz), 12)
        for idx, question in enumerate(quiz):
            self.assertEqual(question["question_index"], idx)
            self.assertTrue(len(question["question"]) > 0)
            self.assertEqual(len(question["options"]), 4)
            self.assertEqual(len(set(question["options"])), 4)

    @patch("backend.services.ai_service.generate_adaptive_content")
    def test_correct_answers_never_appear_in_responses(self, mock_ai_call):
        """Verify neither 'correct_answer' nor 'answer_key' is ever exposed in API responses."""
        mock_ai_call.return_value = _build_valid_mock_ai_output("Data Structures", "Beginner")

        # 1. Check POST /api/sessions response
        post_resp = self.client.post("/api/sessions", json={"topic": "Data Structures"})
        self.assertEqual(post_resp.status_code, 201)
        post_text = post_resp.text
        self.assertNotIn("correct_answer", post_text)
        self.assertNotIn("answer_key", post_text)

        session_id = post_resp.json()["session_id"]

        # 2. Check GET /api/sessions/{id} response
        get_resp = self.client.get(f"/api/sessions/{session_id}")
        self.assertEqual(get_resp.status_code, 200)
        get_text = get_resp.text
        self.assertNotIn("correct_answer", get_text)
        self.assertNotIn("answer_key", get_text)

    @patch("backend.services.ai_service.generate_adaptive_content")
    def test_ai_provider_failure_produces_safe_error_and_no_orphan_session(self, mock_ai_call):
        """Verify AI failure produces HTTP 502 with safe detail and creates zero orphan sessions."""
        mock_ai_call.side_effect = RuntimeError("Gemini API request failed: [REDACTED]")

        response = self.client.post("/api/sessions", json={"topic": "Network Protocols"})
        self.assertEqual(response.status_code, 502)

        # Verify no sensitive information leaked
        detail = response.json().get("detail", "")
        self.assertNotIn("GEMINI_API_KEY", detail)

        # Verify no session was persisted in the database
        db = self.TestingSessionLocal()
        try:
            count = db.query(SessionModel).count()
            self.assertEqual(count, 0, "No orphan session should be persisted when AI generation fails.")
        finally:
            db.close()

    @patch("backend.services.ai_service.generate_adaptive_content")
    def test_invalid_ai_output_handled_safely(self, mock_ai_call):
        """Verify malformed AI output (e.g., only 10 questions) returns 502 without orphan session."""
        bad_output = _build_valid_mock_ai_output("Faulty AI Topic", "Beginner")
        bad_output["quiz"] = bad_output["quiz"][:10]  # Only 10 questions instead of required 12
        mock_ai_call.return_value = bad_output

        response = self.client.post("/api/sessions", json={"topic": "Faulty AI Topic"})
        self.assertEqual(response.status_code, 502)
        self.assertIn("12", response.json().get("detail", ""))

        # Verify no orphan session
        db = self.TestingSessionLocal()
        try:
            count = db.query(SessionModel).count()
            self.assertEqual(count, 0)
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()

