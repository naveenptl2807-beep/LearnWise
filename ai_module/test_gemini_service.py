import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from google.genai.errors import APIError
from pydantic import ValidationError

from ai_module.gemini_service import (
    GeminiService,
    DEFAULT_GEMINI_MODEL,
    generate_learning_content,
)
from ai_module.schemas import LearningModule


class TestGeminiService(unittest.TestCase):
    def setUp(self):
        self.valid_module_data = {
            "topic": "Python Generators",
            "difficulty_level": "Beginner",
            "explanation": "Generators allow you to declare a function that behaves like an iterator using yield.",
            "notes": [
                "Generators use the yield keyword.",
                "They produce items lazily on demand.",
                "They maintain state between yields to save memory."
            ],
            "quiz": [
                {
                    "question": f"Question {i} about generators?",
                    "options": [f"Option {i}A", f"Option {i}B", f"Option {i}C", f"Option {i}D"],
                    "correct_answer": f"Option {i}A"
                }
                for i in range(1, 13)
            ]
        }

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_api_key_raises_value_error(self):
        """Test that initialization without GEMINI_API_KEY raises a clear ValueError."""
        with self.assertRaises(ValueError) as ctx:
            GeminiService()
        self.assertIn("GEMINI_API_KEY environment variable is not set", str(ctx.exception))

    @patch("ai_module.gemini_service.genai.Client")
    def test_default_and_custom_model_configuration(self, mock_client_cls):
        """Test model selection via default and GEMINI_MODEL env variable."""
        with patch.dict(os.environ, {"GEMINI_API_KEY": "test_dummy_key"}, clear=True):
            service_default = GeminiService()
            self.assertEqual(service_default.model_name, DEFAULT_GEMINI_MODEL)

        with patch.dict(os.environ, {"GEMINI_API_KEY": "test_dummy_key", "GEMINI_MODEL": "gemini-3.8-flash"}):
            service_custom = GeminiService()
            self.assertEqual(service_custom.model_name, "gemini-3.8-flash")

    @patch("ai_module.gemini_service.genai.Client")
    def test_successful_learning_module_generation(self, mock_client_cls):
        """Test that mock API response is correctly validated into a LearningModule."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        mock_response = MagicMock()
        mock_response.text = json.dumps(self.valid_module_data)
        mock_client.models.generate_content.return_value = mock_response

        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key_123"}):
            service = GeminiService()
            result = service.generate_learning_module(topic="Python Generators", difficulty_level="Beginner")

        self.assertIsInstance(result, LearningModule)
        self.assertEqual(result.topic, "Python Generators")
        self.assertEqual(result.difficulty_level, "Beginner")
        self.assertEqual(len(result.notes), 3)
        self.assertEqual(len(result.quiz), 12)

    @patch("ai_module.gemini_service.genai.Client")
    def test_reject_empty_gemini_response(self, mock_client_cls):
        """Test that empty or whitespace responses from Gemini raise ValueError."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        mock_response = MagicMock()
        mock_response.text = "   "
        mock_client.models.generate_content.return_value = mock_response

        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key_123"}):
            service = GeminiService()
            with self.assertRaises(ValueError) as ctx:
                service.generate_learning_module(topic="Python Generators", difficulty_level="Beginner")
            self.assertIn("empty or null response", str(ctx.exception))

    @patch("ai_module.gemini_service.genai.Client")
    def test_reject_invalid_schema_content(self, mock_client_cls):
        """Test that malformed content (e.g. only 11 quiz questions) is rejected."""
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        invalid_data = self.valid_module_data.copy()
        invalid_data["quiz"] = invalid_data["quiz"][:11]  # Violates exactly 12 questions constraint

        mock_response = MagicMock()
        mock_response.text = json.dumps(invalid_data)
        mock_client.models.generate_content.return_value = mock_response

        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake_key_123"}):
            service = GeminiService()
            with self.assertRaises(ValueError) as ctx:
                service.generate_learning_module(topic="Python Generators", difficulty_level="Beginner")
            self.assertIn("Generated output failed schema validation", str(ctx.exception))

    @patch("ai_module.gemini_service.genai.Client")
    def test_api_error_handling_sanitizes_secret(self, mock_client_cls):
        """Test that API errors are wrapped in RuntimeError and credentials are never exposed."""
        secret_key = "SECRET_CREDENTIAL_KEY_999"
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client

        # Simulate APIError that includes the secret key in its message
        mock_client.models.generate_content.side_effect = Exception(f"Failed authentication with {secret_key}")

        with patch.dict(os.environ, {"GEMINI_API_KEY": secret_key}):
            service = GeminiService()
            with self.assertRaises(RuntimeError) as ctx:
                service.generate_learning_module(topic="Python Generators", difficulty_level="Beginner")

            error_message = str(ctx.exception)
            self.assertNotIn(secret_key, error_message)
            self.assertIn("[REDACTED]", error_message)

    @patch("ai_module.gemini_service.GeminiService")
    def test_generate_learning_content_helper(self, mock_service_cls):
        """Test convenience wrapper function."""
        mock_instance = MagicMock()
        mock_service_cls.return_value = mock_instance
        mock_instance.generate_learning_module.return_value = MagicMock(spec=LearningModule)

        result = generate_learning_content("Trees", "Beginner", api_key="dummy_key")
        mock_instance.generate_learning_module.assert_called_once_with(topic="Trees", difficulty_level="Beginner")
        self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
