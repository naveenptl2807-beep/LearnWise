import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pydantic import ValidationError
from ai_module.schemas import QuizQuestion, LearningModule


class TestQuizQuestionSchema(unittest.TestCase):
    def setUp(self):
        self.valid_question_payload = {
            "question": "What is Python's primary memory management mechanism?",
            "options": [
                "Reference counting",
                "Manual malloc/free",
                "Mark and sweep only",
                "Linear scan allocator"
            ],
            "correct_answer": "Reference counting"
        }

    def test_valid_quiz_question(self):
        """Test that a well-formed QuizQuestion parses successfully."""
        q = QuizQuestion(**self.valid_question_payload)
        self.assertEqual(q.question, self.valid_question_payload["question"])
        self.assertEqual(len(q.options), 4)
        self.assertEqual(q.correct_answer, "Reference counting")

    def test_invalid_empty_question(self):
        """Test that empty or whitespace-only question is rejected."""
        payload = self.valid_question_payload.copy()
        payload["question"] = "   "
        with self.assertRaises(ValidationError) as ctx:
            QuizQuestion(**payload)
        self.assertIn("Field must be a non-empty string", str(ctx.exception))

    def test_invalid_duplicate_options(self):
        """Test that duplicate options are rejected."""
        payload = self.valid_question_payload.copy()
        payload["options"] = [
            "Reference counting",
            "Reference counting",  # Duplicate
            "Option C",
            "Option D"
        ]
        with self.assertRaises(ValidationError) as ctx:
            QuizQuestion(**payload)
        self.assertIn("All 4 options must be distinct", str(ctx.exception))

    def test_invalid_option_count(self):
        """Test that fewer or more than 4 options are rejected."""
        payload = self.valid_question_payload.copy()
        payload["options"] = ["Choice A", "Choice B", "Choice C"]  # Only 3 options
        with self.assertRaises(ValidationError) as ctx:
            QuizQuestion(**payload)
        self.assertIn("Options must contain exactly 4 choices", str(ctx.exception))

    def test_invalid_correct_answer_not_in_options(self):
        """Test that a correct answer not matching any option is rejected."""
        payload = self.valid_question_payload.copy()
        payload["correct_answer"] = "Non-existent Answer"
        with self.assertRaises(ValidationError) as ctx:
            QuizQuestion(**payload)
        self.assertIn("does not match any of the provided options", str(ctx.exception))

    def test_invalid_extra_field_rejected(self):
        """Test that unexpected extra fields are forbidden."""
        payload = self.valid_question_payload.copy()
        payload["unexpected_extra_field"] = "malicious_data"
        with self.assertRaises(ValidationError) as ctx:
            QuizQuestion(**payload)
        self.assertIn("extra_forbidden", str(ctx.exception))


