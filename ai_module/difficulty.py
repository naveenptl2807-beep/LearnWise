"""
Difficulty Adjustment Engine for AI-Generated Learning.

Provides deterministic pedagogical progression logic based on caller-supplied
quiz score percentages.
"""

import math
from typing import Union

LEVEL_ORDER = ("Beginner", "Intermediate", "Advanced")


def calculate_next_level(current_level: str, score_percentage: Union[int, float]) -> str:
    """
    Adjusts the student's difficulty level based on their latest quiz score percentage.

    Rules:
    - Score >= 80.0: Increase difficulty by one level (clamped at Advanced).
    - Score < 50.0: Decrease difficulty by one level (clamped at Beginner).
    - Otherwise (50.0 <= Score < 80.0): Maintain the current difficulty level.
    - Levels: Beginner, Intermediate, Advanced.
    - Clamping: Never moves above Advanced or below Beginner.

    Args:
        current_level: Must be one of 'Beginner', 'Intermediate', or 'Advanced'.
        score_percentage: A numeric score percentage between 0.0 and 100.0 inclusive.

    Returns:
        str: The updated difficulty level ('Beginner', 'Intermediate', or 'Advanced').

    Raises:
        ValueError: If current_level is invalid, or if score_percentage is not a valid
                    number between 0.0 and 100.0.
    """
    # 1. Validate score_percentage
    if isinstance(score_percentage, bool) or not isinstance(score_percentage, (int, float)):
        raise ValueError(
            f"Score percentage must be a numeric value, got {type(score_percentage).__name__}."
        )

    if math.isnan(score_percentage) or math.isinf(score_percentage):
        raise ValueError("Score percentage must be a finite number.")

    if score_percentage < 0.0 or score_percentage > 100.0:
        raise ValueError(
            f"Score percentage must be between 0.0 and 100.0, got {score_percentage}."
        )

    # 2. Validate current_level
    if not isinstance(current_level, str) or current_level not in LEVEL_ORDER:
        allowed = ", ".join(LEVEL_ORDER)
        raise ValueError(
            f"Invalid difficulty level '{current_level}'. Must be one of: {allowed}."
        )

    current_idx = LEVEL_ORDER.index(current_level)

    # 3. Apply adjustment rules
    if score_percentage >= 80.0:
        # Promote (capped at Advanced)
        return LEVEL_ORDER[min(current_idx + 1, len(LEVEL_ORDER) - 1)]
    elif score_percentage < 50.0:
        # Demote (floored at Beginner)
        return LEVEL_ORDER[max(current_idx - 1, 0)]
    else:
        # Maintain current level (50.0 <= score < 80.0)
        return LEVEL_ORDER[current_idx]
