"""
Live integration test for Gemini AI module.
Requires GEMINI_API_KEY to be set in the environment.
Can be explicitly executed using:
    python ai_module/integration_test_live.py
"""

import os
import sys

# Ensure project root is in sys.path when executed directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ai_module.gemini_service import GeminiService
from ai_module.schemas import LearningModule


def run_live_integration_test():
    print("=" * 70)
    print("        GEMINI SERVICE - LIVE INTEGRATION TEST")
    print("=" * 70)

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key or not api_key.strip():
        print("\n[ERROR] GEMINI_API_KEY environment variable is not set.")
        print("Please configure it in PowerShell for your current session:")
        print("    $env:GEMINI_API_KEY = \"your-api-key-here\"")
        print("Then re-run this script.\n")
        sys.exit(1)

    model_name = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
    print(f"Target Model: {model_name}")
    print("Initializing GeminiService (credentials read securely from environment)...")

    service = GeminiService()

    test_topic = "Binary Search Algorithm"
    test_difficulty = "Beginner"

    print(f"\n--> Calling live Gemini API for '{test_topic}' at '{test_difficulty}' level...")
    try:
        module: LearningModule = service.generate_learning_module(
            topic=test_topic, difficulty_level=test_difficulty
        )
    except Exception as exc:
        print(f"\n[FAIL] Live generation encountered an error: {exc}")
        sys.exit(1)

    # Assertions on returned validated object
    assert isinstance(module, LearningModule), "Result must be a validated LearningModule instance"
    assert module.topic == test_topic, f"Expected topic '{test_topic}', got '{module.topic}'"
    assert module.difficulty_level == test_difficulty, f"Expected difficulty '{test_difficulty}'"
    assert 3 <= len(module.notes) <= 5, f"Notes count ({len(module.notes)}) out of bounds [3, 5]"
    assert len(module.quiz) == 12, f"Quiz must have exactly 12 questions, got {len(module.quiz)}"

    for idx, q in enumerate(module.quiz, 1):
        assert len(q.options) == 4, f"Question {idx} must have 4 options"
        assert len(set(q.options)) == 4, f"Question {idx} options must be distinct"
        assert q.correct_answer in q.options, f"Question {idx} correct answer not in options"

    print("\n[SUCCESS] Live response validated against LearningModule schema!")
    print(f"\nTopic: {module.topic}")
    print(f"Difficulty Level: {module.difficulty_level}")
    print(f"\nExplanation Summary ({len(module.explanation)} chars):")
    print(f"  {module.explanation[:200]}...")

    print(f"\nSummary Notes ({len(module.notes)} points):")
    for note in module.notes:
        print(f"  * {note}")

    print(f"\nPractice Quiz ({len(module.quiz)} questions):")
    for idx, q in enumerate(module.quiz, 1):
        print(f"  Q{idx}: {q.question}")
        for opt in q.options:
            marker = " (Correct)" if opt == q.correct_answer else ""
            print(f"     - {opt}{marker}")

    print("\n" + "=" * 70)
    print("Live integration test passed completely!")
    print("=" * 70)


if __name__ == "__main__":
    run_live_integration_test()
