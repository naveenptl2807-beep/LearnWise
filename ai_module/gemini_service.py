import os
from typing import Optional
from google import genai
from google.genai import types, errors
from pydantic import ValidationError

from ai_module.schemas import LearningModule
from ai_module.prompts import build_prompt

# Documented default model that has verified current availability and structured output support.
# Can be overridden via the GEMINI_MODEL environment variable (e.g., 'gemini-3.8-flash' or 'gemini-3.5-flash-lite').
DEFAULT_GEMINI_MODEL = "gemini-3.5-flash-lite"


class GeminiService:
    """
    Service responsible for interacting with the Google Gen AI Gemini API.
    Handles client initialization, prompt dispatch, structured output enforcement,
    and rigorous schema validation.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        """
        Initializes the GeminiService.

        Args:
            api_key: Optional API key override. If not provided, reads from GEMINI_API_KEY env var.
            model_name: Optional model override. If not provided, reads from GEMINI_MODEL env var
                        or falls back to DEFAULT_GEMINI_MODEL.
        """
        self._api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self._api_key or not self._api_key.strip():
            raise ValueError(
                "GEMINI_API_KEY environment variable is not set. "
                "Please configure GEMINI_API_KEY before initializing GeminiService."
            )

        env_model = os.environ.get("GEMINI_MODEL", "").strip()
        self.model_name = model_name or (env_model if env_model else DEFAULT_GEMINI_MODEL)
        self._client = genai.Client(api_key=self._api_key)

    def generate_learning_module(
        self, topic: str, difficulty_level: str, temperature: float = 0.3
    ) -> LearningModule:
        """
        Builds a pedagogical prompt, requests structured JSON from Gemini using the
        LearningModule schema, and validates the response.

        Args:
            topic: Non-empty topic string.
            difficulty_level: 'Beginner', 'Intermediate', or 'Advanced'.
            temperature: Sampling temperature (default 0.3 for deterministic generation).

        Returns:
            Validated LearningModule Pydantic instance.

        Raises:
            ValueError: If input parameters or model outputs are invalid or empty.
            RuntimeError: If Gemini API encounters communication or server errors.
        """
        # Step 1: Deterministically construct pedagogical prompt
        prompt = build_prompt(topic, difficulty_level)

        # Step 2: Configure structured schema enforcement
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=LearningModule,
            temperature=temperature,
        )

        # Step 3: Invoke the Gemini model
        try:
            response = self._client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config,
            )
        except errors.APIError as api_err:
            clean_msg = str(api_err).replace(self._api_key, "[REDACTED]")
            raise RuntimeError(f"Gemini API request failed: {clean_msg}") from None
        except Exception as exc:
            clean_msg = str(exc).replace(self._api_key, "[REDACTED]")
            raise RuntimeError(f"Unexpected error communicating with Gemini: {clean_msg}") from None

        # Step 4: Validate response content
        if not response or not response.text or not response.text.strip():
            raise ValueError("Gemini returned an empty or null response.")

        # Step 5: Strictly parse and validate via Pydantic schema
        try:
            validated_module = LearningModule.model_validate_json(response.text)
        except ValidationError as val_err:
            raise ValueError(f"Generated output failed schema validation: {val_err}") from val_err

        return validated_module


def generate_learning_content(
    topic: str,
    difficulty_level: str,
    api_key: Optional[str] = None,
    model_name: Optional[str] = None,
) -> LearningModule:
    """
    Convenience function for generating a validated LearningModule in a single call.
    """
    service = GeminiService(api_key=api_key, model_name=model_name)
    return service.generate_learning_module(topic=topic, difficulty_level=difficulty_level)
