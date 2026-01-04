"""
Webhook endpoints for receiving messages from external services.
"""

import asyncio
import time
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Request, Response, status
from pydantic import BaseModel, Field

from src.agents.sdr_agent import process_message
from src.config.settings import settings
from src.services.transcription import transcribe_audio
from src.services.whatsapp import send_whatsapp_message
from src.utils.logging import (
    get_logger,
    log_webhook_received,
    log_webhook_response,
    set_phone,
)
from src.utils.validation import normalize_phone, validate_phone

router = APIRouter()
logger = get_logger(__name__)


class TextMessagePayload(BaseModel):
    """Payload for text message webhook."""

    phone: str = Field(..., description="Phone number of the sender")
    senderName: Optional[str] = Field(None, description="Name of the sender")
    message: str = Field(..., description="Text message content")
    messageId: Optional[str] = Field(None, description="Unique message ID")


class AudioMessagePayload(BaseModel):
    """Payload for audio message webhook."""

    phone: str = Field(..., description="Phone number of the sender")
    senderName: Optional[str] = Field(None, description="Name of the sender")
    audio: dict = Field(
        ...,
        description="Audio object with audioUrl, mimeType, and seconds",
    )
    messageId: Optional[str] = Field(None, description="Unique message ID")


class WhatsAppWebhookPayload(BaseModel):
    """Generic WhatsApp webhook payload that can handle text or audio."""

    phone: str = Field(..., description="Phone number of the sender")
    senderName: Optional[str] = Field(None, description="Name of the sender")
    message: Optional[str] = Field(None, description="Text message content (if text)")
    audio: Optional[dict] = Field(
        None, description="Audio object (if audio message)"
    )
    messageId: Optional[str] = Field(None, description="Unique message ID")
    messageType: Optional[str] = Field(
        "text", description="Type of message: 'text' or 'audio'"
    )


def validate_webhook_auth(
    authorization: Optional[str] = Header(None),
    x_webhook_secret: Optional[str] = Header(None),
) -> bool:
    """
    Validate webhook authentication token/secret.

    Args:
        authorization: Authorization header (Bearer token)
        x_webhook_secret: X-Webhook-Secret header

    Returns:
        True if authentication is valid, False otherwise

    Raises:
        HTTPException: If authentication fails
    """
    webhook_secret = settings.WHATSAPP_WEBHOOK_SECRET

    # If no secret is configured, skip validation (development mode)
    if not webhook_secret:
        logger.warning("WhatsApp webhook secret not configured, skipping validation")
        return True

    # Check X-Webhook-Secret header first (common pattern)
    if x_webhook_secret and x_webhook_secret == webhook_secret:
        return True

    # Check Authorization header (Bearer token)
    if authorization:
        if authorization.startswith("Bearer "):
            token = authorization[7:]
            if token == webhook_secret:
                return True

    # Authentication failed
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid webhook authentication",
    )


async def process_text_message(payload: WhatsAppWebhookPayload) -> dict:
    """
    Process incoming text message.

    Args:
        payload: Webhook payload with text message

    Returns:
        Processing result dictionary
    """
    normalized_phone = normalize_phone(payload.phone)
    if not validate_phone(normalized_phone):
        logger.warning(
            f"Invalid phone number format: {payload.phone}",
            extra={"phone": payload.phone, "normalized": normalized_phone},
        )

    # Set phone in context for logging
    set_phone(normalized_phone)

    logger.info(
        "Text message received",
        extra={
            "phone": normalized_phone,
            "sender_name": payload.senderName,
            "message_length": len(payload.message) if payload.message else 0,
            "message_id": payload.messageId,
        },
    )

    # Process message with agent (US-001)
    try:
        response_text = await process_message(
            phone=normalized_phone,
            message=payload.message or "",
            sender_name=payload.senderName,
        )

        # Send response via WhatsApp
        if response_text:
            success = await send_whatsapp_message(normalized_phone, response_text)
            if not success:
                logger.error(
                    "Failed to send WhatsApp response",
                    extra={"phone": normalized_phone},
                )
        else:
            logger.warning(
                "Empty response from agent, not sending",
                extra={"phone": normalized_phone},
            )

    except Exception as e:
        logger.error(
            "Error processing message with agent",
            extra={
                "phone": normalized_phone,
                "error": str(e),
            },
            exc_info=True,
        )
        # Send fallback message
        fallback_message = (
            "Olá! Seja bem-vindo à Seleto Industrial 👋\n"
            "Desculpe, tive um problema técnico. Pode repetir sua mensagem?"
        )
        await send_whatsapp_message(normalized_phone, fallback_message)

    return {
        "status": "processed",
        "phone": normalized_phone,
        "message_type": "text",
        "message_length": len(payload.message) if payload.message else 0,
    }


