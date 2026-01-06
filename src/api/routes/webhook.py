"""
Webhook endpoints for receiving messages from external services.

Supports:
- Z-API (WhatsApp) webhooks for text/audio messages
- Chatwoot webhooks for SDR intervention detection and commands
"""

import asyncio
import json
import time
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel, Field

from src.agents.sdr_agent import process_message
from src.services.agent_pause import (
    is_resume_command,
    pause_agent,
    process_sdr_command,
)
from src.services.chatwoot_sync import send_internal_message_to_chatwoot
from src.services.transcription import transcribe_audio
from src.services.whatsapp import send_whatsapp_message, whatsapp_service
from src.utils.logging import (
    get_logger,
    log_webhook_received,
    log_webhook_response,
    set_phone,
)
from src.utils.validation import normalize_phone, validate_phone

router = APIRouter()
logger = get_logger(__name__)

# #region debug instrumentation
def _debug_log(location: str, message: str, data: dict, hypothesis_id: str = None):
    """Write debug log in NDJSON format."""
    try:
        import os
        log_path = r"c:\Users\Anderson Domingos\Documents\Projetos\seleto_industrial\.cursor\debug.log"
        log_entry = {
            "sessionId": "debug-session",
            "runId": "run1",
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "data": data,
            "timestamp": int(time.time() * 1000)
        }
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception:
        pass  # Fail silently to not break production
# #endregion


class TextContent(BaseModel):
    """Z-API text content object (nested inside webhook payload)."""

    message: str = Field(..., description="The actual text message content")
    description: Optional[str] = Field(None, description="Optional description")
    title: Optional[str] = Field(None, description="Optional title")
    url: Optional[str] = Field(None, description="Optional URL reference")
    thumbnailUrl: Optional[str] = Field(None, description="Optional thumbnail URL")


class WhatsAppWebhookPayload(BaseModel):
    """
    Z-API webhook payload for on-message-received event.

    Z-API sends text messages with the content nested in a 'text' object:
    {
        "phone": "5511999999999",
        "senderName": "João",
        "text": {
            "message": "Hello"
        }
    }
    """

    phone: str = Field(..., description="Phone number of the sender")
    senderName: Optional[str] = Field(None, description="Name of the sender")
    text: Optional[TextContent] = Field(None, description="Text content object (Z-API structure)")
    audio: Optional[dict] = Field(
        None, description="Audio object (if audio message)"
    )
    messageId: Optional[str] = Field(None, description="Unique message ID")
    # Z-API uses 'type' field with value 'ReceivedCallback' for incoming messages
    type: Optional[str] = Field(None, description="Webhook event type")
    fromMe: Optional[bool] = Field(False, description="Whether message is from the connected number")
    instanceId: Optional[str] = Field(None, description="Z-API instance ID")


