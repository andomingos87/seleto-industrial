"""
Retry utility module for handling transient failures in external API calls.

TECH-029: Implements retry with exponential backoff for integrations.

This module provides:
- RetryConfig: Configuration dataclass for retry behavior
- is_retryable_error: Function to classify retryable errors
- with_retry: Decorator for sync functions
- with_retry_async: Decorator for async functions
- Logging callbacks for retry attempts

Usage:
    from src.utils.retry import with_retry_async, RetryConfig

    @with_retry_async()
    async def call_external_api():
        ...

    # Or with custom config:
    @with_retry_async(RetryConfig(max_attempts=5, initial_backoff=0.5))
    async def call_critical_api():
        ...
"""

import random
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Callable, ParamSpec, TypeVar

import httpx
from tenacity import (
    AsyncRetrying,
    RetryCallState,
    Retrying,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential_jitter,
)

from src.utils.logging import get_logger

logger = get_logger(__name__)

# Type variables for generic decorators
P = ParamSpec("P")
T = TypeVar("T")


@dataclass
class RetryConfig:
    """
    Configuration for retry behavior.

    Attributes:
        max_attempts: Maximum number of attempts (including first try). Default: 3
        initial_backoff: Initial wait time in seconds. Default: 1.0
        max_backoff: Maximum wait time in seconds. Default: 10.0
        backoff_multiplier: Multiplier for exponential backoff. Default: 2
        jitter: Whether to add random jitter to backoff. Default: True
        retryable_status_codes: HTTP status codes that should trigger retry.
            Default: [429, 500, 502, 503, 504]
    """

    max_attempts: int = 3
    initial_backoff: float = 1.0
    max_backoff: float = 10.0
    backoff_multiplier: int = 2
    jitter: bool = True
    retryable_status_codes: list[int] = field(
        default_factory=lambda: [429, 500, 502, 503, 504]
    )


# Default configuration
DEFAULT_CONFIG = RetryConfig()


