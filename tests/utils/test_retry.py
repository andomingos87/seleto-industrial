"""
Tests for retry utility module (TECH-029).

This module tests the retry decorators and helper functions
for handling transient failures in external API calls.
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.utils.retry import (
    DEFAULT_CONFIG,
    RetryableHTTPError,
    RetryConfig,
    check_response_for_retry,
    get_retry_after_or_backoff,
    is_retryable_error,
    with_retry,
    with_retry_async,
)


class TestRetryConfig:
    """Tests for retry configuration."""

    def test_default_config_values(self):
        """Test default retry configuration values."""
        config = RetryConfig()
        assert config.max_attempts == 3
        assert config.initial_backoff == 1.0
        assert config.max_backoff == 10.0
        assert config.backoff_multiplier == 2
        assert config.jitter is True
        assert 429 in config.retryable_status_codes
        assert 500 in config.retryable_status_codes
        assert 502 in config.retryable_status_codes
        assert 503 in config.retryable_status_codes
        assert 504 in config.retryable_status_codes

    def test_custom_config(self):
        """Test custom retry configuration."""
        config = RetryConfig(
            max_attempts=5,
            initial_backoff=0.5,
            max_backoff=30.0,
            jitter=False,
        )
        assert config.max_attempts == 5
        assert config.initial_backoff == 0.5
        assert config.max_backoff == 30.0
        assert config.jitter is False

    def test_default_config_singleton(self):
        """Test that DEFAULT_CONFIG is properly initialized."""
        assert DEFAULT_CONFIG.max_attempts == 3
        assert DEFAULT_CONFIG.initial_backoff == 1.0


class TestIsRetryableError:
    """Tests for error classification logic."""

    def test_timeout_is_retryable(self):
        """Test that timeout exceptions are retryable."""
        error = httpx.TimeoutException("Request timed out")
        assert is_retryable_error(error) is True

    def test_connect_error_is_retryable(self):
        """Test that connection errors are retryable."""
        error = httpx.ConnectError("Connection failed")
        assert is_retryable_error(error) is True

    def test_network_error_is_retryable(self):
        """Test that network errors are retryable."""
        # ConnectError is a subclass of NetworkError
        error = httpx.NetworkError("Network unreachable")
        assert is_retryable_error(error) is True

    def test_retryable_http_error_500_is_retryable(self):
        """Test that 500 errors are retryable."""
        error = RetryableHTTPError("Server error", status_code=500)
        assert is_retryable_error(error) is True

    def test_retryable_http_error_502_is_retryable(self):
        """Test that 502 errors are retryable."""
        error = RetryableHTTPError("Bad gateway", status_code=502)
        assert is_retryable_error(error) is True

    def test_retryable_http_error_503_is_retryable(self):
        """Test that 503 errors are retryable."""
        error = RetryableHTTPError("Service unavailable", status_code=503)
        assert is_retryable_error(error) is True

    def test_retryable_http_error_504_is_retryable(self):
        """Test that 504 errors are retryable."""
        error = RetryableHTTPError("Gateway timeout", status_code=504)
        assert is_retryable_error(error) is True

    def test_retryable_http_error_429_is_retryable(self):
        """Test that 429 (rate limit) errors are retryable."""
        error = RetryableHTTPError("Too many requests", status_code=429)
        assert is_retryable_error(error) is True

    def test_retryable_http_error_400_not_retryable(self):
        """Test that 400 errors are NOT retryable."""
        error = RetryableHTTPError("Bad request", status_code=400)
        assert is_retryable_error(error) is False

    def test_retryable_http_error_401_not_retryable(self):
        """Test that 401 errors are NOT retryable."""
        error = RetryableHTTPError("Unauthorized", status_code=401)
        assert is_retryable_error(error) is False

    def test_retryable_http_error_403_not_retryable(self):
        """Test that 403 errors are NOT retryable."""
        error = RetryableHTTPError("Forbidden", status_code=403)
        assert is_retryable_error(error) is False

    def test_retryable_http_error_404_not_retryable(self):
        """Test that 404 errors are NOT retryable."""
        error = RetryableHTTPError("Not found", status_code=404)
        assert is_retryable_error(error) is False

    def test_retryable_http_error_422_not_retryable(self):
        """Test that 422 errors are NOT retryable."""
        error = RetryableHTTPError("Unprocessable entity", status_code=422)
        assert is_retryable_error(error) is False

    def test_value_error_not_retryable(self):
        """Test that ValueError is NOT retryable."""
        error = ValueError("Invalid input")
        assert is_retryable_error(error) is False

    def test_type_error_not_retryable(self):
        """Test that TypeError is NOT retryable."""
        error = TypeError("Wrong type")
        assert is_retryable_error(error) is False

    def test_generic_exception_not_retryable(self):
        """Test that generic exceptions are NOT retryable."""
        error = Exception("Something went wrong")
        assert is_retryable_error(error) is False

    def test_custom_config_retryable_codes(self):
        """Test custom retryable status codes."""
        config = RetryConfig(retryable_status_codes=[418, 503])

        error_418 = RetryableHTTPError("I'm a teapot", status_code=418)
        assert is_retryable_error(error_418, config) is True

        error_500 = RetryableHTTPError("Server error", status_code=500)
        assert is_retryable_error(error_500, config) is False


class TestRetryableHTTPError:
    """Tests for RetryableHTTPError exception."""

    def test_error_with_status_code(self):
        """Test creating error with status code."""
        error = RetryableHTTPError("Server error", status_code=500)
        assert error.status_code == 500
        assert str(error) == "Server error"

    def test_error_with_retry_after(self):
        """Test creating error with retry_after."""
        error = RetryableHTTPError(
            "Rate limited",
            status_code=429,
            retry_after=30.0,
        )
        assert error.status_code == 429
        assert error.retry_after == 30.0

    def test_error_with_response(self):
        """Test creating error with response object."""
        mock_response = MagicMock(spec=httpx.Response)
        error = RetryableHTTPError(
            "Server error",
            status_code=500,
            response=mock_response,
        )
        assert error.response is mock_response


class TestCheckResponseForRetry:
    """Tests for check_response_for_retry function."""

    def test_raises_on_500(self):
        """Test that 500 raises RetryableHTTPError."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 500
        mock_response.reason_phrase = "Internal Server Error"
        mock_response.headers = {}

        with pytest.raises(RetryableHTTPError) as exc_info:
            check_response_for_retry(mock_response)

        assert exc_info.value.status_code == 500

    def test_raises_on_429_with_retry_after(self):
        """Test that 429 captures Retry-After header."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 429
        mock_response.reason_phrase = "Too Many Requests"
        mock_response.headers = {"Retry-After": "60"}

        with pytest.raises(RetryableHTTPError) as exc_info:
            check_response_for_retry(mock_response)

        assert exc_info.value.status_code == 429
        assert exc_info.value.retry_after == 60.0

    def test_does_not_raise_on_200(self):
        """Test that 200 does not raise."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.headers = {}

        # Should not raise
        check_response_for_retry(mock_response)

    def test_does_not_raise_on_400(self):
        """Test that 400 does not raise (not retryable)."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 400
        mock_response.headers = {}

        # Should not raise
        check_response_for_retry(mock_response)


class TestGetRetryAfterOrBackoff:
    """Tests for get_retry_after_or_backoff function."""

    def test_uses_retry_after_from_error(self):
        """Test that Retry-After from error is used."""
        error = RetryableHTTPError("Rate limited", status_code=429, retry_after=30.0)
        wait_time = get_retry_after_or_backoff(error, attempt=1)
        assert wait_time == 30.0

    def test_exponential_backoff_attempt_1(self):
        """Test exponential backoff for first attempt."""
        config = RetryConfig(initial_backoff=1.0, backoff_multiplier=2, jitter=False)
        error = RetryableHTTPError("Server error", status_code=500)
        wait_time = get_retry_after_or_backoff(error, attempt=1, config=config)
        assert wait_time == 1.0

    def test_exponential_backoff_attempt_2(self):
        """Test exponential backoff for second attempt."""
        config = RetryConfig(initial_backoff=1.0, backoff_multiplier=2, jitter=False)
        error = RetryableHTTPError("Server error", status_code=500)
        wait_time = get_retry_after_or_backoff(error, attempt=2, config=config)
        assert wait_time == 2.0

    def test_exponential_backoff_attempt_3(self):
        """Test exponential backoff for third attempt."""
        config = RetryConfig(initial_backoff=1.0, backoff_multiplier=2, jitter=False)
        error = RetryableHTTPError("Server error", status_code=500)
        wait_time = get_retry_after_or_backoff(error, attempt=3, config=config)
        assert wait_time == 4.0

    def test_max_backoff_respected(self):
        """Test that max_backoff is not exceeded."""
        config = RetryConfig(
            initial_backoff=1.0,
            backoff_multiplier=2,
            max_backoff=5.0,
            jitter=False,
        )
        error = RetryableHTTPError("Server error", status_code=500)
        wait_time = get_retry_after_or_backoff(error, attempt=10, config=config)
        assert wait_time == 5.0

    def test_jitter_adds_randomness(self):
        """Test that jitter adds variation to backoff."""
        config = RetryConfig(initial_backoff=1.0, backoff_multiplier=2, jitter=True)
        error = RetryableHTTPError("Server error", status_code=500)

        # Get multiple values and check they're not all the same
        values = [get_retry_after_or_backoff(error, attempt=1, config=config) for _ in range(10)]

        # With jitter, values should vary
        assert len(set(values)) > 1  # At least some variation


class TestSyncRetryDecorator:
    """Tests for synchronous retry decorator."""

    def test_success_no_retry(self):
        """Test successful call doesn't trigger retry."""
        call_count = 0

        @with_retry()
        def successful_function():
            nonlocal call_count
            call_count += 1
            return "success"

        result = successful_function()
        assert result == "success"
        assert call_count == 1

    def test_retry_on_timeout(self):
        """Test retry happens on timeout."""
        call_count = 0

        @with_retry(RetryConfig(max_attempts=3, initial_backoff=0.01))
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise httpx.TimeoutException("Timeout")
            return "success"

        result = flaky_function()
        assert result == "success"
        assert call_count == 3

    def test_retry_on_connect_error(self):
        """Test retry happens on connection error."""
        call_count = 0

        @with_retry(RetryConfig(max_attempts=3, initial_backoff=0.01))
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise httpx.ConnectError("Connection failed")
            return "success"

        result = flaky_function()
        assert result == "success"
        assert call_count == 2

    def test_retry_on_server_error(self):
        """Test retry happens on 5xx error."""
        call_count = 0

        @with_retry(RetryConfig(max_attempts=3, initial_backoff=0.01))
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise RetryableHTTPError("Server error", status_code=500)
            return "success"

        result = flaky_function()
        assert result == "success"
        assert call_count == 2

    def test_max_retries_exhausted(self):
        """Test that error is raised after max retries."""
        call_count = 0

        @with_retry(RetryConfig(max_attempts=3, initial_backoff=0.01))
        def always_failing():
            nonlocal call_count
            call_count += 1
            raise httpx.TimeoutException("Timeout")

        with pytest.raises(httpx.TimeoutException):
            always_failing()

        assert call_count == 3

    def test_no_retry_on_client_error(self):
        """Test that 4xx errors don't trigger retry."""
        call_count = 0

        @with_retry(RetryConfig(max_attempts=3, initial_backoff=0.01))
        def client_error_function():
            nonlocal call_count
            call_count += 1
            raise RetryableHTTPError("Bad request", status_code=400)

        with pytest.raises(RetryableHTTPError):
            client_error_function()

        assert call_count == 1  # No retry

    def test_no_retry_on_value_error(self):
        """Test that ValueError doesn't trigger retry."""
        call_count = 0

        @with_retry(RetryConfig(max_attempts=3, initial_backoff=0.01))
        def validation_error_function():
            nonlocal call_count
            call_count += 1
            raise ValueError("Invalid input")

        with pytest.raises(ValueError):
            validation_error_function()

        assert call_count == 1  # No retry


