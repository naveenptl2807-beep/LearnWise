"""
AI Service layer interfacing with ai_module.adaptive_tutor.
Handles content generation, strict response validation, question/answer separation,
and exception sanitization.
"""

from typing import Any, Tuple
from ai_module.adaptive_tutor import generate_adaptive_content
from backend.config import GEMINI_API_KEY, GEMINI_MODEL


class AIServiceError(Exception):
    """Raised when AI module generation or validation encounters an error."""
    pass


def generate_and_validate_cycle_content(
    topic: str,
    difficulty_level: str,
) -> Tuple[str, list[str], list[dict[str, Any]], list[str]]:
    """
    Invokes the AI module to generate a learning module and validates the output.

    Args:
        topic: The subject to learn (e.g., 'Python Memory Management').
        difficulty_level: One of 'Beginner', 'Intermediate', 'Advanced'.

    Returns:
        Tuple of:
        - explanation: str
        - notes: list[str] (3 to 5 items)
        - quiz_questions: list[dict] (12 sanitized questions with question_index, question, options)
        - answer_key: list[str] (12 trusted correct answer strings)

    Raises:
        AIServiceError: If generation fails, AI returns invalid schema, or provider errors occur.
    """
    try:
        raw_data = generate_adaptive_content(
            topic=topic,
            difficulty=difficulty_level,
            api_key=GEMINI_API_KEY,
            model_name=GEMINI_MODEL,
        )
    except Exception as exc:
        # ai_module sanitizes credentials as [REDACTED]
        raise AIServiceError(f"AI content generation failed: {exc}") from exc

    if not isinstance(raw_data, dict):
        raise AIServiceError("AI generation returned non-dictionary output.")

    explanation = raw_data.get("explanation")
    if not isinstance(explanation, str) or not explanation.strip():
        raise AIServiceError("AI generation returned missing or empty explanation.")

    notes = raw_data.get("notes")
    if not isinstance(notes, list) or not (3 <= len(notes) <= 5):
        got_count = len(notes) if isinstance(notes, list) else 0
        raise AIServiceError(f"AI generation must return between 3 and 5 notes, got {got_count}.")
    if any(not isinstance(n, str) or not n.strip() for n in notes):
        raise AIServiceError("AI generation returned empty or non-string notes.")

    raw_quiz = raw_data.get("quiz")
    if not isinstance(raw_quiz, list) or len(raw_quiz) != 12:
        got_count = len(raw_quiz) if isinstance(raw_quiz, list) else 0
        raise AIServiceError(f"AI generation must return exactly 12 quiz questions, got {got_count}.")

    sanitized_quiz: list[dict[str, Any]] = []
    trusted_answer_key: list[str] = []

    for idx, q_item in enumerate(raw_quiz):
        if not isinstance(q_item, dict):
            raise AIServiceError(f"Quiz question #{idx} is not a valid object.")

        q_text = q_item.get("question")
        if not isinstance(q_text, str) or not q_text.strip():
            raise AIServiceError(f"Quiz question #{idx} has missing or empty question text.")

        options = q_item.get("options")
        if not isinstance(options, list) or len(options) != 4:
            raise AIServiceError(f"Quiz question #{idx} must have exactly 4 choices.")
        if any(not isinstance(opt, str) or not opt.strip() for opt in options):
            raise AIServiceError(f"Quiz question #{idx} contains empty or invalid option strings.")
        if len(set(options)) != 4:
            raise AIServiceError(f"Quiz question #{idx} contains duplicate options.")

        correct_ans = q_item.get("correct_answer")
        if not isinstance(correct_ans, str) or not correct_ans.strip():
            raise AIServiceError(f"Quiz question #{idx} has missing or empty correct_answer.")
        if correct_ans not in options:
            raise AIServiceError(f"Quiz question #{idx} correct_answer does not match any of its 4 options.")

        # Sanitize for public quiz storage (exclude correct_answer)
        sanitized_quiz.append({
            "question_index": idx,
            "question": q_text.strip(),
            "options": [opt.strip() for opt in options],
        })
        trusted_answer_key.append(correct_ans.strip())

    return explanation.strip(), [n.strip() for n in notes], sanitized_quiz, trusted_answer_key

