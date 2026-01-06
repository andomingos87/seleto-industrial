"""
Metrics endpoint for Prometheus scraping.

TECH-023: Expor métricas em formato Prometheus
"""

from fastapi import APIRouter, Response

from src.services.metrics import get_metrics, get_metrics_content_type

router = APIRouter()


@router.get("/metrics")
async def metrics() -> Response:
    """
    Expose Prometheus metrics.

    Returns metrics in Prometheus text format for scraping by
    Prometheus server or compatible tools.

    Returns:
        Response with metrics in text/plain format
    """
    return Response(
        content=get_metrics(),
        media_type=get_metrics_content_type(),
    )
