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
    """Service for Z-API (WhatsApp) interactions."""

    def __init__(self):
        """Initialize WhatsApp service with Z-API configuration."""
        self.instance_id = settings.ZAPI_INSTANCE_ID
        self.instance_token = settings.ZAPI_INSTANCE_TOKEN
        self.client_token = settings.ZAPI_CLIENT_TOKEN
        
        # Construct Z-API URL dynamically
        if self.instance_id and self.instance_token:
            self.api_url = f"https://api.z-api.io/instances/{self.instance_id}/token/{self.instance_token}"
        else:
            self.api_url = None
        
        self.timeout = httpx.Timeout(10.0, connect=5.0)

    def is_configured(self) -> bool:
        """Check if Z-API service is properly configured."""
        return bool(self.instance_id and self.instance_token and self.client_token)

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
            ValueError: If Z-API is not configured
        """
        if not self.is_configured():
            missing = []
            if not self.instance_id:
                missing.append("ZAPI_INSTANCE_ID")
            if not self.instance_token:
                missing.append("ZAPI_INSTANCE_TOKEN")
            if not self.client_token:
                missing.append("ZAPI_CLIENT_TOKEN")
            raise ValueError(
                f"Z-API service not configured. Missing: {', '.join(missing)}"
            )

        normalized_phone = normalize_phone(phone)
        if not normalized_phone:
            logger.error("Invalid phone number provided", extra={"phone": phone})
            return False

        # Set phone in context for logging
        set_phone(normalized_phone)

        # Z-API uses Client-Token header instead of Authorization Bearer
        headers = {
            "Client-Token": self.client_token,
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
                    # Z-API endpoint for sending text messages
                    response = await client.post(
                        f"{self.api_url}/send-text",
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
                        service="z-api",
                        method="POST",
                        endpoint="/send-text",
                        status_code=response.status_code,
                        duration_ms=duration_ms,
                    )

                    # Success
                    if response.status_code in (200, 201):
                        logger.info(
                            "Z-API message sent successfully",
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
                            f"Z-API message send failed: {error_msg}",
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
                        f"Timeout sending Z-API message, retrying in {backoff}s",
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
                        f"Request error sending Z-API message, retrying in {backoff}s",
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
                    "Unexpected error sending Z-API message",
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
            f"Z-API message send failed after {max_retries} attempts",
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