class TestAsyncRetryDecorator:
    """Tests for asynchronous retry decorator."""

    @pytest.mark.asyncio
    async def test_async_success_no_retry(self):
        """Test successful async call doesn't trigger retry."""
        call_count = 0

        @with_retry_async()
        async def successful_function():
            nonlocal call_count
            call_count += 1
            return "success"

        result = await successful_function()
        assert result == "success"
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_async_retry_on_timeout(self):
        """Test async retry happens on timeout."""
        call_count = 0

        @with_retry_async(RetryConfig(max_attempts=3, initial_backoff=0.01))
        async def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise httpx.TimeoutException("Timeout")
            return "success"

        result = await flaky_function()
        assert result == "success"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_async_retry_on_connect_error(self):
        """Test async retry happens on connection error."""
        call_count = 0

        @with_retry_async(RetryConfig(max_attempts=3, initial_backoff=0.01))
        async def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise httpx.ConnectError("Connection failed")
            return "success"

        result = await flaky_function()
        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_async_retry_on_server_error(self):
        """Test async retry happens on 5xx error."""
        call_count = 0

        @with_retry_async(RetryConfig(max_attempts=3, initial_backoff=0.01))
        async def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise RetryableHTTPError("Server error", status_code=500)
            return "success"

        result = await flaky_function()
        assert result == "success"
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_async_max_retries_exhausted(self):
        """Test that error is raised after max async retries."""
        call_count = 0

        @with_retry_async(RetryConfig(max_attempts=3, initial_backoff=0.01))
        async def always_failing():
            nonlocal call_count
            call_count += 1
            raise httpx.TimeoutException("Timeout")

        with pytest.raises(httpx.TimeoutException):
            await always_failing()

        assert call_count == 3

    @pytest.mark.asyncio
    async def test_async_no_retry_on_client_error(self):
        """Test that 4xx errors don't trigger async retry."""
        call_count = 0

        @with_retry_async(RetryConfig(max_attempts=3, initial_backoff=0.01))
        async def client_error_function():
            nonlocal call_count
            call_count += 1
            raise RetryableHTTPError("Unauthorized", status_code=401)

        with pytest.raises(RetryableHTTPError):
            await client_error_function()

        assert call_count == 1  # No retry

    @pytest.mark.asyncio
    async def test_async_no_retry_on_value_error(self):
        """Test that ValueError doesn't trigger async retry."""
        call_count = 0

        @with_retry_async(RetryConfig(max_attempts=3, initial_backoff=0.01))
        async def validation_error_function():
            nonlocal call_count
            call_count += 1
            raise ValueError("Invalid input")

        with pytest.raises(ValueError):
            await validation_error_function()

        assert call_count == 1  # No retry


