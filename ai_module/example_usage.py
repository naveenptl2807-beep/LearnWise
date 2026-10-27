"""
Example script demonstrating how to invoke the public AI module interface.
Suitable for Rounak's FastAPI backend routes or CLI testing.
"""

import json
import os
import sys

# Ensure project root is available
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ai_module import generate_adaptive_content, calculate_next_level


def main():
    print("=" * 65)
    print("      PUBLIC AI MODULE INTERFACE - USAGE DEMO")
    print("=" * 65)

    topic = "Binary Search Tree"
    current_difficulty = "Beginner"

    print(f"\n1. Calling generate_adaptive_content('{topic}', '{current_difficulty}')...")

    # In actual deployment, GEMINI_API_KEY is configured in the environment
    if not os.environ.get("GEMINI_API_KEY"):
        print("[NOTE] GEMINI_API_KEY is not set in this terminal session.")
        print("To run live, set: $env:GEMINI_API_KEY = 'your_key'")
        return

    try:
        module_data: dict = generate_adaptive_content(topic, current_difficulty)
    except Exception as err:
        print(f"[ERROR] Content generation failed: {err}")
        return

    print("\n[SUCCESS] Content generated successfully!")
    print(f"Type: {type(module_data).__name__}")
    print(f"Topic: {module_data.get('topic')}")
    print(f"Difficulty: {module_data.get('difficulty_level')}")
    print(f"Explanation: {module_data.get('explanation', '')[:120]}...")
    print(f"Notes Count: {len(module_data.get('notes', []))}")
    print(f"Quiz Questions Count: {len(module_data.get('quiz', []))}")

    # 2. Adaptive Difficulty Evaluation
    print("\n2. Evaluating student quiz performance...")
    simulated_score = 91.6  # 11 out of 12 correct
    next_level = calculate_next_level(current_difficulty, simulated_score)
    print(f"Student scored: {simulated_score}%")
    print(f"Progression: {current_difficulty} -> {next_level} (>= 80% scales up difficulty)")


if __name__ == "__main__":
    main()