class TestLearningModuleSchema(unittest.TestCase):
    def setUp(self):
        self.valid_quiz_questions = [
            QuizQuestion(
                question=f"Question {i}?",
                options=[f"Choice {i}A", f"Choice {i}B", f"Choice {i}C", f"Choice {i}D"],
                correct_answer=f"Choice {i}A"
            )
            for i in range(1, 13)
        ]
        self.valid_module_payload = {
            "topic": "Python Memory Management",
            "difficulty_level": "Beginner",
            "explanation": "Python manages memory automatically using reference counting and a cyclic garbage collector.",
            "notes": [
                "Memory is organized in a private heap.",
                "Variables are references to objects.",
                "Reference counts drop when variables go out of scope."
            ],
            "quiz": self.valid_quiz_questions
        }

    def test_valid_learning_module(self):
        """Test that a well-formed LearningModule with exactly 12 questions parses successfully."""
        module = LearningModule(**self.valid_module_payload)
        self.assertEqual(module.topic, "Python Memory Management")
        self.assertEqual(module.difficulty_level, "Beginner")
        self.assertEqual(len(module.notes), 3)
        self.assertEqual(len(module.quiz), 12)
        # Verify every question has 4 distinct options and valid matching correct_answer
        for q in module.quiz:
            self.assertEqual(len(q.options), 4)
            self.assertEqual(len(set(q.options)), 4)
            self.assertIn(q.correct_answer, q.options)

    def test_valid_learning_module_with_five_notes_and_advanced(self):
        """Test boundary condition with maximum allowed notes (5) and Advanced level."""
        payload = self.valid_module_payload.copy()
        payload["difficulty_level"] = "Advanced"
        payload["notes"] = [f"Summary point {i}" for i in range(1, 6)]
        module = LearningModule(**payload)
        self.assertEqual(len(module.notes), 5)
        self.assertEqual(module.difficulty_level, "Advanced")
        self.assertEqual(len(module.quiz), 12)

    def test_invalid_difficulty_level(self):
        """Test that invalid difficulty level (not Beginner/Intermediate/Advanced) is rejected."""
        payload = self.valid_module_payload.copy()
        payload["difficulty_level"] = "Expert"  # Invalid
        with self.assertRaises(ValidationError) as ctx:
            LearningModule(**payload)
        self.assertIn("difficulty_level", str(ctx.exception))

    def test_invalid_notes_under_minimum(self):
        """Test that fewer than 3 notes are rejected."""
        payload = self.valid_module_payload.copy()
        payload["notes"] = ["Note 1", "Note 2"]  # Only 2 notes
        with self.assertRaises(ValidationError) as ctx:
            LearningModule(**payload)
        self.assertIn("Notes must contain between 3 and 5 items", str(ctx.exception))

    def test_invalid_notes_over_maximum(self):
        """Test that more than 5 notes are rejected."""
        payload = self.valid_module_payload.copy()
        payload["notes"] = [f"Note {i}" for i in range(6)]  # 6 notes
        with self.assertRaises(ValidationError) as ctx:
            LearningModule(**payload)
        self.assertIn("Notes must contain between 3 and 5 items", str(ctx.exception))

    def test_invalid_empty_note_item(self):
        """Test that empty or whitespace note entries are rejected."""
        payload = self.valid_module_payload.copy()
        payload["notes"] = ["Valid note 1", "   ", "Valid note 3"]
        with self.assertRaises(ValidationError) as ctx:
            LearningModule(**payload)
        self.assertIn("All notes must be non-empty strings", str(ctx.exception))

    def test_invalid_quiz_question_count_under_12(self):
        """Test that a quiz with 11 questions is rejected."""
        payload = self.valid_module_payload.copy()
        payload["quiz"] = self.valid_quiz_questions[:11]  # 11 questions
        with self.assertRaises(ValidationError) as ctx:
            LearningModule(**payload)
        self.assertIn("Quiz must contain exactly 12 questions", str(ctx.exception))

    def test_invalid_quiz_question_count_over_12(self):
        """Test that a quiz with 13 questions is rejected."""
        payload = self.valid_module_payload.copy()
        extra_question = QuizQuestion(
            question="Question 13?",
            options=["Choice 13A", "Choice 13B", "Choice 13C", "Choice 13D"],
            correct_answer="Choice 13A"
        )
        payload["quiz"] = self.valid_quiz_questions + [extra_question]  # 13 questions
        with self.assertRaises(ValidationError) as ctx:
            LearningModule(**payload)
        self.assertIn("Quiz must contain exactly 12 questions", str(ctx.exception))

    def test_invalid_module_extra_field_rejected(self):
        """Test that extra fields in LearningModule are rejected."""
        payload = self.valid_module_payload.copy()
        payload["score_weight"] = 100
        with self.assertRaises(ValidationError) as ctx:
            LearningModule(**payload)
        self.assertIn("extra_forbidden", str(ctx.exception))


if __name__ == "__main__":
    unittest.main(verbosity=2)