async def process_text_message(payload: WhatsAppWebhookPayload) -> dict:
    """
    Process incoming text message.

    Args:
        payload: Webhook payload with text message

    Returns:
        Processing result dictionary
    """
    # Extract message text from Z-API nested structure
    message_text = payload.text.message if payload.text else ""

    # #region debug instrumentation
    _debug_log("webhook.py:63", "process_text_message ENTRY", {"phone": payload.phone, "has_message": bool(message_text)}, "A")
    # #endregion

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
            "message_length": len(message_text),
            "message_id": payload.messageId,
        },
    )

    # Process message with agent (US-001)
    try:
        # #region debug instrumentation
        _debug_log("webhook.py:95", "BEFORE process_message", {"phone": normalized_phone, "message_preview": message_text[:50] if message_text else ""}, "B")
        # #endregion

        response_text = await process_message(
            phone=normalized_phone,
            message=message_text,
            sender_name=payload.senderName,
        )

        # #region debug instrumentation
        _debug_log("webhook.py:100", "AFTER process_message", {"phone": normalized_phone, "response_text": response_text[:100] if response_text else None, "response_length": len(response_text) if response_text else 0, "is_empty": not response_text}, "B")
        # #endregion

        # Send response via Z-API
        if response_text:
            # #region debug instrumentation
            is_configured = whatsapp_service.is_configured()
            _debug_log("webhook.py:103", "CHECK is_configured", {"phone": normalized_phone, "is_configured": is_configured, "instance_id": bool(whatsapp_service.instance_id), "instance_token": bool(whatsapp_service.instance_token), "client_token": bool(whatsapp_service.client_token)}, "A")
            # #endregion
            
            if is_configured:
                # #region debug instrumentation
                _debug_log("webhook.py:104", "BEFORE send_whatsapp_message", {"phone": normalized_phone, "response_length": len(response_text)}, "D")
                # #endregion
                
                success = await send_whatsapp_message(normalized_phone, response_text)
                
                # #region debug instrumentation
                _debug_log("webhook.py:105", "AFTER send_whatsapp_message", {"phone": normalized_phone, "success": success}, "D")
                # #endregion
                
                if not success:
                    logger.error(
                        "Failed to send Z-API response",
                        extra={"phone": normalized_phone},
                    )
            else:
                logger.warning(
                    "Z-API not configured, response generated but not sent",
                    extra={
                        "phone": normalized_phone,
                        "response_length": len(response_text),
                    },
                )
        else:
            # #region debug instrumentation
            _debug_log("webhook.py:118", "EMPTY response_text", {"phone": normalized_phone}, "B")
            # #endregion
            
            logger.warning(
                "Empty response from agent, not sending",
                extra={"phone": normalized_phone},
            )

    except Exception as e:
        # #region debug instrumentation
        _debug_log("webhook.py:124", "EXCEPTION in process_text_message", {"phone": normalized_phone, "error": str(e), "error_type": type(e).__name__}, "C")
        # #endregion
        
        logger.error(
            "Error processing message with agent",
            extra={
                "phone": normalized_phone,
                "error": str(e),
            },
            exc_info=True,
        )
        # Send fallback message only if Z-API is configured
        fallback_message = (
            "Olá! Seja bem-vindo à Seleto Industrial 👋\n"
            "Desculpe, tive um problema técnico. Pode repetir sua mensagem?"
        )
        if whatsapp_service.is_configured():
            try:
                await send_whatsapp_message(normalized_phone, fallback_message)
            except Exception as fallback_error:
                logger.error(
                    "Failed to send fallback message",
                    extra={
                        "phone": normalized_phone,
                        "error": str(fallback_error),
                    },
                )
        else:
            logger.warning(
                "Z-API not configured, fallback message not sent",
                extra={"phone": normalized_phone},
            )

    return {
        "status": "processed",
        "phone": normalized_phone,
        "message_type": "text",
        "message_length": len(message_text),
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

        # Send response via Z-API
        if response_text:
            if whatsapp_service.is_configured():
                success = await send_whatsapp_message(normalized_phone, response_text)
                if not success:
                    logger.error(
                        "Failed to send Z-API response",
                        extra={"phone": normalized_phone},
                    )
            else:
                logger.warning(
                    "Z-API not configured, response generated but not sent",
                    extra={
                        "phone": normalized_phone,
                        "response_length": len(response_text),
                    },
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
        # Send fallback message only if Z-API is configured
        fallback_message = (
            "Olá! Seja bem-vindo à Seleto Industrial 👋\n"
            "Desculpe, tive um problema técnico. Pode repetir sua mensagem?"
        )
        if whatsapp_service.is_configured():
            try:
                await send_whatsapp_message(normalized_phone, fallback_message)
            except Exception as fallback_error:
                logger.error(
                    "Failed to send fallback message",
                    extra={
                        "phone": normalized_phone,
                        "error": str(fallback_error),
                    },
                )
        else:
            logger.warning(
                "Z-API not configured, fallback message not sent",
                extra={"phone": normalized_phone},
            )

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
) -> Response:
    """
    Receive webhook from Z-API (WhatsApp provider).

    Supports both text and audio messages.

    Security Note: Z-API does not support custom authentication headers.
    We rely on:
    - HTTPS (required by Z-API)
    - Payload validation
    - Request logging for audit

    Args:
        request: FastAPI request object

    Returns:
        HTTP 200 response (processing happens asynchronously)
    """
    start_time = time.perf_counter()

    # Read body from state (set by middleware) or directly
    import json

    if hasattr(request.state, "body"):
        body_bytes = request.state.body
    else:
        body_bytes = await request.body()

    # Parse payload
    try:
        payload_data = json.loads(body_bytes)

        # Log raw payload for debugging Z-API structure
        logger.info(
            "Raw webhook payload received",
            extra={
                "raw_keys": list(payload_data.keys()),
                "has_text": "text" in payload_data,
                "has_message": "message" in payload_data,
                "type": payload_data.get("type"),
                "phone": payload_data.get("phone"),
            },
        )

        payload = WhatsAppWebhookPayload(**payload_data)
    except json.JSONDecodeError as e:
        logger.error(
            "Failed to parse webhook JSON",
            extra={"error": str(e), "body_preview": body_bytes[:500].decode("utf-8", errors="replace") if body_bytes else None},
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )
    except Exception as e:
        # Log the raw payload to understand Z-API structure
        logger.error(
            "Failed to validate webhook payload",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
                "raw_payload": payload_data if 'payload_data' in locals() else None,
            },
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid webhook payload: {str(e)}",
        )

    # Log webhook received
    normalized_phone = normalize_phone(payload.phone) if payload.phone else None
    set_phone(normalized_phone)

    # Determine message type from payload structure
    # Z-API uses 'audio' object for audio messages, 'text' object for text messages
    if payload.audio:
        message_type = "audio"
    elif payload.text:
        message_type = "text"
    else:
        message_type = "unknown"
    payload_size = len(body_bytes) if body_bytes else None
    log_webhook_received(
        logger,
        webhook_type="whatsapp",
        phone=normalized_phone,
        payload_size=payload_size,
    )

    # Process message asynchronously (fire and forget)
    # This ensures we respond quickly (< 2s) to the webhook provider
    # Skip messages from self (fromMe=True) to avoid echo loops
    if payload.fromMe:
        logger.info(
            "Skipping message from self (fromMe=True)",
            extra={"phone": normalized_phone, "message_id": payload.messageId},
        )
    elif message_type == "audio" and payload.audio:
        # Process audio message
        # #region debug instrumentation
        _debug_log("webhook.py:385", "CREATING audio task", {"phone": normalized_phone}, "C")
        # #endregion
        task = asyncio.create_task(process_audio_message(payload))
        # #region debug instrumentation
        task.add_done_callback(lambda t: _debug_log("webhook.py:385", "audio task DONE", {"phone": normalized_phone, "exception": str(t.exception()) if t.exception() else None}, "C"))
        # #endregion
    elif payload.text and payload.text.message:
        # Process text message (Z-API nested structure: text.message)
        # #region debug instrumentation
        _debug_log("webhook.py:388", "CREATING text task", {"phone": normalized_phone, "message_preview": payload.text.message[:50]}, "C")
        # #endregion
        task = asyncio.create_task(process_text_message(payload))
        # #region debug instrumentation
        task.add_done_callback(lambda t: _debug_log("webhook.py:388", "text task DONE", {"phone": normalized_phone, "exception": str(t.exception()) if t.exception() else None}, "C"))
        # #endregion
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


