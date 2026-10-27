from typing import get_args
from ai_module.schemas import LearningModule

# Extract valid difficulty levels directly from the schema to ensure single source of truth
VALID_DIFFICULTIES = tuple(get_args(LearningModule.model_fields["difficulty_level"].annotation))

LEVEL_GUIDELINES = {
    "Beginner": (
        "Focus on simple definitions, intuitive analogies, and basic foundational examples "
        "suitable for a novice learner."
    ),
    "Intermediate": (
        "Focus on precise technical terminology, underlying mechanisms and architecture, "
        "and practical real-world usage examples."
    ),
    "Advanced": (
        "Focus on deep system internals, subtle edge cases, architectural and design trade-offs, "
        "and performance optimization."
    ),
}


def build_prompt(topic: str, difficulty_level: str) -> str:
    """
    Constructs a deterministic pedagogical prompt for generating a structured
    LearningModule matching the given topic and difficulty level.

    Args:
        topic: Non-empty string naming the subject or concept to learn.
        difficulty_level: Must be one of 'Beginner', 'Intermediate', or 'Advanced'.

    Returns:
        A formatted prompt string ready to pass to Gemini with the LearningModule schema.

    Raises:
        ValueError: If topic is empty/whitespace or difficulty_level is invalid.
    """
    if not isinstance(topic, str) or not topic.strip():
        raise ValueError("Topic must be a non-empty string.")

    cleaned_topic = topic.strip()

    if difficulty_level not in VALID_DIFFICULTIES:
        allowed = ", ".join(sorted(VALID_DIFFICULTIES))
        raise ValueError(
            f"Invalid difficulty level '{difficulty_level}'. Must be one of: {allowed}."
        )

    guidelines = LEVEL_GUIDELINES[difficulty_level]

    prompt = f"""You are an expert AI tutor. Generate a personalized, structured learning module strictly matching the requested topic and difficulty level.

Target Topic: {cleaned_topic}
Target Difficulty Level: {difficulty_level}

Pedagogical Guidelines for {difficulty_level} Level:
- {guidelines}

Module Requirements:
1. Detailed Explanation: Provide a comprehensive explanation tailored specifically to the {difficulty_level} level.
2. Revision Notes: Include between 3 and 5 concise, high-impact summary bullet points.
3. Practice Quiz: Include exactly 12 distinct, topic-relevant multiple-choice questions (MCQs) assessing understanding at the {difficulty_level} level.
   - Each question must provide exactly four distinct options.
   - Each question must designate one correct answer that identically matches one of the four options.
"""
    return prompt.strip()
