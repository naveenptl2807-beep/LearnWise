import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ai_module.prompts import build_prompt, VALID_DIFFICULTIES


class TestPromptBuilder(unittest.TestCase):
    def test_valid_difficulties_sync_with_schema(self):
        """Ensure VALID_DIFFICULTIES matches the schema definition."""
        self.assertEqual(set(VALID_DIFFICULTIES), {"Beginner", "Intermediate", "Advanced"})

    def test_beginner_prompt_structure_and_guidelines(self):
        """Test Beginner prompt generation and pedagogical guideline content."""
        topic = "Recursion in Python"
        prompt = build_prompt(topic, "Beginner")

        self.assertIn("Target Topic: Recursion in Python", prompt)
        self.assertIn("Target Difficulty Level: Beginner", prompt)
        # Check Beginner pedagogical instructions
        self.assertIn("simple definitions", prompt)
        self.assertIn("analogies", prompt)
        self.assertIn("basic", prompt)
        # Check structural requirements
        self.assertIn("Detailed Explanation", prompt)
        self.assertIn("between 3 and 5", prompt)
        self.assertIn("exactly 12 distinct, topic-relevant multiple-choice questions", prompt)
        self.assertIn("exactly four distinct options", prompt)
        self.assertIn("identically matches one of the four options", prompt)

    def test_intermediate_prompt_structure_and_guidelines(self):
        """Test Intermediate prompt generation and pedagogical guideline content."""
        topic = "PostgreSQL Indexing"
        prompt = build_prompt(topic, "Intermediate")

        self.assertIn("Target Topic: PostgreSQL Indexing", prompt)
        self.assertIn("Target Difficulty Level: Intermediate", prompt)
        # Check Intermediate pedagogical instructions
        self.assertIn("technical terminology", prompt)
        self.assertIn("mechanisms", prompt)
        self.assertIn("practical", prompt)
        # Ensure it does not include instructions for other levels
        self.assertNotIn("internals, subtle edge cases", prompt)

    def test_advanced_prompt_structure_and_guidelines(self):
        """Test Advanced prompt generation and pedagogical guideline content."""
        topic = "Distributed Consensus Algorithms"
        prompt = build_prompt(topic, "Advanced")

        self.assertIn("Target Topic: Distributed Consensus Algorithms", prompt)
        self.assertIn("Target Difficulty Level: Advanced", prompt)
        # Check Advanced pedagogical instructions
        self.assertIn("internals", prompt)
        self.assertIn("edge cases", prompt)
        self.assertIn("trade-offs", prompt)
        self.assertIn("optimization", prompt)

    def test_reject_empty_or_whitespace_topic(self):
        """Test that empty or whitespace topic strings raise ValueError."""
        with self.assertRaises(ValueError) as ctx:
            build_prompt("", "Beginner")
        self.assertIn("Topic must be a non-empty string", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            build_prompt("   ", "Beginner")
        self.assertIn("Topic must be a non-empty string", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            build_prompt(None, "Beginner")
        self.assertIn("Topic must be a non-empty string", str(ctx.exception))

    def test_reject_invalid_difficulty_level(self):
        """Test that unapproved difficulty levels raise ValueError."""
        with self.assertRaises(ValueError) as ctx:
            build_prompt("Python", "Expert")
        self.assertIn("Invalid difficulty level 'Expert'", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            build_prompt("Python", "beginner")  # Lowercase should be rejected
        self.assertIn("Invalid difficulty level 'beginner'", str(ctx.exception))

        with self.assertRaises(ValueError) as ctx:
            build_prompt("Python", "")
        self.assertIn("Invalid difficulty level ''", str(ctx.exception))

    def test_deterministic_output(self):
        """Test that prompt generation is strictly deterministic and produces identical output."""
        prompt_1 = build_prompt("Asyncio Event Loop", "Advanced")
        prompt_2 = build_prompt("Asyncio Event Loop", "Advanced")
        self.assertEqual(prompt_1, prompt_2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