async def process_audio_message(payload: WhatsAppWebhookPayload) -> dict:
    """
    Process incoming audio message: download and transcribe.

    Args:
        payload: Webhook payload with audio message

    Returns:
        Processing result dictionary with transcribed text
    """
    normalized_phone = normalize_phone(payload.phone)
    if not validate_phone(normalized_phone):
        logger.warning(
            f"Invalid phone number format: {payload.phone}",
            extra={"phone": payload.phone, "normalized": normalized_phone},
        )

    # Set phone in context for logging
    set_phone(normalized_phone)

    if not payload.audio:
        logger.error(
            "Audio message received but audio object is missing",
            extra={"phone": normalized_phone},
        )
        return {
            "status": "error",
            "error": "Audio object missing",
            "phone": normalized_phone,
        }

    audio_url = payload.audio.get("audioUrl")
    mime_type = payload.audio.get("mimeType")
    duration_seconds = payload.audio.get("seconds")

    if not audio_url:
        logger.error(
            "Audio message received but audioUrl is missing",
            extra={"phone": normalized_phone},
        )
        return {
            "status": "error",
            "error": "Audio URL missing",
            "phone": normalized_phone,
        }

    logger.info(
        "Audio message received",
        extra={
            "phone": normalized_phone,
            "sender_name": payload.senderName,
            "audio_url": audio_url,
            "mime_type": mime_type,
            "duration_seconds": duration_seconds,
            "message_id": payload.messageId,
        },
    )

    # Transcribe audio
    transcribed_text = await transcribe_audio(
        audio_url=audio_url,
        mime_type=mime_type,
        duration_seconds=duration_seconds,
    )

    if not transcribed_text:
        logger.error(
            "Audio transcription failed",
            extra={
                "phone": normalized_phone,
                "audio_url": audio_url,
            },
        )
        return {
            "status": "error",
            "error": "Transcription failed",
            "phone": normalized_phone,
        }

    logger.info(
        "Audio message transcribed successfully",
        extra={
            "phone": normalized_phone,
            "transcription_length": len(transcribed_text),
            "duration_seconds": duration_seconds,
        },
    )

    # Process transcribed text with agent (US-001)
    try:
        response_text = await process_message(
            phone=normalized_phone,
            message=transcribed_text,
            sender_name=payload.senderName,
        )

        # Send response via WhatsApp
        if response_text:
            success = await send_whatsapp_message(normalized_phone, response_text)
            if not success:
                logger.error(
                    "Failed to send WhatsApp response",
                    extra={"phone": normalized_phone},
                )
        else:
            logger.warning(
                "Empty response from agent, not sending",
                extra={"phone": normalized_phone},
            )

    except Exception as e:
        logger.error(
            "Error processing transcribed message with agent",
            extra={
                "phone": normalized_phone,
                "error": str(e),
            },
            exc_info=True,
        )
        # Send fallback message
        fallback_message = (
            "Olá! Seja bem-vindo à Seleto Industrial 👋\n"
            "Desculpe, tive um problema técnico. Pode repetir sua mensagem?"
        )
        await send_whatsapp_message(normalized_phone, fallback_message)

    return {
        "status": "processed",
        "phone": normalized_phone,
        "message_type": "audio",
        "transcribed_text": transcribed_text,
        "duration_seconds": duration_seconds,
    }


@router.post("/webhook/whatsapp")
async def whatsapp_webhook(
    request: Request,
    authorization: Optional[str] = Header(None),
    x_webhook_secret: Optional[str] = Header(None),
) -> Response:
    """
    Receive webhook from WhatsApp provider.

    Supports both text and audio messages.

    Args:
        request: FastAPI request object
        authorization: Authorization header (Bearer token)
        x_webhook_secret: X-Webhook-Secret header

    Returns:
        HTTP 200 response (processing happens asynchronously)
    """
    start_time = time.perf_counter()

    # Validate authentication
    validate_webhook_auth(authorization, x_webhook_secret)

    # Read body from state (set by middleware) or directly
    import json

    if hasattr(request.state, "body"):
        body_bytes = request.state.body
    else:
        body_bytes = await request.body()

    # Parse payload
    try:
        payload_data = json.loads(body_bytes)
        payload = WhatsAppWebhookPayload(**payload_data)
    except (json.JSONDecodeError, ValueError) as e:
        logger.error(
            "Failed to parse webhook payload",
            extra={"error": str(e)},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook payload",
        )

    # Log webhook received
    normalized_phone = normalize_phone(payload.phone) if payload.phone else None
    set_phone(normalized_phone)

    message_type = payload.messageType or ("audio" if payload.audio else "text")
    payload_size = len(body_bytes) if body_bytes else None
    log_webhook_received(
        logger,
        webhook_type="whatsapp",
        phone=normalized_phone,
        payload_size=payload_size,
    )

    # Process message asynchronously (fire and forget)
    # This ensures we respond quickly (< 2s) to the webhook provider
    if message_type == "audio" and payload.audio:
        # Process audio message
        asyncio.create_task(process_audio_message(payload))
    elif payload.message:
        # Process text message
        asyncio.create_task(process_text_message(payload))
    else:
        logger.warning(
            "Webhook received but no message or audio found",
            extra={"phone": normalized_phone, "payload": payload.model_dump()},
        )

    # Calculate response time
    duration_ms = (time.perf_counter() - start_time) * 1000

    # Log response
    log_webhook_response(
        logger,
        webhook_type="whatsapp",
        status_code=200,
        duration_ms=duration_ms,
    )

    # Return 200 immediately (async processing continues in background)
    return Response(
        status_code=status.HTTP_200_OK,
        content='{"status": "received"}',
        media_type="application/json",
    )