# =============================================================================
# Chatwoot Webhook Endpoint (US-008: SDR Intervention Detection)
# =============================================================================


class ChatwootSender(BaseModel):
    """Chatwoot message sender object."""

    id: Optional[int] = Field(None, description="Sender ID")
    name: Optional[str] = Field(None, description="Sender name")
    type: Optional[str] = Field(None, description="Sender type: 'user' (SDR) or 'contact' (lead)")
    email: Optional[str] = Field(None, description="Sender email")


class ChatwootConversation(BaseModel):
    """Chatwoot conversation object."""

    id: Optional[int] = Field(None, description="Conversation ID")
    inbox_id: Optional[int] = Field(None, description="Inbox ID")
    contact_inbox: Optional[dict] = Field(None, description="Contact inbox details")
    meta: Optional[dict] = Field(None, description="Conversation metadata")


class ChatwootContact(BaseModel):
    """Chatwoot contact object."""

    id: Optional[int] = Field(None, description="Contact ID")
    name: Optional[str] = Field(None, description="Contact name")
    phone_number: Optional[str] = Field(None, description="Contact phone number")
    email: Optional[str] = Field(None, description="Contact email")


class ChatwootMessage(BaseModel):
    """Chatwoot message object."""

    id: Optional[int] = Field(None, description="Message ID")
    content: Optional[str] = Field(None, description="Message content")
    message_type: Optional[str] = Field(None, description="Message type: incoming/outgoing")
    content_type: Optional[str] = Field(None, description="Content type: text/input_select/etc")
    private: Optional[bool] = Field(False, description="Whether message is private/internal")
    sender: Optional[ChatwootSender] = Field(None, description="Message sender")
    conversation_id: Optional[int] = Field(None, description="Conversation ID")
    created_at: Optional[str] = Field(None, description="Creation timestamp")