class TestRetryLogging:
    """Tests for retry logging behavior."""

    def test_logs_retry_attempt(self):
        """Test that retry attempts are logged."""
        call_count = 0

        @with_retry(RetryConfig(max_attempts=2, initial_backoff=0.01))
        def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise httpx.TimeoutException("Timeout")
            return "success"

        with patch("src.utils.retry.logger") as mock_logger:
            result = flaky_function()

        assert result == "success"
        # Should have logged the retry attempt
        mock_logger.warning.assert_called()

    def test_logs_final_failure(self):
        """Test that final failure is logged as ERROR."""

        @with_retry(RetryConfig(max_attempts=2, initial_backoff=0.01))
        def always_failing():
            raise httpx.TimeoutException("Timeout")

        with patch("src.utils.retry.logger") as mock_logger:
            with pytest.raises(httpx.TimeoutException):
                always_failing()

        # Should have logged the error
        mock_logger.error.assert_called()


class TestRateLimitHandling:
    """Tests for rate limit (429) handling."""

    def test_retry_on_429(self):
        """Test that 429 triggers retry."""
        call_count = 0

        @with_retry(RetryConfig(max_attempts=3, initial_backoff=0.01))
        def rate_limited_function():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise RetryableHTTPError("Rate limited", status_code=429)
            return "success"

        result = rate_limited_function()
        assert result == "success"
        assert call_count == 2
