"""
Webhook endpoints for receiving messages from external services.

Supports:
- Z-API (WhatsApp) webhooks for text/audio messages
- Chatwoot webhooks for SDR intervention detection and commands
"""

import asyncio
import json
import time
from typing import Optional, Union

from fastapi import APIRouter, HTTPException, Request, Response, status
from pydantic import BaseModel, Field

from src.agents.sdr_agent import process_message
from src.services.agent_pause import (
    is_resume_command,
    pause_agent,
    process_sdr_command,
)
from src.services.chatwoot_sync import is_bot_message, send_internal_message_to_chatwoot
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
        response_text = await process_message(
            phone=normalized_phone,
            message=message_text,
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

        # Detect and ignore Chatwoot webhooks sent to wrong endpoint
        # Chatwoot payloads have 'event' field and no 'phone' field at root level
        chatwoot_events = {
            "message_created", "message_updated", "conversation_created",
            "conversation_updated", "conversation_typing_on", "conversation_typing_off",
            "conversation_status_changed", "conversation_resolved", "webwidget_triggered",
        }
        if payload_data.get("event") in chatwoot_events or (
            "account" in payload_data and "phone" not in payload_data
        ):
            logger.debug(
                "Ignoring Chatwoot webhook on WhatsApp endpoint",
                extra={
                    "event": payload_data.get("event"),
                    "hint": "Configure Chatwoot to use /webhook/chatwoot endpoint instead",
                },
            )
            return {"status": "ignored", "reason": "chatwoot_webhook_on_wrong_endpoint"}

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
        asyncio.create_task(process_audio_message(payload))
    elif payload.text and payload.text.message:
        # Process text message (Z-API nested structure: text.message)
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

    Chatwoot sends webhooks with message fields at ROOT level (not nested):
    {
        "event": "message_created",
        "content": "message text",
        "sender": {"id": 1, "name": "Agent", "type": "user"},
        "message_type": "outgoing",
        "conversation": {...},
        "account": {...}
    }
    """

    # Webhook event type
    event: Optional[str] = Field(None, description="Webhook event type")

    # Message fields (at ROOT level, not nested in "message")
    id: Optional[int] = Field(None, description="Message ID")
    content: Optional[str] = Field(None, description="Message content")
    message_type: Optional[str] = Field(None, description="Message type: incoming/outgoing")
    content_type: Optional[str] = Field(None, description="Content type: text/input_select/etc")
    private: Optional[bool] = Field(False, description="Whether message is private/internal")
    sender: Optional[ChatwootSender] = Field(None, description="Message sender")
    source_id: Optional[str] = Field(None, description="Source ID")
    # Timestamps can be string (ISO), int (Unix), or float (Unix with decimals)
    created_at: Optional[Union[str, int, float]] = Field(None, description="Creation timestamp")
    updated_at: Optional[Union[str, int, float]] = Field(None, description="Update timestamp")
    timestamp: Optional[Union[str, int, float]] = Field(None, description="Timestamp")
    inbox: Optional[dict] = Field(None, description="Inbox details")
    inbox_id: Optional[int] = Field(None, description="Inbox ID")
    content_attributes: Optional[dict] = Field(None, description="Content attributes")
    additional_attributes: Optional[dict] = Field(None, description="Additional attributes")

    # conversation_updated event fields
    can_reply: Optional[bool] = Field(None, description="Can reply to conversation")
    channel: Optional[str] = Field(None, description="Channel type")
    contact_inbox: Optional[dict] = Field(None, description="Contact inbox details")
    messages: Optional[list] = Field(None, description="Messages in conversation")
    labels: Optional[list] = Field(None, description="Labels")
    meta: Optional[dict] = Field(None, description="Metadata")
    status: Optional[str] = Field(None, description="Conversation status")
    custom_attributes: Optional[dict] = Field(None, description="Custom attributes")
    snoozed_until: Optional[Union[str, int, float]] = Field(None, description="Snoozed until")
    unread_count: Optional[int] = Field(None, description="Unread count")
    first_reply_created_at: Optional[Union[str, int, float]] = Field(None, description="First reply timestamp")
    priority: Optional[str] = Field(None, description="Priority")
    waiting_since: Optional[Union[str, int, float]] = Field(None, description="Waiting since")
    agent_last_seen_at: Optional[Union[str, int, float]] = Field(None, description="Agent last seen")
    contact_last_seen_at: Optional[Union[str, int, float]] = Field(None, description="Contact last seen")
    last_activity_at: Optional[Union[str, int, float]] = Field(None, description="Last activity")
    changed_attributes: Optional[Union[dict, list]] = Field(None, description="Changed attributes")

    # typing event fields
    user: Optional[dict] = Field(None, description="User object for typing events")
    is_private: Optional[bool] = Field(None, description="Is private typing")

    # Related objects
    conversation: Optional[ChatwootConversation] = Field(None, description="Conversation object")
    contact: Optional[ChatwootContact] = Field(None, description="Contact object")
    account: Optional[dict] = Field(None, description="Account object")

    # Legacy field for backwards compatibility (some versions may still use it)
    message: Optional[ChatwootMessage] = Field(None, description="Legacy message object")


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
    # Check sender at root level (current Chatwoot structure)
    if payload.sender:
        sender_type = payload.sender.type
        return sender_type == "user"

    # Fallback: check legacy nested message structure
    if payload.message and payload.message.sender:
        sender_type = payload.message.sender.type
        return sender_type == "user"

    return False


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
    # Get message content from root level (current Chatwoot structure)
    # or fall back to legacy nested message structure
    message_content = payload.content or ""
    if not message_content and payload.message:
        message_content = payload.message.content or ""

    # Check if there's any message content
    if not message_content:
        return {"status": "ignored", "reason": "no_message_content"}

    # Get private flag from root level or legacy structure
    is_private = payload.private or False
    if payload.message:
        is_private = is_private or (payload.message.private or False)

    is_from_sdr = _is_sdr_message(payload)

    # Extract phone number for the conversation
    phone = _extract_phone_from_payload(payload)

    if not phone:
        logger.warning(
            "Chatwoot webhook: could not extract phone number",
            extra={
                "conversation_id": payload.conversation.id if payload.conversation else None,
                "message_id": payload.id,
            },
        )
        return {"status": "error", "reason": "no_phone"}

    # Set phone in context for logging
    set_phone(phone)

    # BUG-003 FIX: Check if this is a message we sent ourselves (feedback loop prevention)
    # When our bot sends a message to Chatwoot via API, Chatwoot fires a webhook back
    # with sender.type = "user" (the API user), which would incorrectly trigger agent pause
    if is_bot_message(phone, message_content):
        logger.debug(
            "Ignoring bot's own message (feedback loop prevention)",
            extra={
                "phone": phone,
                "message_preview": message_content[:50] if message_content else None,
            },
        )
        return {"status": "ignored", "reason": "bot_message_feedback_loop"}

    # Get sender name and ID from root level or legacy structure
    sender_name = None
    sender_id = None
    sender_type = None
    if payload.sender:
        sender_name = payload.sender.name
        sender_id = str(payload.sender.id) if payload.sender.id else None
        sender_type = payload.sender.type
    elif payload.message and payload.message.sender:
        sender_name = payload.message.sender.name
        sender_id = str(payload.message.sender.id) if payload.message.sender.id else None
        sender_type = payload.message.sender.type

    # Get message ID from root level or legacy structure
    message_id = payload.id
    if not message_id and payload.message:
        message_id = payload.message.id

    logger.info(
        "Chatwoot message received",
        extra={
            "phone": phone,
            "message_id": message_id,
            "is_from_sdr": is_from_sdr,
            "is_private": is_private,
            "sender_name": sender_name,
            "sender_type": sender_type,
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

    # BUG-002 FIX: Send SDR's message to WhatsApp via Z-API
    # This ensures the lead receives the SDR's message on WhatsApp
    if message_content and message_content.strip():
        try:
            whatsapp_success = await send_whatsapp_message(phone, message_content)
            if whatsapp_success:
                logger.info(
                    "SDR message sent to WhatsApp",
                    extra={
                        "phone": phone,
                        "sender_name": sender_name,
                        "message_length": len(message_content),
                    },
                )
            else:
                logger.error(
                    "Failed to send SDR message to WhatsApp",
                    extra={"phone": phone, "message_content_preview": message_content[:50]},
                )
        except Exception as e:
            logger.error(
                "Error sending SDR message to WhatsApp",
                extra={"phone": phone, "error": str(e)},
                exc_info=True,
            )

    return {
        "status": "agent_paused" if success else "pause_failed",
        "phone": phone,
        "sender_name": sender_name,
        "message_sent_to_whatsapp": bool(message_content and message_content.strip()),
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
        logger.info(
            "Chatwoot webhook event ignored (not message_created)",
            extra={"event": event_type, "phone": phone},
        )
        return Response(
            status_code=status.HTTP_200_OK,
            content='{"status": "ignored", "reason": "event_type"}',
            media_type="application/json",
        )

    # Log that we're processing this message (check root level first, then legacy)
    content_preview = None
    if payload.content:
        content_preview = payload.content[:50]
    elif payload.message and payload.message.content:
        content_preview = payload.message.content[:50]

    sender_type = None
    if payload.sender:
        sender_type = payload.sender.type
    elif payload.message and payload.message.sender:
        sender_type = payload.message.sender.type

    logger.info(
        "Chatwoot message_created event - processing",
        extra={
            "phone": phone,
            "has_content": bool(payload.content or (payload.message and payload.message.content)),
            "message_content_preview": content_preview,
            "sender_type": sender_type,
            "is_sdr": sender_type == "user",
        },
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