class ChatwootWebhookPayload(BaseModel):
    """
    Chatwoot webhook payload for message events.

    Chatwoot sends webhooks with the following structure:
    {
        "event": "message_created",
        "message": {...},
        "conversation": {...},
        "contact": {...},
        "account": {...}
    }
    """

    event: Optional[str] = Field(None, description="Webhook event type")
    message: Optional[ChatwootMessage] = Field(None, description="Message object")
    conversation: Optional[ChatwootConversation] = Field(None, description="Conversation object")
    contact: Optional[ChatwootContact] = Field(None, description="Contact object")
    account: Optional[dict] = Field(None, description="Account object")


def _is_sdr_message(payload: ChatwootWebhookPayload) -> bool:
    """
    Check if the message is from an SDR (human agent) vs a contact (lead).

    SDR messages have sender.type == "user"
    Contact messages have sender.type == "contact"

    Args:
        payload: Chatwoot webhook payload

    Returns:
        True if message is from SDR, False otherwise
    """
    if not payload.message or not payload.message.sender:
        return False

    sender_type = payload.message.sender.type
    return sender_type == "user"


def _extract_phone_from_payload(payload: ChatwootWebhookPayload) -> Optional[str]:
    """
    Extract the lead's phone number from the Chatwoot webhook payload.

    Args:
        payload: Chatwoot webhook payload

    Returns:
        Normalized phone number or None
    """
    phone = None

    # Try to get phone from contact
    if payload.contact and payload.contact.phone_number:
        phone = payload.contact.phone_number

    # Try to get phone from conversation metadata if not in contact
    if not phone and payload.conversation and payload.conversation.meta:
        meta = payload.conversation.meta
        # Chatwoot stores phone in meta.sender.phone_number for WhatsApp
        if "sender" in meta and isinstance(meta["sender"], dict):
            phone = meta["sender"].get("phone_number")

    if phone:
        return normalize_phone(phone)

    return None


async def process_chatwoot_message(payload: ChatwootWebhookPayload) -> dict:
    """
    Process incoming Chatwoot webhook message.

    This function:
    1. Identifies if message is from SDR (sender.type == "user")
    2. If SDR message and not a command: pause the agent
    3. If SDR command (/retomar, /continuar): process command
    4. Private messages are not shown to lead

    Args:
        payload: Chatwoot webhook payload

    Returns:
        Processing result dictionary
    """
    if not payload.message:
        return {"status": "ignored", "reason": "no_message"}

    message_content = payload.message.content or ""
    is_private = payload.message.private or False
    is_from_sdr = _is_sdr_message(payload)

    # Extract phone number for the conversation
    phone = _extract_phone_from_payload(payload)

    if not phone:
        logger.warning(
            "Chatwoot webhook: could not extract phone number",
            extra={
                "conversation_id": payload.conversation.id if payload.conversation else None,
                "message_id": payload.message.id,
            },
        )
        return {"status": "error", "reason": "no_phone"}

    # Set phone in context for logging
    set_phone(phone)

    sender_name = payload.message.sender.name if payload.message.sender else None
    sender_id = str(payload.message.sender.id) if payload.message.sender and payload.message.sender.id else None

    logger.info(
        "Chatwoot message received",
        extra={
            "phone": phone,
            "message_id": payload.message.id,
            "is_from_sdr": is_from_sdr,
            "is_private": is_private,
            "sender_name": sender_name,
            "sender_type": payload.message.sender.type if payload.message.sender else None,
            "message_preview": message_content[:50] if message_content else None,
        },
    )

    # Process only SDR messages (not contact/lead messages)
    if not is_from_sdr:
        logger.debug(
            "Message from contact (not SDR) - no action needed",
            extra={"phone": phone},
        )
        return {"status": "ignored", "reason": "contact_message"}

    # Check if it's a resume command
    if is_resume_command(message_content):
        was_command, response = process_sdr_command(phone, message_content, sender_name)
        if was_command:
            # Send response as private message in Chatwoot
            if response:
                asyncio.create_task(
                    send_internal_message_to_chatwoot(phone, response, sender_name="Sistema")
                )
            logger.info(
                "SDR command processed",
                extra={
                    "phone": phone,
                    "command": message_content.strip().lower(),
                    "response": response,
                },
            )
            return {"status": "command_processed", "response": response}

    # SDR sent a non-command message - pause the agent
    # Skip private notes (they don't require pausing)
    if is_private:
        logger.debug(
            "Private note from SDR - no pause needed",
            extra={"phone": phone, "sender_name": sender_name},
        )
        return {"status": "ignored", "reason": "private_note"}

    # Pause the agent for this conversation
    success = pause_agent(
        phone=phone,
        reason="sdr_intervention",
        sender_name=sender_name,
        sender_id=sender_id,
    )

    if success:
        # Send confirmation as private message
        confirmation = (
            f"Agente pausado para esta conversa. "
            f"O SDR {sender_name or ''} assumiu o atendimento. "
            f"Use /retomar para reativar o agente."
        )
        asyncio.create_task(
            send_internal_message_to_chatwoot(phone, confirmation, sender_name="Sistema")
        )

    return {
        "status": "agent_paused" if success else "pause_failed",
        "phone": phone,
        "sender_name": sender_name,
    }