class RetryableHTTPError(Exception):
    """
    Exception wrapper for retryable HTTP errors.

    Used to wrap httpx responses with retryable status codes
    so tenacity can properly handle them.
    """

    def __init__(
        self,
        message: str,
        status_code: int,
        response: httpx.Response | None = None,
        retry_after: float | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response = response
        self.retry_after = retry_after


def is_retryable_error(
    error: BaseException,
    config: RetryConfig | None = None,
) -> bool:
    """
    Determine if an error should trigger a retry.

    Retryable errors:
    - httpx.TimeoutException
    - httpx.ConnectError
    - httpx.NetworkError
    - RetryableHTTPError (5xx and 429)

    Non-retryable errors:
    - httpx.HTTPStatusError with 4xx (except 429)
    - ValueError, TypeError, etc.
    - Any other exception not in the retryable list

    Args:
        error: The exception to check
        config: Optional retry configuration

    Returns:
        True if the error is retryable, False otherwise
    """
    cfg = config or DEFAULT_CONFIG

    # Network-level errors are always retryable
    if isinstance(error, (httpx.TimeoutException, httpx.ConnectError)):
        return True

    # Check for NetworkError (parent of ConnectError)
    if isinstance(error, httpx.NetworkError):
        return True

    # Our custom retryable error wrapper
    if isinstance(error, RetryableHTTPError):
        return error.status_code in cfg.retryable_status_codes

    # httpx HTTPStatusError - check status code
    if isinstance(error, httpx.HTTPStatusError):
        return error.response.status_code in cfg.retryable_status_codes

    # All other errors are not retryable
    return False


def _create_retry_predicate(config: RetryConfig) -> Callable[[BaseException], bool]:
    """Create a retry predicate function for tenacity."""

    def predicate(error: BaseException) -> bool:
        return is_retryable_error(error, config)

    return predicate


def _log_retry_attempt(retry_state: RetryCallState) -> None:
    """
    Log each retry attempt.

    Called by tenacity before sleeping between retries.
    """
    attempt = retry_state.attempt_number
    outcome = retry_state.outcome

    if outcome is None:
        return

    exception = outcome.exception()
    if exception is None:
        return

    # Get function name for logging
    fn_name = getattr(retry_state.fn, "__name__", "unknown")

    # Calculate next wait time
    next_wait = 0.0
    if retry_state.next_action and hasattr(retry_state.next_action, "sleep"):
        next_wait = retry_state.next_action.sleep

    # Build log context
    extra: dict[str, Any] = {
        "function": fn_name,
        "attempt": attempt,
        "next_wait_seconds": round(next_wait, 2),
        "error_type": type(exception).__name__,
    }

    # Add status code if available
    if isinstance(exception, RetryableHTTPError):
        extra["status_code"] = exception.status_code
        if exception.retry_after:
            extra["retry_after"] = exception.retry_after
    elif isinstance(exception, httpx.HTTPStatusError):
        extra["status_code"] = exception.response.status_code

    logger.warning(
        f"Retry attempt {attempt} for {fn_name}: {type(exception).__name__}",
        extra=extra,
    )


def _log_retry_exhausted(retry_state: RetryCallState) -> None:
    """
    Log when all retries are exhausted.

    Called by tenacity when max attempts reached.
    """
    attempt = retry_state.attempt_number
    outcome = retry_state.outcome

    if outcome is None:
        return

    exception = outcome.exception()
    fn_name = getattr(retry_state.fn, "__name__", "unknown")

    extra: dict[str, Any] = {
        "function": fn_name,
        "total_attempts": attempt,
        "error_type": type(exception).__name__ if exception else "unknown",
    }

    if isinstance(exception, RetryableHTTPError):
        extra["status_code"] = exception.status_code
    elif isinstance(exception, httpx.HTTPStatusError):
        extra["status_code"] = exception.response.status_code

    logger.error(
        f"All retries exhausted for {fn_name} after {attempt} attempts",
        extra=extra,
    )


def _log_retry_attempt_simple(
    func: Callable,
    attempt: int,
    exception: BaseException,
    next_wait: float,
) -> None:
    """Log a retry attempt with simple parameters."""
    fn_name = getattr(func, "__name__", "unknown")

    extra: dict[str, Any] = {
        "function": fn_name,
        "attempt": attempt,
        "next_wait_seconds": round(next_wait, 2),
        "error_type": type(exception).__name__,
    }

    if isinstance(exception, RetryableHTTPError):
        extra["status_code"] = exception.status_code
        if exception.retry_after:
            extra["retry_after"] = exception.retry_after
    elif isinstance(exception, httpx.HTTPStatusError):
        extra["status_code"] = exception.response.status_code

    logger.warning(
        f"Retry attempt {attempt} for {fn_name}: {type(exception).__name__}",
        extra=extra,
    )


def _log_retry_exhausted_simple(
    func: Callable,
    total_attempts: int,
    exception: BaseException,
) -> None:
    """Log when all retries are exhausted with simple parameters."""
    fn_name = getattr(func, "__name__", "unknown")

    extra: dict[str, Any] = {
        "function": fn_name,
        "total_attempts": total_attempts,
        "error_type": type(exception).__name__,
    }

    if isinstance(exception, RetryableHTTPError):
        extra["status_code"] = exception.status_code
    elif isinstance(exception, httpx.HTTPStatusError):
        extra["status_code"] = exception.response.status_code

    logger.error(
        f"All retries exhausted for {fn_name} after {total_attempts} attempts",
        extra=extra,
    )


def with_retry(
    config: RetryConfig | None = None,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator for synchronous functions with retry logic.

    Uses tenacity with exponential backoff and jitter.

    Args:
        config: Optional RetryConfig. Uses DEFAULT_CONFIG if not provided.

    Returns:
        Decorated function with retry behavior.

    Example:
        @with_retry()
        def call_api():
            response = requests.get("https://api.example.com")
            response.raise_for_status()
            return response.json()

        @with_retry(RetryConfig(max_attempts=5))
        def call_critical_api():
            ...
    """
    cfg = config or DEFAULT_CONFIG

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            last_exception: BaseException | None = None

            for attempt_number in range(1, cfg.max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except BaseException as e:
                    last_exception = e

                    # Check if we should retry
                    if not is_retryable_error(e, cfg):
                        raise

                    # Check if we have more attempts
                    if attempt_number >= cfg.max_attempts:
                        _log_retry_exhausted_simple(func, attempt_number, e)
                        raise

                    # Calculate wait time
                    wait_time = get_retry_after_or_backoff(e, attempt_number, cfg)

                    # Log retry attempt
                    _log_retry_attempt_simple(func, attempt_number, e, wait_time)

                    # Wait before retry
                    import time
                    time.sleep(wait_time)

            # This should never be reached
            if last_exception:
                raise last_exception
            raise RuntimeError("Retry loop exited unexpectedly")

        return wrapper

    return decorator


def with_retry_async(
    config: RetryConfig | None = None,
) -> Callable[[Callable[P, T]], Callable[P, T]]:
    """
    Decorator for asynchronous functions with retry logic.

    Uses exponential backoff and jitter.

    Args:
        config: Optional RetryConfig. Uses DEFAULT_CONFIG if not provided.

    Returns:
        Decorated async function with retry behavior.

    Example:
        @with_retry_async()
        async def call_api():
            async with httpx.AsyncClient() as client:
                response = await client.get("https://api.example.com")
                response.raise_for_status()
                return response.json()

        @with_retry_async(RetryConfig(max_attempts=5))
        async def call_critical_api():
            ...
    """
    cfg = config or DEFAULT_CONFIG

    def decorator(func: Callable[P, T]) -> Callable[P, T]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            import asyncio

            last_exception: BaseException | None = None

            for attempt_number in range(1, cfg.max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except BaseException as e:
                    last_exception = e

                    # Check if we should retry
                    if not is_retryable_error(e, cfg):
                        raise

                    # Check if we have more attempts
                    if attempt_number >= cfg.max_attempts:
                        _log_retry_exhausted_simple(func, attempt_number, e)
                        raise

                    # Calculate wait time
                    wait_time = get_retry_after_or_backoff(e, attempt_number, cfg)

                    # Log retry attempt
                    _log_retry_attempt_simple(func, attempt_number, e, wait_time)

                    # Wait before retry
                    await asyncio.sleep(wait_time)

            # This should never be reached
            if last_exception:
                raise last_exception
            raise RuntimeError("Retry loop exited unexpectedly")

        return wrapper

    return decorator


def check_response_for_retry(
    response: httpx.Response,
    config: RetryConfig | None = None,
) -> None:
    """
    Check HTTP response and raise RetryableHTTPError if status code is retryable.

    This function should be called after making an HTTP request to determine
    if the response indicates a retryable error.

    Args:
        response: The httpx Response object
        config: Optional retry configuration

    Raises:
        RetryableHTTPError: If status code is in retryable list (429, 5xx)

    Example:
        @with_retry_async()
        async def call_api():
            async with httpx.AsyncClient() as client:
                response = await client.get("https://api.example.com")
                check_response_for_retry(response)
                return response.json()
    """
    cfg = config or DEFAULT_CONFIG

    if response.status_code in cfg.retryable_status_codes:
        # Try to get Retry-After header for 429
        retry_after = None
        if response.status_code == 429:
            retry_after_header = response.headers.get("Retry-After")
            if retry_after_header:
                try:
                    retry_after = float(retry_after_header)
                except ValueError:
                    pass

        raise RetryableHTTPError(
            f"HTTP {response.status_code}: {response.reason_phrase}",
            status_code=response.status_code,
            response=response,
            retry_after=retry_after,
        )


def get_retry_after_or_backoff(
    error: BaseException,
    attempt: int,
    config: RetryConfig | None = None,
) -> float:
    """
    Get the wait time before next retry.

    Uses Retry-After header if available (for 429), otherwise
    calculates exponential backoff with jitter.

    Args:
        error: The exception that triggered retry
        attempt: Current attempt number (1-based)
        config: Optional retry configuration

    Returns:
        Wait time in seconds
    """
    cfg = config or DEFAULT_CONFIG

    # Check for Retry-After in our custom error
    if isinstance(error, RetryableHTTPError) and error.retry_after:
        return error.retry_after

    # Check for Retry-After in httpx error
    if isinstance(error, httpx.HTTPStatusError):
        retry_after_header = error.response.headers.get("Retry-After")
        if retry_after_header:
            try:
                return float(retry_after_header)
            except ValueError:
                pass

    # Calculate exponential backoff
    backoff = cfg.initial_backoff * (cfg.backoff_multiplier ** (attempt - 1))
    backoff = min(backoff, cfg.max_backoff)

    # Add jitter if enabled
    if cfg.jitter:
        jitter = random.uniform(0, backoff * 0.5)
        backoff += jitter

    return backoff
