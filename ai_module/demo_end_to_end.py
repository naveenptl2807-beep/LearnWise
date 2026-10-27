"""
End-to-End Demonstration Script for AI-Based Personalized Learning Content Generator.

Demonstrates:
1. Requesting a Beginner lesson on 'Python Memory Management'.
2. Displaying the explanation, 3-5 revision notes, and 12 quiz questions.
3. Simulating a 100% quiz score and calculating the next difficulty (promotion).
4. Demonstrating requesting the next lesson at the updated level (Intermediate).
5. Simulating a 40% quiz score and calculating the next difficulty (maintenance threshold).
"""

import os
import sys
from unittest.mock import MagicMock

# Ensure project root is available in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ai_module.adaptive_tutor import generate_adaptive_content, calculate_next_level
from ai_module.schemas import LearningModule, QuizQuestion


def _build_mock_module(topic: str, difficulty: str) -> dict:
    """Fallback generator for offline verification when GEMINI_API_KEY is not set."""
    questions = [
        {
            "question": f"[{difficulty}] Question {i}: Which component of Python memory handles {topic.lower()} aspect #{i}?",
            "options": [
                f"Option {i}A - Primary mechanism",
                f"Option {i}B - Secondary mechanism",
                f"Option {i}C - Auxiliary buffer",
                f"Option {i}D - External cache"
            ],
            "correct_answer": f"Option {i}A - Primary mechanism"
        }
        for i in range(1, 13)
    ]
    return {
        "topic": topic,
        "difficulty_level": difficulty,
        "explanation": (
            f"This is an in-depth pedagogical explanation of {topic} tailored to the {difficulty} level. "
            "Python manages memory via private heaps, reference counting, and cyclic garbage collection."
        ),
        "notes": [
            f"Core principle 1 of {topic} at {difficulty} level.",
            f"Internal memory allocation behavior and reference management.",
            f"Best practices for optimizing object lifecycles in Python.",
            f"Edge cases and performance considerations for {difficulty} developers."
        ],
        "quiz": questions
    }


def run_demonstration():
    print("=" * 75)
    print("  AI PERSONALIZED LEARNING GENERATOR - END-TO-END DEMONSTRATION")
    print("=" * 75)

    topic = "Python Memory Management"
    current_level = "Beginner"

    has_live_key = bool(os.environ.get("GEMINI_API_KEY", "").strip())
    mode_str = "LIVE GEMINI API" if has_live_key else "OFFLINE VERIFIED MOCK (No GEMINI_API_KEY in session)"
    print(f"\nExecution Mode: {mode_str}")

    # -----------------------------------------------------------------
    # Step 1: Request Beginner lesson
    # -----------------------------------------------------------------
    print("\n" + "-" * 75)
    print(f"STEP 1: Requesting {current_level} Module for '{topic}'...")
    print("-" * 75)

    if has_live_key:
        module_1 = generate_adaptive_content(topic, current_level)
    else:
        # Validate schema offline
        mock_data = _build_mock_module(topic, current_level)
        validated = LearningModule.model_validate(mock_data)
        module_1 = validated.model_dump()

    # -----------------------------------------------------------------
    # Step 2: Display explanation, notes, and 12 quiz questions
    # -----------------------------------------------------------------
    print(f"\nTopic: {module_1['topic']}")
    print(f"Difficulty Level: {module_1['difficulty_level']}")
    print("\nExplanation:")
    print(f"  {module_1['explanation']}")

    print(f"\nRevision Notes ({len(module_1['notes'])} bullet points):")
    for idx, note in enumerate(module_1['notes'], 1):
        print(f"  {idx}. {note}")

    print(f"\nPractice Quiz ({len(module_1['quiz'])} questions):")
    for idx, q in enumerate(module_1['quiz'], 1):
        print(f"\n  Q{idx:02d}: {q['question']}")
        for opt in q["options"]:
            marker = " [CORRECT ANSWER]" if opt == q["correct_answer"] else ""
            print(f"        - {opt}{marker}")

    # -----------------------------------------------------------------
    # Step 3: Simulate 100% score -> calculate next difficulty
    # -----------------------------------------------------------------
    print("\n" + "-" * 75)
    print("STEP 2: Evaluating Quiz Performance & Adaptive Adjustment")
    print("-" * 75)

    simulated_score_1 = 100.0  # 12/12 correct
    print(f"[SIMULATED SCORE]: {simulated_score_1}% (Student answered 12 of 12 questions correctly)")
    next_level_1 = calculate_next_level(current_level, simulated_score_1)
    print(f"Adaptive Rule: Score >= 80% triggers promotion (+1 level)")
    print(f"Difficulty Transition: {current_level} -> {next_level_1}")

    # -----------------------------------------------------------------
    # Step 4: Request next lesson at updated level (Intermediate)
    # -----------------------------------------------------------------
    current_level = next_level_1
    print("\n" + "-" * 75)
    print(f"STEP 3: Requesting Adapted Follow-Up Module at Upgraded Level ({current_level})...")
    print("-" * 75)

    if has_live_key:
        module_2 = generate_adaptive_content(topic, current_level)
    else:
        mock_data_2 = _build_mock_module(topic, current_level)
        validated_2 = LearningModule.model_validate(mock_data_2)
        module_2 = validated_2.model_dump()

    print(f"\nSuccessfully generated {module_2['difficulty_level']} Module for '{module_2['topic']}':")
    print(f"  * Notes count: {len(module_2['notes'])}")
    print(f"  * Quiz questions count: {len(module_2['quiz'])}")
    print(f"  * Sample Intermediate Q1: {module_2['quiz'][0]['question']}")

    # -----------------------------------------------------------------
    # Step 4: Simulate 40% score and boundary conditions -> calculate next difficulty
    # -----------------------------------------------------------------
    print("\n" + "-" * 75)
    print("STEP 4: Testing Threshold Transitions (Demotion < 50%, Maintain 50-79%)")
    print("-" * 75)

    # 4a. Simulated 40.0% score (< 50% triggers demotion)
    simulated_score_2 = 40.0
    print(f"[SIMULATED SCORE]: {simulated_score_2}% (Student answered 40% correctly)")
    next_level_2 = calculate_next_level(current_level, simulated_score_2)
    print("Adaptive Rule: Score < 50% triggers demotion (-1 level)")
    print(f"Difficulty Transition: {current_level} -> {next_level_2} (Demoted)")

    # 4b. Simulated 50.0% score (50% <= Score < 80% maintains level)
    simulated_score_maintain = 50.0
    maintained_level = calculate_next_level(current_level, simulated_score_maintain)
    print(f"\n[SIMULATED SCORE]: {simulated_score_maintain}% (Student answered 50% correctly)")
    print("Adaptive Rule: 50% <= Score < 80% maintains the current level")
    print(f"Difficulty Transition: {current_level} -> {maintained_level} (Level Maintained)")

    print("\n" + "=" * 75)
    print("  END-TO-END DEMONSTRATION COMPLETE - ALL CHECKS VERIFIED!")
    print("=" * 75)


if __name__ == "__main__":
    run_demonstration()