@router.post("/webhook/chatwoot")
async def chatwoot_webhook(
    request: Request,
) -> Response:
    """
    Receive webhook from Chatwoot for SDR intervention detection.

    This webhook is triggered when:
    - SDR sends a message to a lead in Chatwoot
    - SDR sends a command (/retomar, /continuar)

    The webhook pauses the agent when SDR intervenes and processes
    resume commands.

    Args:
        request: FastAPI request object

    Returns:
        HTTP 200 response (processing happens asynchronously)
    """
    start_time = time.perf_counter()

    # Read body from state (set by middleware) or directly
    if hasattr(request.state, "body"):
        body_bytes = request.state.body
    else:
        body_bytes = await request.body()

    # Parse payload
    try:
        payload_data = json.loads(body_bytes)

        logger.debug(
            "Chatwoot webhook raw payload",
            extra={
                "event": payload_data.get("event"),
                "has_message": "message" in payload_data,
                "has_conversation": "conversation" in payload_data,
                "has_contact": "contact" in payload_data,
            },
        )

        payload = ChatwootWebhookPayload(**payload_data)

    except json.JSONDecodeError as e:
        logger.error(
            "Failed to parse Chatwoot webhook JSON",
            extra={
                "error": str(e),
                "body_preview": body_bytes[:500].decode("utf-8", errors="replace") if body_bytes else None,
            },
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )
    except Exception as e:
        logger.error(
            "Failed to validate Chatwoot webhook payload",
            extra={
                "error": str(e),
                "error_type": type(e).__name__,
            },
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid webhook payload: {str(e)}",
        )

    # Log webhook received
    phone = _extract_phone_from_payload(payload)
    payload_size = len(body_bytes) if body_bytes else None

    log_webhook_received(
        logger,
        webhook_type="chatwoot",
        phone=phone,
        payload_size=payload_size,
    )

    # Filter events - only process message_created
    event_type = payload.event
    if event_type != "message_created":
        logger.debug(
            "Chatwoot webhook event ignored",
            extra={"event": event_type, "phone": phone},
        )
        return Response(
            status_code=status.HTTP_200_OK,
            content='{"status": "ignored", "reason": "event_type"}',
            media_type="application/json",
        )

    # Process message asynchronously
    asyncio.create_task(process_chatwoot_message(payload))

    # Calculate response time
    duration_ms = (time.perf_counter() - start_time) * 1000

    # Log response
    log_webhook_response(
        logger,
        webhook_type="chatwoot",
        status_code=200,
        duration_ms=duration_ms,
    )

    # Return 200 immediately (async processing continues in background)
    return Response(
        status_code=status.HTTP_200_OK,
        content='{"status": "received"}',
        media_type="application/json",
    )

