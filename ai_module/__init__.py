"""
AI Module - AI-Based Personalized Learning Content Generator.
Public package entry point exposing core generation and adaptive progression interfaces.
"""

from ai_module.adaptive_tutor import (
    generate_adaptive_content,
    calculate_next_level,
)
from ai_module.schemas import LearningModule, QuizQuestion
from ai_module.prompts import build_prompt, VALID_DIFFICULTIES
from ai_module.gemini_service import GeminiService

__all__ = [
    "generate_adaptive_content",
    "calculate_next_level",
    "LearningModule",
    "QuizQuestion",
    "build_prompt",
    "VALID_DIFFICULTIES",
    "GeminiService",
]
