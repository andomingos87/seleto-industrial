"""
Health check endpoint
"""

from datetime import UTC, datetime

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""

    status: str
    timestamp: str
    service: str
    version: str


@router.get("/api/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Verifica se o serviço está operacional.
    Retorna status 200 se tudo estiver OK.
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(UTC).isoformat(),
        service="seleto-sdr-agent",
        version="0.1.0",
    )
