"""
Adaptive Tutor - Public Interface for AI Learning Module Generation.

Provides the primary public entry point `generate_adaptive_content` for FastAPI backend
routes and the difficulty adaptation engine `calculate_next_level`.
"""

import os
import sys
from typing import Any, Optional

# Ensure project root is in sys.path when executed directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ai_module.difficulty import calculate_next_level
from ai_module.gemini_service import GeminiService
from ai_module.prompts import VALID_DIFFICULTIES
from ai_module.schemas import LearningModule, QuizQuestion


def generate_adaptive_content(
    topic: str,
    difficulty: str,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
) -> dict[str, Any]:
    """
    Generates a personalized, structured learning module using Gemini AI.

    Public interface function designed for backend endpoints (e.g. FastAPI / Flask)
    and learning pipelines. Validates inputs, builds pedagogical prompts, calls the
    Gemini service with structured JSON output enforcement, validates the resulting
    payload against the LearningModule schema, and returns a JSON-compliant dictionary.

    Args:
        topic: Non-empty string specifying the subject or concept to learn (e.g., 'Binary Search Algorithm').
        difficulty: Target difficulty level. Must be one of 'Beginner', 'Intermediate', or 'Advanced'.
        api_key: Optional Gemini API key override. If omitted, reads from the GEMINI_API_KEY environment variable.
        model_name: Optional Gemini model override. If omitted, reads from the GEMINI_MODEL environment variable
                    or defaults to the supported default model ('gemini-3.5-flash-lite').

    Returns:
        dict[str, Any]: A JSON-serializable dictionary with the following structure:
            {
                "topic": str,
                "difficulty_level": "Beginner" | "Intermediate" | "Advanced",
                "explanation": str,
                "notes": list[str],          # Between 3 and 5 summary bullet points
                "quiz": list[dict[str, Any]] # Exactly 12 multiple-choice questions
                    # Each quiz dict has:
                    # {
                    #     "question": str,
                    #     "options": list[str],   # Exactly 4 distinct choices
                    #     "correct_answer": str   # Identical match to one of the options
                    # }
            }

    Raises:
        ValueError: If topic is empty/whitespace, difficulty is not one of ('Beginner', 'Intermediate', 'Advanced'),
                    or the generated model output fails schema validation constraints.
        RuntimeError: If the Gemini API encounters authentication errors, rate limits, network failures, or 503 spikes.
    """
    # 1. Validate inputs
    if not isinstance(topic, str) or not topic.strip():
        raise ValueError("Topic must be a non-empty string.")

    cleaned_topic = topic.strip()

    if difficulty not in VALID_DIFFICULTIES:
        allowed = ", ".join(sorted(VALID_DIFFICULTIES))
        raise ValueError(
            f"Invalid difficulty '{difficulty}'. Must be one of: {allowed}."
        )

    # 2. Initialize Gemini Service (credentials verified from environment)
    service = GeminiService(api_key=api_key, model_name=model_name)

    # 3. Request structured generation & validate against LearningModule schema
    learning_module: LearningModule = service.generate_learning_module(
        topic=cleaned_topic, difficulty_level=difficulty
    )

    # 4. Return predictable Python dictionary suitable for direct FastAPI JSON responses
    return learning_module.model_dump()