"""
Unit tests for the health check endpoint and application lifecycle.
Verifies response format, decoupled operation without Gemini API keys, and service availability.
"""

import os
import sys
import unittest
from fastapi.testclient import TestClient

# Ensure project root is available in sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.main import app


class TestHealthEndpoint(unittest.TestCase):
    """Test suite for GET /api/health."""

    def setUp(self):
        """Create TestClient instance with context management."""
        self.client = TestClient(app)

    def test_health_returns_expected_status(self):
        """Verify GET /api/health returns HTTP 200 and {'status': 'ok'}."""
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_health_works_without_gemini_api_key(self):
        """Verify health check succeeds even if GEMINI_API_KEY is not set."""
        original_key = os.environ.get("GEMINI_API_KEY")
        try:
            if "GEMINI_API_KEY" in os.environ:
                del os.environ["GEMINI_API_KEY"]

            response = self.client.get("/api/health")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {"status": "ok"})
        finally:
            if original_key is not None:
                os.environ["GEMINI_API_KEY"] = original_key

    def test_root_endpoint_metadata(self):
        """Verify root endpoint exposes documentation and health check links."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("service", data)
        self.assertEqual(data.get("health_check"), "/api/health")
        self.assertEqual(data.get("docs_url"), "/docs")


if __name__ == "__main__":
    unittest.main()

