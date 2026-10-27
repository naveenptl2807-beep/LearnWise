import math
import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ai_module.difficulty import calculate_next_level


class TestDifficultyAdjustment(unittest.TestCase):
    """
    Unit tests for calculate_next_level covering:
    - Score thresholds: 0, 49.99, 50, 79.99, 80, 100
    - Boundary transitions and level clamping (Beginner floor, Advanced ceiling)
    - Input validation rejecting invalid levels and out-of-range scores
    """

    # -----------------------------------------------------------------
    # 1. Tests Starting from 'Beginner'
    # -----------------------------------------------------------------
    def test_beginner_transitions(self):
        # Score 0: < 50 -> decrease by 1, but floored at Beginner
        self.assertEqual(calculate_next_level("Beginner", 0), "Beginner")

        # Score 49.99: < 50 -> decrease by 1, but floored at Beginner
        self.assertEqual(calculate_next_level("Beginner", 49.99), "Beginner")

        # Score 50: 50 <= score < 80 -> maintain Beginner
        self.assertEqual(calculate_next_level("Beginner", 50), "Beginner")

        # Score 79.99: 50 <= score < 80 -> maintain Beginner
        self.assertEqual(calculate_next_level("Beginner", 79.99), "Beginner")

        # Score 80: >= 80 -> promote to Intermediate
        self.assertEqual(calculate_next_level("Beginner", 80), "Intermediate")

        # Score 100: >= 80 -> promote to Intermediate
        self.assertEqual(calculate_next_level("Beginner", 100), "Intermediate")

    # -----------------------------------------------------------------
    # 2. Tests Starting from 'Intermediate'
    # -----------------------------------------------------------------
    def test_intermediate_transitions(self):
        # Score 0: < 50 -> demote to Beginner
        self.assertEqual(calculate_next_level("Intermediate", 0), "Beginner")

        # Score 39.99: < 50 -> demote to Beginner
        self.assertEqual(calculate_next_level("Intermediate", 39.99), "Beginner")

        # Score 49.99: < 50 -> demote to Beginner
        self.assertEqual(calculate_next_level("Intermediate", 49.99), "Beginner")

        # Score 50: boundary for maintain -> maintain Intermediate
        self.assertEqual(calculate_next_level("Intermediate", 50), "Intermediate")

        # Score 79.99: 50 <= score < 80 -> maintain Intermediate
        self.assertEqual(calculate_next_level("Intermediate", 79.99), "Intermediate")

        # Score 80: >= 80 -> promote to Advanced
        self.assertEqual(calculate_next_level("Intermediate", 80), "Advanced")

        # Score 100: >= 80 -> promote to Advanced
        self.assertEqual(calculate_next_level("Intermediate", 100), "Advanced")

    # -----------------------------------------------------------------
    # 3. Tests Starting from 'Advanced'
    # -----------------------------------------------------------------
    def test_advanced_transitions(self):
        # Score 0: < 50 -> demote to Intermediate
        self.assertEqual(calculate_next_level("Advanced", 0), "Intermediate")

        # Score 39.99: < 50 -> demote to Intermediate
        self.assertEqual(calculate_next_level("Advanced", 39.99), "Intermediate")

        # Score 49.99: < 50 -> demote to Intermediate
        self.assertEqual(calculate_next_level("Advanced", 49.99), "Intermediate")

        # Score 50: boundary for maintain -> maintain Advanced
        self.assertEqual(calculate_next_level("Advanced", 50), "Advanced")

        # Score 79.99: 50 <= score < 80 -> maintain Advanced
        self.assertEqual(calculate_next_level("Advanced", 79.99), "Advanced")

        # Score 80: >= 80 -> promote, but clamped at Advanced
        self.assertEqual(calculate_next_level("Advanced", 80), "Advanced")

        # Score 100: >= 80 -> promote, but clamped at Advanced
        self.assertEqual(calculate_next_level("Advanced", 100), "Advanced")

    # -----------------------------------------------------------------
    # 4. Score Input Validation (rejects outside 0-100 and invalid types)
    # -----------------------------------------------------------------
    def test_reject_scores_outside_0_to_100(self):
        # Below 0
        with self.assertRaises(ValueError) as ctx:
            calculate_next_level("Beginner", -0.01)
        self.assertIn("between 0.0 and 100.0", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            calculate_next_level("Beginner", -25)
        self.assertIn("between 0.0 and 100.0", str(ctx.exception))

        # Above 100
        with self.assertRaises(ValueError) as ctx:
            calculate_next_level("Beginner", 100.01)
        self.assertIn("between 0.0 and 100.0", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            calculate_next_level("Beginner", 150)
        self.assertIn("between 0.0 and 100.0", str(ctx.exception))

    def test_reject_non_numeric_and_special_scores(self):
        # Boolean is rejected (subclass of int in Python)
        with self.assertRaises(ValueError) as ctx:
            calculate_next_level("Beginner", True)
        self.assertIn("numeric value", str(ctx.exception))

        # None and strings
        with self.assertRaises(ValueError):
            calculate_next_level("Beginner", None)  # type: ignore

        with self.assertRaises(ValueError):
            calculate_next_level("Beginner", "80")  # type: ignore

        # NaN and Infinities
        with self.assertRaises(ValueError) as ctx:
            calculate_next_level("Beginner", float("nan"))
        self.assertIn("finite number", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            calculate_next_level("Beginner", float("inf"))
        self.assertIn("finite number", str(ctx.exception))

    # -----------------------------------------------------------------
    # 5. Difficulty Level Input Validation
    # -----------------------------------------------------------------
    def test_reject_invalid_difficulty_levels(self):
        with self.assertRaises(ValueError) as ctx:
            calculate_next_level("Expert", 80)
        self.assertIn("Invalid difficulty level 'Expert'", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            calculate_next_level("beginner", 80)  # Case sensitive
        self.assertIn("Invalid difficulty level 'beginner'", str(ctx.exception))

        with self.assertRaises(ValueError):
            calculate_next_level("", 80)

        with self.assertRaises(ValueError):
            calculate_next_level(None, 80)  # type: ignore

        with self.assertRaises(ValueError):
            calculate_next_level(123, 80)  # type: ignore

    # -----------------------------------------------------------------
    # 6. Explicit Verification of User's Exact Boundaries
    # -----------------------------------------------------------------
    def test_exact_boundaries_lower_level_selection_under_50(self):
        """0% and 49.99% select a lower level when possible (< 50%)."""
        # Advanced drops to Intermediate
        self.assertEqual(calculate_next_level("Advanced", 0.0), "Intermediate")
        self.assertEqual(calculate_next_level("Advanced", 39.99), "Intermediate")
        self.assertEqual(calculate_next_level("Advanced", 49.99), "Intermediate")

        # Intermediate drops to Beginner
        self.assertEqual(calculate_next_level("Intermediate", 0.0), "Beginner")
        self.assertEqual(calculate_next_level("Intermediate", 39.99), "Beginner")
        self.assertEqual(calculate_next_level("Intermediate", 49.99), "Beginner")

    def test_exact_boundaries_maintain_current_level_50_to_79_99(self):
        """50% and 79.99% maintain the current level (50% <= Score < 80%)."""
        # Beginner remains Beginner
        self.assertEqual(calculate_next_level("Beginner", 50.0), "Beginner")
        self.assertEqual(calculate_next_level("Beginner", 79.99), "Beginner")

        # Intermediate remains Intermediate
        self.assertEqual(calculate_next_level("Intermediate", 50.0), "Intermediate")
        self.assertEqual(calculate_next_level("Intermediate", 79.99), "Intermediate")

        # Advanced remains Advanced
        self.assertEqual(calculate_next_level("Advanced", 50.0), "Advanced")
        self.assertEqual(calculate_next_level("Advanced", 79.99), "Advanced")

    def test_exact_boundaries_higher_level_selection_80_and_100(self):
        """80% and 100% select a higher level when possible."""
        # Beginner promotes to Intermediate
        self.assertEqual(calculate_next_level("Beginner", 80.0), "Intermediate")
        self.assertEqual(calculate_next_level("Beginner", 100.0), "Intermediate")

        # Intermediate promotes to Advanced
        self.assertEqual(calculate_next_level("Intermediate", 80.0), "Advanced")
        self.assertEqual(calculate_next_level("Intermediate", 100.0), "Advanced")

    def test_boundary_beginner_cannot_go_below_beginner(self):
        """Beginner cannot go below Beginner (floor constraint)."""
        self.assertEqual(calculate_next_level("Beginner", 0.0), "Beginner")
        self.assertEqual(calculate_next_level("Beginner", 15.0), "Beginner")
        self.assertEqual(calculate_next_level("Beginner", 39.99), "Beginner")

    def test_boundary_advanced_cannot_go_above_advanced(self):
        """Advanced cannot go above Advanced (ceiling constraint)."""
        self.assertEqual(calculate_next_level("Advanced", 80.0), "Advanced")
        self.assertEqual(calculate_next_level("Advanced", 95.0), "Advanced")
        self.assertEqual(calculate_next_level("Advanced", 100.0), "Advanced")

    def test_confirm_function_does_not_call_gemini(self):
        """Confirm calculate_next_level is a pure algorithmic function and does not call Gemini."""
        import ai_module.difficulty as diff_mod

        # 1. Assert difficulty.py does not import google, genai, or GeminiService
        self.assertNotIn("genai", dir(diff_mod))
        self.assertNotIn("GeminiService", dir(diff_mod))

        # 2. Spy on genai.Client to ensure zero calls occur during execution
        from unittest.mock import patch
        with patch("google.genai.Client") as mock_client:
            for level in ("Beginner", "Intermediate", "Advanced"):
                for score in (0, 39.99, 40, 79.99, 80, 100):
                    calculate_next_level(level, score)
            mock_client.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
