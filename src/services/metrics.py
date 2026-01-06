"""
Prometheus metrics service for observability.

TECH-023: Implementar métricas de latência e taxa de sucesso
- Coleta de métricas de tempo de resposta (P50, P95, P99)
- Taxa de sucesso/falha por operação e integração
- Métricas expostas em formato Prometheus
"""

import time
from contextlib import contextmanager
from functools import wraps
from typing import Callable, Optional

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Histogram,
    generate_latest,
)

from src.utils.logging import get_logger

logger = get_logger(__name__)

# Global registry for metrics
METRICS_REGISTRY = CollectorRegistry()

# ==================== Latency Buckets ====================
# Buckets optimized for API response times:
# - 0.1s: Very fast responses (health checks)
# - 0.5s: Fast responses (simple DB queries)
# - 1.0s: Normal responses
# - 2.0s: Slow but acceptable
# - 5.0s: Slow (may need investigation)
# - 10.0s: Very slow (alert threshold)
# - 30.0s: Extremely slow (external API timeouts)
HTTP_LATENCY_BUCKETS = (0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0)

# Buckets for integration calls (may be slower)
INTEGRATION_LATENCY_BUCKETS = (0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0)

# Buckets for internal operations
OPERATION_LATENCY_BUCKETS = (0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0)


# ==================== HTTP Request Metrics ====================

# Counter for total HTTP requests
http_requests_total = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["endpoint", "method", "status"],
    registry=METRICS_REGISTRY,
)

# Histogram for HTTP request duration
http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["endpoint", "method", "status"],
    buckets=HTTP_LATENCY_BUCKETS,
    registry=METRICS_REGISTRY,
)


# ==================== Integration Metrics ====================

# Counter for integration requests
integration_requests_total = Counter(
    "integration_requests_total",
    "Total number of integration requests",
    ["integration", "operation", "status"],
    registry=METRICS_REGISTRY,
)

# Histogram for integration request duration
integration_request_duration_seconds = Histogram(
    "integration_request_duration_seconds",
    "Integration request duration in seconds",
    ["integration", "operation"],
    buckets=INTEGRATION_LATENCY_BUCKETS,
    registry=METRICS_REGISTRY,
)


# ==================== Internal Operation Metrics ====================

# Counter for internal operations
operation_total = Counter(
    "operation_total",
    "Total number of internal operations",
    ["operation", "status"],
    registry=METRICS_REGISTRY,
)

# Histogram for internal operation duration
operation_duration_seconds = Histogram(
    "operation_duration_seconds",
    "Internal operation duration in seconds",
    ["operation"],
    buckets=OPERATION_LATENCY_BUCKETS,
    registry=METRICS_REGISTRY,
)


# ==================== Webhook Metrics ====================

# Counter for webhook events received
webhook_events_total = Counter(
    "webhook_events_total",
    "Total number of webhook events received",
    ["webhook_type", "event_type", "status"],
    registry=METRICS_REGISTRY,
)


# ==================== Agent Metrics ====================

# Counter for agent messages processed
agent_messages_total = Counter(
    "agent_messages_total",
    "Total number of messages processed by the agent",
    ["message_type", "status"],
    registry=METRICS_REGISTRY,
)

# Histogram for agent processing time
agent_processing_duration_seconds = Histogram(
    "agent_processing_duration_seconds",
    "Agent message processing duration in seconds",
    ["message_type"],
    buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0),
    registry=METRICS_REGISTRY,
)


# ==================== Helper Functions ====================


def record_http_request(
    endpoint: str,
    method: str,
    status_code: int,
    duration_seconds: float,
) -> None:
    """
    Record an HTTP request metric.

    Args:
        endpoint: Request endpoint path (e.g., "/webhook/whatsapp")
        method: HTTP method (e.g., "POST")
        status_code: HTTP response status code
        duration_seconds: Request duration in seconds
    """
    status = str(status_code)
    http_requests_total.labels(
        endpoint=endpoint,
        method=method,
        status=status,
    ).inc()
    http_request_duration_seconds.labels(
        endpoint=endpoint,
        method=method,
        status=status,
    ).observe(duration_seconds)


def record_integration_request(
    integration: str,
    operation: str,
    success: bool,
    duration_seconds: float,
) -> None:
    """
    Record an integration request metric.

    Args:
        integration: Integration name (e.g., "whatsapp", "piperun", "chatwoot")
        operation: Operation name (e.g., "send_message", "create_deal")
        success: Whether the request was successful
        duration_seconds: Request duration in seconds
    """
    status = "success" if success else "error"
    integration_requests_total.labels(
        integration=integration,
        operation=operation,
        status=status,
    ).inc()
    integration_request_duration_seconds.labels(
        integration=integration,
        operation=operation,
    ).observe(duration_seconds)


def record_operation(
    operation: str,
    success: bool,
    duration_seconds: float,
) -> None:
    """
    Record an internal operation metric.

    Args:
        operation: Operation name (e.g., "process_message", "classify_temperature")
        success: Whether the operation was successful
        duration_seconds: Operation duration in seconds
    """
    status = "success" if success else "error"
    operation_total.labels(
        operation=operation,
        status=status,
    ).inc()
    operation_duration_seconds.labels(
        operation=operation,
    ).observe(duration_seconds)


