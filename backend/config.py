"""
Configuration module for the AI Personalized Learning Content Generator Backend.
Handles environment variables, database URLs, and application metadata.
"""

import os
from pathlib import Path
from typing import Optional

# Base directories
BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent

# Database configuration
# Default SQLite database located directly under backend/
DEFAULT_DB_FILE = BASE_DIR / "learning_app.db"
DATABASE_URL: str = os.environ.get(
    "DATABASE_URL", f"sqlite:///{DEFAULT_DB_FILE.as_posix()}"
)

# Gemini API configuration (optional for health checks and initial server startup)
GEMINI_API_KEY: Optional[str] = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL: str = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")

# Application metadata
APP_TITLE: str = "AI Personalized Learning Content Generator"
APP_DESCRIPTION: str = (
    "Adaptive personalized learning content backend powered by FastAPI, SQLite, and Google Gemini."
)
APP_VERSION: str = "1.0.0"

