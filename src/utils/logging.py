"""
Structured logging module for Seleto Industrial SDR Agent.

Provides JSON-formatted logs with contextual information per request.
"""

import json
import logging
import sys
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any

from src.config.settings import settings

# Context variables for request-scoped data
request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
phone_var: ContextVar[str | None] = ContextVar("phone", default=None)
flow_step_var: ContextVar[str | None] = ContextVar("flow_step", default=None)


def get_request_id() -> str | None:
    """Get current request ID from context."""
    return request_id_var.get()


def set_request_id(request_id: str | None = None) -> str:
    """Set request ID in context. Generates new UUID if not provided."""
    rid = request_id or str(uuid.uuid4())
    request_id_var.set(rid)
    return rid


def get_phone() -> str | None:
    """Get current phone from context."""
    return phone_var.get()


def set_phone(phone: str | None) -> None:
    """Set phone in context."""
    phone_var.set(phone)


def get_flow_step() -> str | None:
    """Get current flow step from context."""
    return flow_step_var.get()


def set_flow_step(step: str | None) -> None:
    """Set flow step in context."""
    flow_step_var.set(step)


def clear_context() -> None:
    """Clear all context variables."""
    request_id_var.set(None)
    phone_var.set(None)
    flow_step_var.set(None)


class JSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for structured logging.

    Output format:
    {
        "timestamp": "2026-01-03T12:00:00.000Z",
        "level": "INFO",
        "message": "Log message",
        "request_id": "uuid",
        "phone": "+5511999999999",
        "flow_step": "qualification",
        "logger": "src.module",
        "extra": {...}
    }
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }

        # Add context variables if available
        request_id = get_request_id()
        if request_id:
            log_data["request_id"] = request_id

        phone = get_phone()
        if phone:
            log_data["phone"] = phone

        flow_step = get_flow_step()
        if flow_step:
            log_data["flow_step"] = flow_step

        # Add extra fields from record
        extra_fields = {}
        for key, value in record.__dict__.items():
            if key not in (
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "stack_info",
                "exc_info",
                "exc_text",
                "thread",
                "threadName",
                "taskName",
                "message",
            ):
                extra_fields[key] = value

        if extra_fields:
            log_data["extra"] = extra_fields

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, default=str, ensure_ascii=False)


class TextFormatter(logging.Formatter):
    """
    Human-readable text formatter for development.

    Output format:
    2026-01-03 12:00:00 | INFO | [request_id] [phone] message
    """

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        level = record.levelname.ljust(8)

        # Build context prefix
        context_parts = []
        request_id = get_request_id()
        if request_id:
            context_parts.append(f"[{request_id[:8]}]")

        phone = get_phone()
        if phone:
            context_parts.append(f"[{phone}]")

        flow_step = get_flow_step()
        if flow_step:
            context_parts.append(f"[{flow_step}]")

        context = " ".join(context_parts)
        context_str = f" {context}" if context else ""

        message = f"{timestamp} | {level} |{context_str} {record.getMessage()}"

        if record.exc_info:
            message += f"\n{self.formatException(record.exc_info)}"

        return message


def setup_logging() -> logging.Logger:
    """
    Configure and return the application logger.

    Uses LOG_LEVEL and LOG_FORMAT from settings.
    """
    # Get or create logger
    logger = logging.getLogger("seleto_sdr")

    # Avoid duplicate handlers
    if logger.handlers:
        return logger

    # Set level from settings
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)

    # Create handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)

    # Set formatter based on LOG_FORMAT
    if settings.LOG_FORMAT.lower() == "json":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(TextFormatter())

    logger.addHandler(handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name (usually __name__). If None, returns root app logger.

    Returns:
        Configured logger instance.
    """
    if name is None:
        return setup_logging()

    # Create child logger
    parent = setup_logging()
    return parent.getChild(name)


# Convenience functions for common log patterns
def log_webhook_received(
    logger: logging.Logger,
    webhook_type: str,
    phone: str | None = None,
    payload_size: int | None = None,
) -> None:
    """Log incoming webhook."""
    extra = {"webhook_type": webhook_type, "direction": "incoming"}
    if payload_size:
        extra["payload_size"] = payload_size
    logger.info(f"Webhook received: {webhook_type}", extra=extra)


def log_webhook_response(
    logger: logging.Logger,
    webhook_type: str,
    status_code: int,
    duration_ms: float,
) -> None:
    """Log webhook response."""
    logger.info(
        f"Webhook response: {webhook_type} -> {status_code}",
        extra={
            "webhook_type": webhook_type,
            "status_code": status_code,
            "duration_ms": round(duration_ms, 2),
            "direction": "outgoing",
        },
    )


def log_api_call(
    logger: logging.Logger,
    service: str,
    method: str,
    endpoint: str,
    status_code: int | None = None,
    duration_ms: float | None = None,
    error: str | None = None,
) -> None:
    """Log external API call (PipeRun, Supabase, etc.)."""
    extra: dict[str, Any] = {
        "service": service,
        "method": method,
        "endpoint": endpoint,
        "direction": "outgoing",
    }
    if status_code:
        extra["status_code"] = status_code
    if duration_ms:
        extra["duration_ms"] = round(duration_ms, 2)
    if error:
        extra["error"] = error
        logger.error(f"API call failed: {service} {method} {endpoint}", extra=extra)
    else:
        logger.info(f"API call: {service} {method} {endpoint}", extra=extra)


# Initialize logger on module import
logger = setup_logging()