def record_webhook_event(
    webhook_type: str,
    event_type: str,
    success: bool,
) -> None:
    """
    Record a webhook event metric.

    Args:
        webhook_type: Webhook source (e.g., "whatsapp", "chatwoot")
        event_type: Event type (e.g., "text", "audio", "message_created")
        success: Whether the event was processed successfully
    """
    status = "success" if success else "error"
    webhook_events_total.labels(
        webhook_type=webhook_type,
        event_type=event_type,
        status=status,
    ).inc()


def record_agent_message(
    message_type: str,
    success: bool,
    duration_seconds: float,
) -> None:
    """
    Record an agent message processing metric.

    Args:
        message_type: Type of message (e.g., "text", "audio")
        success: Whether processing was successful
        duration_seconds: Processing duration in seconds
    """
    status = "success" if success else "error"
    agent_messages_total.labels(
        message_type=message_type,
        status=status,
    ).inc()
    agent_processing_duration_seconds.labels(
        message_type=message_type,
    ).observe(duration_seconds)


# ==================== Context Managers and Decorators ====================


@contextmanager
def track_integration_time(integration: str, operation: str):
    """
    Context manager to track integration call duration.

    Usage:
        with track_integration_time("whatsapp", "send_message"):
            await whatsapp_client.send_message(...)

    Args:
        integration: Integration name
        operation: Operation name

    Yields:
        None (records metrics on exit)
    """
    start_time = time.perf_counter()
    success = True
    try:
        yield
    except Exception:
        success = False
        raise
    finally:
        duration = time.perf_counter() - start_time
        record_integration_request(integration, operation, success, duration)


@contextmanager
def track_operation_time(operation: str):
    """
    Context manager to track operation duration.

    Usage:
        with track_operation_time("process_message"):
            result = await process_message(...)

    Args:
        operation: Operation name

    Yields:
        None (records metrics on exit)
    """
    start_time = time.perf_counter()
    success = True
    try:
        yield
    except Exception:
        success = False
        raise
    finally:
        duration = time.perf_counter() - start_time
        record_operation(operation, success, duration)


def track_integration(integration: str, operation: str):
    """
    Decorator to track integration call metrics.

    Usage:
        @track_integration("whatsapp", "send_message")
        async def send_message(phone: str, text: str) -> bool:
            ...

    Args:
        integration: Integration name
        operation: Operation name
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            success = True
            try:
                result = await func(*args, **kwargs)
                # Check if result indicates success (for functions returning bool)
                if isinstance(result, bool):
                    success = result
                return result
            except Exception:
                success = False
                raise
            finally:
                duration = time.perf_counter() - start_time
                record_integration_request(integration, operation, success, duration)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            success = True
            try:
                result = func(*args, **kwargs)
                if isinstance(result, bool):
                    success = result
                return result
            except Exception:
                success = False
                raise
            finally:
                duration = time.perf_counter() - start_time
                record_integration_request(integration, operation, success, duration)

        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def track_operation_decorator(operation: str):
    """
    Decorator to track operation metrics.

    Usage:
        @track_operation_decorator("classify_temperature")
        def classify_temperature(lead_data: dict) -> str:
            ...

    Args:
        operation: Operation name
    """
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            success = True
            try:
                return await func(*args, **kwargs)
            except Exception:
                success = False
                raise
            finally:
                duration = time.perf_counter() - start_time
                record_operation(operation, success, duration)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            success = True
            try:
                return func(*args, **kwargs)
            except Exception:
                success = False
                raise
            finally:
                duration = time.perf_counter() - start_time
                record_operation(operation, success, duration)

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# ==================== Metrics Export ====================


def get_metrics() -> bytes:
    """
    Generate Prometheus metrics output.

    Returns:
        Metrics in Prometheus text format as bytes
    """
    return generate_latest(METRICS_REGISTRY)


def get_metrics_content_type() -> str:
    """
    Get the content type for Prometheus metrics.

    Returns:
        Content type string
    """
    return CONTENT_TYPE_LATEST


# ==================== Metrics Retrieval (for alerts) ====================


def get_error_rate(
    integration: Optional[str] = None,
    window_seconds: int = 300,
) -> float:
    """
    Calculate error rate for a given integration.

    Note: This is a simplified calculation that doesn't consider time windows.
    For production, use Prometheus queries with PromQL.

    Args:
        integration: Integration name (None for all)
        window_seconds: Time window in seconds (not implemented, placeholder)

    Returns:
        Error rate as a float (0.0 to 1.0)
    """
    # This is a placeholder - actual implementation would query Prometheus
    # or use a time-series database to calculate rates over windows
    logger.debug(
        "get_error_rate called",
        extra={"integration": integration, "window_seconds": window_seconds},
    )
    return 0.0


def get_latency_p95(
    endpoint: Optional[str] = None,
) -> float:
    """
    Get P95 latency for a given endpoint.

    Note: This is a placeholder. Actual P95 calculation requires
    histogram bucket analysis or quantile metrics.

    Args:
        endpoint: Endpoint path (None for all)

    Returns:
        P95 latency in seconds
    """
    # This is a placeholder - actual implementation would calculate
    # from histogram buckets or use Prometheus quantiles
    logger.debug(
        "get_latency_p95 called",
        extra={"endpoint": endpoint},
    )
    return 0.0
