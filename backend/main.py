"""
Main application entry point for AI Personalized Learning Content Generator Backend.
Configures FastAPI, startup/shutdown lifecycles, and route mounting.
"""

import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI

# Ensure project root is in sys.path when executed directly
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.config import APP_DESCRIPTION, APP_TITLE, APP_VERSION
from backend.database import init_db
from backend.routers.health import router as health_router
from backend.routers.sessions import router as sessions_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    Safely initializes SQLite tables on startup without destroying existing data.
    """
    # Safe startup initialization
    init_db()
    yield
    # Clean shutdown


app = FastAPI(
    title=APP_TITLE,
    description=APP_DESCRIPTION,
    version=APP_VERSION,
    lifespan=lifespan,
)

# Register routers
app.include_router(health_router)
app.include_router(sessions_router)


@app.get("/", summary="Root Status", include_in_schema=False)
def root_info() -> dict[str, str]:
    """Provides high-level service metadata and documentation link."""
    return {
        "service": APP_TITLE,
        "version": APP_VERSION,
        "docs_url": "/docs",
        "health_check": "/api/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)

