"""
Automated integration tests for quiz submission, adaptive progression, and topic mastery.
Tests:
- Accurate grading against server-side answer keys (100%, 0%, partial).
- Validation of submission payload (missing/extra answers, answers outside options).
- Server-side derivation of scores (client cannot inject fake scores or statuses).
- Rejection of duplicate submissions (HTTP 409).
- Adaptive difficulty progression:
  * Beginner 100% -> Intermediate (not mastered)
  * Intermediate 100% -> Advanced (not mastered)
  * Advanced 100% -> MASTERED
  * Advanced < 100% -> remains Advanced (not mastered)
- Next cycle generation enforcement:
  * Cannot generate next cycle before submitting current cycle (HTTP 409)
  * Cannot generate next cycle after mastery (HTTP 409)
  * Next cycle generated with updated difficulty and incremented cycle number
  * AI failure during next cycle generation produces HTTP 502 with no orphan cycle
- Inspection and privacy:
  * GET /api/sessions/{session_id} reflects submitted cycles, scores, and submitted answers
  * Answer keys are strictly excluded from public views before submission
- Convenience endpoint:
  * POST /api/sessions/{session_id}/submit operates on the active cycle
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
from backend.services.ai_service import AIServiceError


def _build_valid_mock_ai_output(topic: str = "Binary Search Trees", difficulty: str = "Beginner") -> dict:
    """Builds a compliant mock AI response containing 12 MCQs and 3 notes."""
    return {
        "topic": topic,
        "difficulty_level": difficulty,
        "explanation": f"Pedagogical explanation of {topic} for {difficulty} level.",
        "notes": [
            f"Concept 1 of {topic}.",
            f"Concept 2 of {topic}.",
            f"Concept 3 of {topic}.",
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


class TestQuizProgressionAndMastery(unittest.TestCase):
    """Test suite for quiz grading, difficulty progression, mastery, and next cycles."""

    def setUp(self):
        """Sets up an isolated SQLite database and test client for each test."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_progression.db")
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

    def _create_test_session(self, topic: str = "Binary Search Trees", initial_difficulty: str = "Beginner") -> dict:
        """Helper to create a session with mocked AI content."""
        with patch("backend.services.ai_service.generate_adaptive_content") as mock_ai:
            mock_ai.return_value = _build_valid_mock_ai_output(topic, initial_difficulty)
            response = self.client.post(
                "/api/sessions",
                json={"topic": topic, "initial_difficulty": initial_difficulty},
            )
            self.assertEqual(response.status_code, 201)
            return response.json()

    # 1. All 12 answers correct produces 100%
    def test_1_all_12_answers_correct_produces_100(self):
        """Verify submitting all 12 correct answers produces 100.0% score and 12 correct count."""
        session_data = self._create_test_session("Binary Search Trees", "Beginner")
        session_id = session_data["session_id"]

        # All Option iA (Correct)
        answers = [f"Option {i + 1}A (Correct)" for i in range(12)]
        response = self.client.post(
            f"/api/sessions/{session_id}/cycles/1/submit",
            json={"answers": answers},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["score_percentage"], 100.0)
        self.assertEqual(data["correct_count"], 12)
        self.assertEqual(data["total_questions"], 12)
        self.assertEqual(data["status"], "SUBMITTED")
        self.assertEqual(len(data["results"]), 12)
        for r in data["results"]:
            self.assertTrue(r["is_correct"])

    # 2. All answers wrong produces 0%
    def test_2_all_answers_wrong_produces_0(self):
        """Verify submitting all wrong answers produces 0.0% score and 0 correct count."""
        session_data = self._create_test_session("Binary Search Trees", "Beginner")
        session_id = session_data["session_id"]

        # All Option iB (Distractor)
        answers = [f"Option {i + 1}B (Distractor)" for i in range(12)]
        response = self.client.post(
            f"/api/sessions/{session_id}/cycles/1/submit",
            json={"answers": answers},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["score_percentage"], 0.0)
        self.assertEqual(data["correct_count"], 0)
        self.assertEqual(data["total_questions"], 12)
        for r in data["results"]:
            self.assertFalse(r["is_correct"])

    # 3. Partial score calculation correct
    def test_3_partial_score_calculation_correct(self):
        """Verify partial score calculation: 6/12 = 50.0% and 11/12 = 91.67%."""
        # Case A: 6 correct, 6 wrong -> 50.0%
        session_data_1 = self._create_test_session("Binary Search Trees", "Beginner")
        sess_id_1 = session_data_1["session_id"]
        answers_6 = [
            f"Option {i + 1}A (Correct)" if i < 6 else f"Option {i + 1}B (Distractor)"
            for i in range(12)
        ]
        resp_6 = self.client.post(f"/api/sessions/{sess_id_1}/cycles/1/submit", json={"answers": answers_6})
        self.assertEqual(resp_6.status_code, 200)
        self.assertEqual(resp_6.json()["score_percentage"], 50.0)
        self.assertEqual(resp_6.json()["correct_count"], 6)

        # Case B: 11 correct, 1 wrong -> 91.67%
        session_data_2 = self._create_test_session("Binary Search Trees", "Beginner")
        sess_id_2 = session_data_2["session_id"]
        answers_11 = [
            f"Option {i + 1}A (Correct)" if i < 11 else f"Option {i + 1}B (Distractor)"
            for i in range(12)
        ]
        resp_11 = self.client.post(f"/api/sessions/{sess_id_2}/cycles/1/submit", json={"answers": answers_11})
        self.assertEqual(resp_11.status_code, 200)
        self.assertEqual(resp_11.json()["score_percentage"], 91.67)
        self.assertEqual(resp_11.json()["correct_count"], 11)

    # 4. Answers not in options rejected
    def test_4_answers_not_in_options_rejected(self):
        """Verify submitting an answer not among the 4 options returns HTTP 422."""
        session_data = self._create_test_session("Binary Search Trees", "Beginner")
        session_id = session_data["session_id"]

        answers = [f"Option {i + 1}A (Correct)" for i in range(11)]
        answers.append("Invalid Non-Existent Option")

        response = self.client.post(
            f"/api/sessions/{session_id}/cycles/1/submit",
            json={"answers": answers},
        )
        self.assertEqual(response.status_code, 422)
        self.assertIn("not one of the available choices", response.json()["detail"])

    # 5. Missing or extra answers rejected
    def test_5_missing_or_extra_answers_rejected(self):
        """Verify submitting fewer than 12 or more than 12 answers returns HTTP 422."""
        session_data = self._create_test_session("Binary Search Trees", "Beginner")
        session_id = session_data["session_id"]

        # Only 11 answers
        response_11 = self.client.post(
            f"/api/sessions/{session_id}/cycles/1/submit",
            json={"answers": [f"Option {i + 1}A (Correct)" for i in range(11)]},
        )
        self.assertEqual(response_11.status_code, 422)

        # 13 answers
        answers_13 = [f"Option {i + 1}A (Correct)" for i in range(12)] + ["Extra Answer"]
        response_13 = self.client.post(
            f"/api/sessions/{session_id}/cycles/1/submit",
            json={"answers": answers_13},
        )
        self.assertEqual(response_13.status_code, 422)

    # 6. Client cannot submit fake score or answer key
    def test_6_client_cannot_submit_fake_score_or_answer_key(self):
        """Verify client-supplied score, mastery, or status fields in payload are ignored."""
        session_data = self._create_test_session("Binary Search Trees", "Beginner")
        session_id = session_data["session_id"]

        # 0 correct answers, but injecting fake score_percentage, is_mastered, status
        answers = [f"Option {i + 1}B (Distractor)" for i in range(12)]
        payload = {
            "answers": answers,
            "score_percentage": 100.0,
            "correct_count": 12,
            "is_mastered": True,
            "status": "MASTERED",
        }
        response = self.client.post(
            f"/api/sessions/{session_id}/cycles/1/submit",
            json=payload,
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # Trust only server evaluation
        self.assertEqual(data["score_percentage"], 0.0)
        self.assertEqual(data["correct_count"], 0)
        self.assertFalse(data["is_mastered"])
        self.assertEqual(data["status"], "SUBMITTED")

    # 7. Duplicate submission returns 409
    def test_7_duplicate_submission_returns_409(self):
        """Verify submitting quiz for an already submitted cycle returns HTTP 409 Conflict."""
        session_data = self._create_test_session("Binary Search Trees", "Beginner")
        session_id = session_data["session_id"]

        answers = [f"Option {i + 1}A (Correct)" for i in range(12)]
        resp1 = self.client.post(f"/api/sessions/{session_id}/cycles/1/submit", json={"answers": answers})
        self.assertEqual(resp1.status_code, 200)

        # Attempt to re-submit with wrong answers
        wrong_answers = [f"Option {i + 1}B (Distractor)" for i in range(12)]
        resp2 = self.client.post(f"/api/sessions/{session_id}/cycles/1/submit", json={"answers": wrong_answers})
        self.assertEqual(resp2.status_code, 409)
        self.assertIn("already been submitted", resp2.json()["detail"])

        # Check that original 100% score was not changed
        session_check = self.client.get(f"/api/sessions/{session_id}").json()
        self.assertEqual(session_check["cycles"][0]["score_percentage"], 100.0)

    # 8. Beginner 100% promotes to Intermediate, not mastered
    def test_8_beginner_100_percent_promotes_to_intermediate_not_mastered(self):
        """Verify 100% on Beginner promotes to Intermediate, session remains IN_PROGRESS."""
        session_data = self._create_test_session("Binary Search Trees", "Beginner")
        session_id = session_data["session_id"]

        answers = [f"Option {i + 1}A (Correct)" for i in range(12)]
        response = self.client.post(f"/api/sessions/{session_id}/cycles/1/submit", json={"answers": answers})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["next_difficulty"], "Intermediate")
        self.assertFalse(data["is_mastered"])
        self.assertEqual(data["next_step"]["action"], "FETCH_NEXT_CYCLE")

        # Verify session level updated in database
        session_get = self.client.get(f"/api/sessions/{session_id}").json()
        self.assertEqual(session_get["current_difficulty"], "Intermediate")
        self.assertEqual(session_get["status"], "IN_PROGRESS")
        self.assertFalse(session_get["is_mastered"])

    # 9. Intermediate 100% promotes to Advanced, not mastered
    def test_9_intermediate_100_percent_promotes_to_advanced_not_mastered(self):
        """Verify 100% on Intermediate promotes to Advanced, session remains IN_PROGRESS."""
        session_data = self._create_test_session("Binary Search Trees", "Intermediate")
        session_id = session_data["session_id"]

        answers = [f"Option {i + 1}A (Correct)" for i in range(12)]
        response = self.client.post(f"/api/sessions/{session_id}/cycles/1/submit", json={"answers": answers})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["next_difficulty"], "Advanced")
        self.assertFalse(data["is_mastered"])
        self.assertEqual(data["next_step"]["action"], "FETCH_NEXT_CYCLE")

        # Verify session level updated in database
        session_get = self.client.get(f"/api/sessions/{session_id}").json()
        self.assertEqual(session_get["current_difficulty"], "Advanced")
        self.assertEqual(session_get["status"], "IN_PROGRESS")
        self.assertFalse(session_get["is_mastered"])

    # 10. Advanced 100% marks session MASTERED
    def test_10_advanced_100_percent_marks_session_mastered(self):
        """Verify 100% on Advanced marks session as MASTERED with TOPIC_COMPLETED."""
        session_data = self._create_test_session("Binary Search Trees", "Advanced")
        session_id = session_data["session_id"]

        answers = [f"Option {i + 1}A (Correct)" for i in range(12)]
        response = self.client.post(f"/api/sessions/{session_id}/cycles/1/submit", json={"answers": answers})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["next_difficulty"], "Advanced")
        self.assertTrue(data["is_mastered"])
        self.assertEqual(data["next_step"]["action"], "TOPIC_COMPLETED")

        # Verify session state in database
        session_get = self.client.get(f"/api/sessions/{session_id}").json()
        self.assertEqual(session_get["status"], "MASTERED")
        self.assertTrue(session_get["is_mastered"])

    # 11. Advanced below 100% does not mark mastery
    def test_11_advanced_below_100_percent_does_not_mark_mastery(self):
        """Verify score below 100% on Advanced (e.g. 11/12) does not mark mastery."""
        session_data = self._create_test_session("Binary Search Trees", "Advanced")
        session_id = session_data["session_id"]

        answers = [
            f"Option {i + 1}A (Correct)" if i < 11 else f"Option {i + 1}B (Distractor)"
            for i in range(12)
        ]
        response = self.client.post(f"/api/sessions/{session_id}/cycles/1/submit", json={"answers": answers})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["score_percentage"], 91.67)
        self.assertFalse(data["is_mastered"])
        self.assertEqual(data["next_step"]["action"], "FETCH_NEXT_CYCLE")

        session_get = self.client.get(f"/api/sessions/{session_id}").json()
        self.assertEqual(session_get["status"], "IN_PROGRESS")
        self.assertFalse(session_get["is_mastered"])

    # 12. Next cycle cannot be generated before submission
    def test_12_next_cycle_cannot_be_generated_before_submission(self):
        """Verify calling POST /cycles before submitting current cycle returns HTTP 409."""
        session_data = self._create_test_session("Binary Search Trees", "Beginner")
        session_id = session_data["session_id"]

        response = self.client.post(f"/api/sessions/{session_id}/cycles")
        self.assertEqual(response.status_code, 409)
        self.assertIn("has not been submitted yet", response.json()["detail"])

    # 13. Next cycle uses correct difficulty and increments cycle number
    @patch("backend.services.ai_service.generate_adaptive_content")
    def test_13_next_cycle_uses_correct_difficulty_and_increments_cycle_number(self, mock_ai):
        """Verify next cycle generation uses promoted difficulty and increments cycle count."""
        mock_ai.return_value = _build_valid_mock_ai_output("Binary Search Trees", "Beginner")
        session_resp = self.client.post("/api/sessions", json={"topic": "Binary Search Trees"})
        session_id = session_resp.json()["session_id"]

        # Submit cycle 1 with 100% -> promoted to Intermediate
        answers = [f"Option {i + 1}A (Correct)" for i in range(12)]
        self.client.post(f"/api/sessions/{session_id}/cycles/1/submit", json={"answers": answers})

        # Mock AI output for cycle 2 at Intermediate
        mock_ai.return_value = _build_valid_mock_ai_output("Binary Search Trees", "Intermediate")

        next_cycle_resp = self.client.post(f"/api/sessions/{session_id}/cycles")
        self.assertEqual(next_cycle_resp.status_code, 201)
        next_data = next_cycle_resp.json()
        self.assertEqual(next_data["current_cycle_number"], 2)
        self.assertEqual(next_data["current_difficulty"], "Intermediate")
        self.assertEqual(next_data["cycle"]["cycle_number"], 2)
        self.assertEqual(next_data["cycle"]["difficulty_level"], "Intermediate")

        # Verify AI function was called with Intermediate
        mock_ai.assert_called_with(
            topic="Binary Search Trees",
            difficulty="Intermediate",
            api_key=None,
            model_name="gemini-3.5-flash-lite",
        )

    # 14. No cycle can be generated after mastery
    def test_14_no_cycle_can_be_generated_after_mastery(self):
        """Verify calling POST /cycles on a MASTERED session returns HTTP 409."""
        session_data = self._create_test_session("Binary Search Trees", "Advanced")
        session_id = session_data["session_id"]

        # Submit with 100% to achieve mastery
        answers = [f"Option {i + 1}A (Correct)" for i in range(12)]
        self.client.post(f"/api/sessions/{session_id}/cycles/1/submit", json={"answers": answers})

        # Attempt to generate next cycle
        response = self.client.post(f"/api/sessions/{session_id}/cycles")
        self.assertEqual(response.status_code, 409)
        self.assertIn("already mastered", response.json()["detail"])

    # 15. AI generation failure creates no orphan cycle
    @patch("backend.services.ai_service.generate_adaptive_content")
    def test_15_ai_generation_failure_creates_no_orphan_cycle(self, mock_ai):
        """Verify AI failure during next cycle generation returns 502 without orphan cycles."""
        mock_ai.return_value = _build_valid_mock_ai_output("Binary Search Trees", "Beginner")
        session_resp = self.client.post("/api/sessions", json={"topic": "Binary Search Trees"})
        session_id = session_resp.json()["session_id"]

        # Submit cycle 1
        answers = [f"Option {i + 1}A (Correct)" for i in range(12)]
        self.client.post(f"/api/sessions/{session_id}/cycles/1/submit", json={"answers": answers})

        # Mock AI to fail on next cycle generation
        mock_ai.side_effect = Exception("Upstream AI model quota exceeded")

        fail_resp = self.client.post(f"/api/sessions/{session_id}/cycles")
        self.assertEqual(fail_resp.status_code, 502)

        # Check database: session current_cycle_number is still 1, exactly 1 cycle exists
        session_data = self.client.get(f"/api/sessions/{session_id}").json()
        self.assertEqual(session_data["current_cycle_number"], 1)
        self.assertEqual(len(session_data["cycles"]), 1)

    # 16. Session retrieval reports cycle status and scores
    @patch("backend.services.ai_service.generate_adaptive_content")
    def test_16_session_retrieval_reports_cycle_status_and_scores(self, mock_ai):
        """Verify GET /api/sessions/{id} returns submitted cycles with scores and active cycle unsubmitted."""
        mock_ai.return_value = _build_valid_mock_ai_output("Binary Search Trees", "Beginner")
        session_resp = self.client.post("/api/sessions", json={"topic": "Binary Search Trees"})
        session_id = session_resp.json()["session_id"]

        # Submit cycle 1
        answers = [f"Option {i + 1}A (Correct)" for i in range(12)]
        self.client.post(f"/api/sessions/{session_id}/cycles/1/submit", json={"answers": answers})

        # Generate cycle 2
        mock_ai.return_value = _build_valid_mock_ai_output("Binary Search Trees", "Intermediate")
        self.client.post(f"/api/sessions/{session_id}/cycles")

        # Retrieve full session
        session_detail = self.client.get(f"/api/sessions/{session_id}").json()
        self.assertEqual(len(session_detail["cycles"]), 2)

        cycle_1 = session_detail["cycles"][0]
        self.assertEqual(cycle_1["cycle_number"], 1)
        self.assertEqual(cycle_1["status"], "SUBMITTED")
        self.assertEqual(cycle_1["score_percentage"], 100.0)
        self.assertIsNotNone(cycle_1["submitted_answers"])
        self.assertIsNotNone(cycle_1["submitted_at"])

        cycle_2 = session_detail["cycles"][1]
        self.assertEqual(cycle_2["cycle_number"], 2)
        self.assertEqual(cycle_2["status"], "IN_PROGRESS")
        self.assertIsNone(cycle_2["score_percentage"])
        self.assertIsNone(cycle_2["submitted_answers"])
        self.assertIsNone(cycle_2["submitted_at"])

    # 17. Answer keys remain private before submission
    @patch("backend.services.ai_service.generate_adaptive_content")
    def test_17_answer_keys_remain_private_before_submission(self, mock_ai):
        """Verify neither answer_key nor correct_answer is exposed in unsubmitted cycles."""
        mock_ai.return_value = _build_valid_mock_ai_output("Binary Search Trees", "Beginner")
        create_resp = self.client.post("/api/sessions", json={"topic": "Binary Search Trees"})
        data = create_resp.json()
        session_id = data["session_id"]

        # 1. Check create response
        cycle_data = data["cycle"]
        self.assertNotIn("answer_key", cycle_data)
        for q in cycle_data["quiz"]:
            self.assertNotIn("correct_answer", q)

        # 2. Check get session response before submit
        detail_resp = self.client.get(f"/api/sessions/{session_id}").json()
        for q in detail_resp["cycles"][0]["quiz"]:
            self.assertNotIn("correct_answer", q)
        self.assertNotIn("answer_key", detail_resp["cycles"][0])

    # 18. Active cycle submit shortcut
    def test_18_active_cycle_submit_shortcut(self):
        """Verify POST /api/sessions/{session_id}/submit operates on the active cycle."""
        session_data = self._create_test_session("Binary Search Trees", "Beginner")
        session_id = session_data["session_id"]

        # Submit via shortcut without cycle number in path
        answers = [f"Option {i + 1}A (Correct)" for i in range(12)]
        response = self.client.post(
            f"/api/sessions/{session_id}/submit",
            json={"answers": answers},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["cycle_number"], 1)
        self.assertEqual(data["score_percentage"], 100.0)
        self.assertEqual(data["status"], "SUBMITTED")


if __name__ == "__main__":
    unittest.main()
