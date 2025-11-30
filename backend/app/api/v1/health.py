"""Health check endpoints."""

from fastapi import APIRouter, Response
from pydantic import BaseModel

from app.core.config import settings

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    environment: str
    version: str


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.

    Returns basic health status of the API.
    """
    return HealthResponse(
        status="healthy",
        environment=settings.environment,
        version="1.0.0",
    )


@router.get("/ready")
async def readiness_check():
    """
    Readiness check endpoint.

    Checks if all dependencies are ready.
    """
    # In production, check database connectivity, etc.
    return {"status": "ready"}


@router.get("/ping")
async def ping():
    """Simple ping endpoint."""
    return Response(content="pong", media_type="text/plain")
