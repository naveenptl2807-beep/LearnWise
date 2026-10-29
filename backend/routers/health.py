"""
Health and operational readiness router.
Provides endpoint for uptime and service verification independent of external AI services.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["Health"])


@router.get("/health", summary="Service Health Check")
def health_check() -> dict[str, str]:
    """
    Returns operational health status.
    Kept completely decoupled from Gemini API availability to ensure reliable monitoring.
    """
    return {"status": "ok"}

