"""
Logging middleware for FastAPI.

Provides request/response logging with contextual information.
"""

import time
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.utils.logging import (
    clear_context,
    get_logger,
    log_webhook_received,
    log_webhook_response,
    set_phone,
    set_request_id,
)

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs all HTTP requests and responses.

    Features:
    - Generates unique request_id for each request
    - Extracts phone from request body for webhook requests
    - Logs request entry and exit with timing
    - Cleans up context after request
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID from header or create new one
        request_id = request.headers.get("X-Request-ID")
        set_request_id(request_id)

        # Start timing
        start_time = time.perf_counter()

        # Determine if this is a webhook request
        is_webhook = "/webhook" in request.url.path

        # Try to extract phone from webhook requests
        if is_webhook and request.method == "POST":
            try:
                # Clone body for reading (body can only be read once)
                body = await request.body()

                # Store body for later use by route handlers
                request.state.body = body

                # Try to extract phone from JSON body
                import json

                try:
                    data = json.loads(body)
                    phone = data.get("phone") or data.get("from") or data.get("sender")
                    if phone:
                        set_phone(str(phone))
                except (json.JSONDecodeError, AttributeError):
                    pass

                # Log webhook received
                log_webhook_received(
                    logger,
                    webhook_type=request.url.path.split("/")[-1],
                    phone=phone if "phone" in dir() else None,
                    payload_size=len(body),
                )
            except Exception:
                # Don't fail request if logging fails
                pass
        else:
            # Log regular request
            logger.info(
                f"Request: {request.method} {request.url.path}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "client_ip": request.client.host if request.client else None,
                },
            )

        # Process request
        try:
            response = await call_next(request)
        except Exception as e:
            # Log exception
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.exception(
                f"Request failed: {request.method} {request.url.path}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": round(duration_ms, 2),
                    "error": str(e),
                },
            )
            raise
        finally:
            # Clean up context
            clear_context()

        # Calculate duration
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Log response
        if is_webhook:
            log_webhook_response(
                logger,
                webhook_type=request.url.path.split("/")[-1],
                status_code=response.status_code,
                duration_ms=duration_ms,
            )
        else:
            logger.info(
                f"Response: {request.method} {request.url.path} -> {response.status_code}",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                },
            )

        # Add request ID to response headers
        from src.utils.logging import get_request_id

        rid = get_request_id()
        if rid:
            response.headers["X-Request-ID"] = rid

        return response

