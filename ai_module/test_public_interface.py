import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ai_module.adaptive_tutor import generate_adaptive_content, calculate_next_level
from ai_module.schemas import LearningModule, QuizQuestion


class TestPublicInterface(unittest.TestCase):
    def setUp(self):
        # 12 valid mock quiz questions
        self.mock_questions = [
            QuizQuestion(
                question=f"What is concept {i}?",
                options=[f"Choice {i}A", f"Choice {i}B", f"Choice {i}C", f"Choice {i}D"],
                correct_answer=f"Choice {i}A"
            )
            for i in range(1, 13)
        ]
        self.mock_module = LearningModule(
            topic="Dynamic Programming",
            difficulty_level="Intermediate",
            explanation="Dynamic Programming is an optimization technique using memoization and tabulation.",
            notes=[
                "Optimal substructure is required.",
                "Overlapping subproblems allow caching.",
                "Can be implemented top-down or bottom-up."
            ],
            quiz=self.mock_questions
        )

    @patch("ai_module.adaptive_tutor.GeminiService")
    def test_successful_generate_adaptive_content_returns_dict(self, mock_service_cls):
        """Test that generate_adaptive_content returns a valid, FastAPI-ready dictionary."""
        mock_service_instance = MagicMock()
        mock_service_cls.return_value = mock_service_instance
        mock_service_instance.generate_learning_module.return_value = self.mock_module

        result = generate_adaptive_content("Dynamic Programming", "Intermediate", api_key="dummy_key")

        # Verify output is a pure Python dictionary
        self.assertIsInstance(result, dict)
        self.assertEqual(result["topic"], "Dynamic Programming")
        self.assertEqual(result["difficulty_level"], "Intermediate")
        self.assertTrue(isinstance(result["explanation"], str) and len(result["explanation"]) > 0)
        self.assertEqual(len(result["notes"]), 3)
        self.assertEqual(len(result["quiz"]), 12)

        # Verify quiz questions format
        for q in result["quiz"]:
            self.assertIsInstance(q, dict)
            self.assertIn("question", q)
            self.assertIn("options", q)
            self.assertIn("correct_answer", q)
            self.assertEqual(len(q["options"]), 4)
            self.assertEqual(len(set(q["options"])), 4)
            self.assertIn(q["correct_answer"], q["options"])

    def test_invalid_topic_raises_value_error(self):
        """Test that empty or non-string topics raise a descriptive ValueError."""
        with self.assertRaises(ValueError) as ctx:
            generate_adaptive_content("", "Beginner")
        self.assertIn("Topic must be a non-empty string", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            generate_adaptive_content("   ", "Beginner")
        self.assertIn("Topic must be a non-empty string", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            generate_adaptive_content(None, "Beginner")
        self.assertIn("Topic must be a non-empty string", str(ctx.exception))

    def test_invalid_difficulty_raises_value_error(self):
        """Test that invalid difficulty level raises a descriptive ValueError."""
        with self.assertRaises(ValueError) as ctx:
            generate_adaptive_content("Recursion", "Expert")
        self.assertIn("Invalid difficulty 'Expert'", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            generate_adaptive_content("Recursion", "beginner")  # Lowercase unapproved
        self.assertIn("Invalid difficulty 'beginner'", str(ctx.exception))

    @patch("ai_module.adaptive_tutor.GeminiService")
    def test_api_error_propagation(self, mock_service_cls):
        """Test that API communication errors are cleanly propagated without leaking secrets."""
        mock_service_instance = MagicMock()
        mock_service_cls.return_value = mock_service_instance
        mock_service_instance.generate_learning_module.side_effect = RuntimeError(
            "Gemini API request failed: 503 UNAVAILABLE"
        )

        with self.assertRaises(RuntimeError) as ctx:
            generate_adaptive_content("Hash Tables", "Beginner", api_key="dummy_key")
        self.assertIn("Gemini API request failed", str(ctx.exception))

    def test_adaptive_difficulty_progression_logic(self):
        """Test calculation of next difficulty level based on quiz score percentage."""
        # Scale up (Score >= 80%)
        self.assertEqual(calculate_next_level("Beginner", 80.0), "Intermediate")
        self.assertEqual(calculate_next_level("Beginner", 100.0), "Intermediate")
        self.assertEqual(calculate_next_level("Intermediate", 90.0), "Advanced")
        self.assertEqual(calculate_next_level("Advanced", 95.0), "Advanced")  # Ceiling

        # Step down (Score < 50%)
        self.assertEqual(calculate_next_level("Advanced", 49.0), "Intermediate")
        self.assertEqual(calculate_next_level("Intermediate", 30.0), "Beginner")
        self.assertEqual(calculate_next_level("Beginner", 20.0), "Beginner")  # Floor

        # Maintain level (50% <= Score < 80%)
        self.assertEqual(calculate_next_level("Beginner", 50.0), "Beginner")
        self.assertEqual(calculate_next_level("Beginner", 60.0), "Beginner")
        self.assertEqual(calculate_next_level("Intermediate", 75.0), "Intermediate")
        self.assertEqual(calculate_next_level("Advanced", 65.0), "Advanced")

        # Unknown level raises ValueError
        with self.assertRaises(ValueError):
            calculate_next_level("Unknown", 50.0)

    @patch("ai_module.adaptive_tutor.GeminiService")
    def test_invalid_inputs_rejected_before_api_call(self, mock_service_cls):
        """Confirm invalid inputs are rejected immediately without initializing GeminiService or making API calls."""
        # Empty topic
        with self.assertRaises(ValueError):
            generate_adaptive_content("", "Beginner")
        mock_service_cls.assert_not_called()

        # Whitespace topic
        with self.assertRaises(ValueError):
            generate_adaptive_content("   \t\n  ", "Beginner")
        mock_service_cls.assert_not_called()

        # Non-string topic
        with self.assertRaises(ValueError):
            generate_adaptive_content(12345, "Beginner")  # type: ignore
        mock_service_cls.assert_not_called()

        # Invalid difficulty
        with self.assertRaises(ValueError):
            generate_adaptive_content("Valid Topic", "Expert")
        mock_service_cls.assert_not_called()

        with self.assertRaises(ValueError):
            generate_adaptive_content("Valid Topic", "invalid_level")
        mock_service_cls.assert_not_called()

    def test_documented_signature_matches_implementation(self):
        """Confirm that the documented function signature matches the real implementation."""
        import inspect
        from typing import get_type_hints

        sig = inspect.signature(generate_adaptive_content)
        params = list(sig.parameters.keys())

        # Verify parameter names and ordering
        self.assertEqual(params, ["topic", "difficulty", "api_key", "model_name"])

        # Verify defaults
        self.assertEqual(sig.parameters["topic"].default, inspect.Parameter.empty)
        self.assertEqual(sig.parameters["difficulty"].default, inspect.Parameter.empty)
        self.assertIsNone(sig.parameters["api_key"].default)
        self.assertIsNone(sig.parameters["model_name"].default)

        # Verify return type annotation
        type_hints = get_type_hints(generate_adaptive_content)
        self.assertIn("return", type_hints)
        self.assertEqual(type_hints["return"].__origin__, dict)

    @patch("ai_module.gemini_service.genai.Client")
    def test_end_to_end_mocked_gemini_response_payload(self, mock_client_cls):
        """Test full pipeline with a mocked raw Gemini JSON response, verifying all required fields and types."""
        import json

        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        # Mock JSON payload returned from Gemini model
        mock_response_payload = {
            "topic": "Graph Algorithms",
            "difficulty_level": "Advanced",
            "explanation": "Advanced graph algorithms include Tarjan's strongly connected components and Dinic's max-flow algorithm.",
            "notes": [
                "Tarjan's algorithm uses DFS with discovery and low-link values.",
                "Dinic's algorithm uses BFS to build level graphs and DFS for blocking flows.",
                "Complexity of Dinic's is O(V^2 * E) on general networks.",
                "Residual graphs track backward edge capacities."
            ],
            "quiz": [
                {
                    "question": f"Advanced graph query {i}?",
                    "options": [f"Option {i}A", f"Option {i}B", f"Option {i}C", f"Option {i}D"],
                    "correct_answer": f"Option {i}A"
                }
                for i in range(1, 13)
            ]
        }

        mock_response = MagicMock()
        mock_response.text = json.dumps(mock_response_payload)
        mock_client.models.generate_content.return_value = mock_response

        # Execute public function
        result = generate_adaptive_content(
            topic="Graph Algorithms",
            difficulty="Advanced",
            api_key="mock_secret_key"
        )

        # 1. Documented type verification
        self.assertIsInstance(result, dict)

        # 2. Required top-level fields
        required_keys = {"topic", "difficulty_level", "explanation", "notes", "quiz"}
        self.assertEqual(set(result.keys()), required_keys)

        # 3. Field type and content constraints
        self.assertEqual(result["topic"], "Graph Algorithms")
        self.assertEqual(result["difficulty_level"], "Advanced")
        self.assertIsInstance(result["explanation"], str)
        self.assertTrue(len(result["explanation"]) > 0)

        # 4. Notes validation (3-5 items, non-empty)
        self.assertIsInstance(result["notes"], list)
        self.assertTrue(3 <= len(result["notes"]) <= 5)
        for note in result["notes"]:
            self.assertIsInstance(note, str)
            self.assertTrue(len(note.strip()) > 0)

        # 5. Quiz validation (exactly 12 items, 4 distinct options, matching answer)
        self.assertIsInstance(result["quiz"], list)
        self.assertEqual(len(result["quiz"]), 12)

        for q in result["quiz"]:
            self.assertIsInstance(q, dict)
            self.assertEqual(set(q.keys()), {"question", "options", "correct_answer"})
            self.assertIsInstance(q["question"], str)
            self.assertTrue(len(q["question"].strip()) > 0)

            self.assertIsInstance(q["options"], list)
            self.assertEqual(len(q["options"]), 4)
            self.assertEqual(len(set(q["options"])), 4)  # 4 distinct options

            self.assertIsInstance(q["correct_answer"], str)
            self.assertIn(q["correct_answer"], q["options"])  # Matching option


if __name__ == "__main__":
    unittest.main(verbosity=2)
