"""
WhatsApp service for sending and receiving messages.
"""

import asyncio
import time
from typing import Optional

import httpx
from src.config.settings import settings
from src.utils.logging import get_logger, log_api_call, set_phone
from src.utils.validation import normalize_phone

logger = get_logger(__name__)


class WhatsAppService:
    """Service for WhatsApp API interactions."""

    def __init__(self):
        """Initialize WhatsApp service with API configuration."""
        self.api_url = settings.WHATSAPP_API_URL
        self.api_token = settings.WHATSAPP_API_TOKEN
        self.timeout = httpx.Timeout(10.0, connect=5.0)

    async def send_message(
        self,
        phone: str,
        text: str,
        max_retries: int = 3,
        initial_backoff: float = 1.0,
    ) -> bool:
        """
        Send WhatsApp message with retry and exponential backoff.

        Args:
            phone: Phone number (will be normalized to E.164)
            text: Message text to send
            max_retries: Maximum number of retry attempts (default: 3)
            initial_backoff: Initial backoff delay in seconds (default: 1.0)

        Returns:
            True if message was sent successfully, False otherwise

        Raises:
            ValueError: If WhatsApp API URL or token is not configured
        """
        if not self.api_url or not self.api_token:
            raise ValueError(
                "WhatsApp API URL and token must be configured via environment variables"
            )

        normalized_phone = normalize_phone(phone)
        if not normalized_phone:
            logger.error("Invalid phone number provided", extra={"phone": phone})
            return False

        # Set phone in context for logging
        set_phone(normalized_phone)

        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

        payload = {
            "phone": normalized_phone,
            "message": text,
        }

        # Retry logic with exponential backoff
        last_error: Optional[Exception] = None
        for attempt in range(max_retries):
            try:
                start_time = time.perf_counter()
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.api_url}/messages",
                        json=payload,
                        headers=headers,
                    )

                    duration_ms = (time.perf_counter() - start_time) * 1000

                    # Check for rate limiting (429)
                    if response.status_code == 429:
                        retry_after = int(
                            response.headers.get("Retry-After", initial_backoff * (2**attempt))
                        )
                        logger.warning(
                            f"Rate limited, waiting {retry_after}s before retry",
                            extra={
                                "phone": normalized_phone,
                                "attempt": attempt + 1,
                                "retry_after": retry_after,
                            },
                        )
                        if attempt < max_retries - 1:
                            await asyncio.sleep(retry_after)
                            continue

                    # Log API call
                    log_api_call(
                        logger,
                        service="whatsapp",
                        method="POST",
                        endpoint="/messages",
                        status_code=response.status_code,
                        duration_ms=duration_ms,
                    )

                    # Success
                    if response.status_code in (200, 201):
                        logger.info(
                            f"WhatsApp message sent successfully",
                            extra={
                                "phone": normalized_phone,
                                "status_code": response.status_code,
                                "attempt": attempt + 1,
                            },
                        )
                        return True

                    # Client errors (4xx) - don't retry except 429
                    if 400 <= response.status_code < 500:
                        error_msg = f"Client error: {response.status_code}"
                        try:
                            error_data = response.json()
                            error_msg = error_data.get("error", error_msg)
                        except Exception:
                            pass

                        logger.error(
                            f"WhatsApp message send failed: {error_msg}",
                            extra={
                                "phone": normalized_phone,
                                "status_code": response.status_code,
                                "attempt": attempt + 1,
                            },
                        )
                        return False

                    # Server errors (5xx) - retry
                    if attempt < max_retries - 1:
                        backoff = initial_backoff * (2**attempt)
                        logger.warning(
                            f"Server error, retrying in {backoff}s",
                            extra={
                                "phone": normalized_phone,
                                "status_code": response.status_code,
                                "attempt": attempt + 1,
                                "backoff": backoff,
                            },
                        )
                        await asyncio.sleep(backoff)
                        continue

            except httpx.TimeoutException as e:
                last_error = e
                if attempt < max_retries - 1:
                    backoff = initial_backoff * (2**attempt)
                    logger.warning(
                        f"Timeout sending WhatsApp message, retrying in {backoff}s",
                        extra={
                            "phone": normalized_phone,
                            "attempt": attempt + 1,
                            "backoff": backoff,
                        },
                    )
                    await asyncio.sleep(backoff)
                    continue

            except httpx.RequestError as e:
                last_error = e
                if attempt < max_retries - 1:
                    backoff = initial_backoff * (2**attempt)
                    logger.warning(
                        f"Request error sending WhatsApp message, retrying in {backoff}s",
                        extra={
                            "phone": normalized_phone,
                            "attempt": attempt + 1,
                            "backoff": backoff,
                            "error": str(e),
                        },
                    )
                    await asyncio.sleep(backoff)
                    continue

            except Exception as e:
                last_error = e
                logger.error(
                    f"Unexpected error sending WhatsApp message",
                    extra={
                        "phone": normalized_phone,
                        "attempt": attempt + 1,
                        "error": str(e),
                    },
                    exc_info=True,
                )
                if attempt < max_retries - 1:
                    backoff = initial_backoff * (2**attempt)
                    await asyncio.sleep(backoff)
                    continue

        # All retries exhausted
        logger.error(
            f"WhatsApp message send failed after {max_retries} attempts",
            extra={
                "phone": normalized_phone,
                "max_retries": max_retries,
                "last_error": str(last_error) if last_error else None,
            },
        )
        return False


# Global service instance
whatsapp_service = WhatsAppService()


async def send_whatsapp_message(phone: str, text: str) -> bool:
    """
    Convenience function to send WhatsApp message.

    Args:
        phone: Phone number (will be normalized)
        text: Message text

    Returns:
        True if sent successfully, False otherwise
    """
    return await whatsapp_service.send_message(phone, text)

