"""
Chatwoot synchronization service for replicating conversation messages to Chatwoot.

This service provides functions to sync messages to Chatwoot for visual interface
and human monitoring in real-time.

Features:
- Sync incoming/outgoing messages to Chatwoot conversations
- Create contacts and conversations automatically
- Send internal notes (private messages) for SDR handoff
- Retry with exponential backoff for resilience (TECH-029)
- Feedback loop prevention (BUG-003)
"""

import asyncio
import hashlib
import threading
import time
from threading import Lock
from typing import Optional

import httpx

from src.config.settings import settings
from src.services.alerts import record_integration_result
from src.services.metrics import record_integration_request
from src.utils.logging import get_logger
from src.utils.retry import (
    RetryConfig,
    check_response_for_retry,
    with_retry_async,
)
from src.utils.validation import normalize_phone

logger = get_logger(__name__)

# Default timeout for Chatwoot API calls (in seconds)
CHATWOOT_TIMEOUT = 10.0

# Retry configuration for Chatwoot (TECH-029)
CHATWOOT_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    initial_backoff=1.0,
    max_backoff=10.0,
    backoff_multiplier=2,
    jitter=True,
    retryable_status_codes=[429, 500, 502, 503, 504],
)

# Cache for conversation IDs (phone -> chatwoot_conversation_id)
_conversation_cache: dict[str, Optional[str]] = {}

# ============================================================================
# BUG-003 FIX: Feedback Loop Prevention
# ============================================================================
# Cache of recently sent bot messages to prevent webhook feedback loop.
# When the bot sends a message to Chatwoot, the webhook fires back with
# sender.type = "user" (the API user), which would incorrectly trigger
# agent pause. This cache helps identify and ignore those webhook events.
# ============================================================================

# Structure: {message_hash: timestamp_of_send}
_sent_messages_cache: dict[str, float] = {}
_sent_messages_lock = Lock()
_SENT_MESSAGES_TTL_SECONDS = 15  # Messages expire after 15 seconds


def _get_message_hash(phone: str, content: str) -> str:
    """
    Generate a unique hash to identify a message.

    Uses phone + content to create a short hash that can be used
    to match webhook messages against recently sent bot messages.

    Args:
        phone: Normalized phone number
        content: Message content

    Returns:
        16-character hexadecimal hash
    """
    normalized_content = content.strip()[:500]  # Limit content to prevent issues
    return hashlib.sha256(f"{phone}:{normalized_content}".encode()).hexdigest()[:16]


def _register_sent_message(phone: str, content: str) -> None:
    """
    Register a message as sent by the bot.

    This is called after successfully sending a message to Chatwoot
    to prevent the webhook from re-processing it as an SDR message.

    Args:
        phone: Normalized phone number
        content: Message content
    """
    msg_hash = _get_message_hash(phone, content)
    current_time = time.time()

    with _sent_messages_lock:
        _sent_messages_cache[msg_hash] = current_time

        # Cleanup expired entries (keep cache small)
        expired_hashes = [
            h for h, t in _sent_messages_cache.items()
            if current_time - t > _SENT_MESSAGES_TTL_SECONDS
        ]
        for h in expired_hashes:
            del _sent_messages_cache[h]

    logger.debug(
        "Registered sent message in feedback prevention cache",
        extra={"phone": phone, "hash": msg_hash, "cache_size": len(_sent_messages_cache)},
    )


def is_bot_message(phone: str, content: str) -> bool:
    """
    Check if a message was recently sent by the bot.

    Used to prevent webhook feedback loops where the bot's own messages
    sent to Chatwoot are incorrectly interpreted as SDR messages.

    Args:
        phone: Normalized phone number
        content: Message content

    Returns:
        True if this message was recently sent by the bot, False otherwise
    """
    if not content:
        return False

    msg_hash = _get_message_hash(phone, content)
    current_time = time.time()

    with _sent_messages_lock:
        if msg_hash in _sent_messages_cache:
            timestamp = _sent_messages_cache[msg_hash]
            if current_time - timestamp <= _SENT_MESSAGES_TTL_SECONDS:
                logger.debug(
                    "Message identified as bot's own (feedback loop prevention)",
                    extra={"phone": phone, "hash": msg_hash, "age_seconds": current_time - timestamp},
                )
                return True
            else:
                # Expired, remove it
                del _sent_messages_cache[msg_hash]

    return False


@with_retry_async(CHATWOOT_RETRY_CONFIG)
async def _make_chatwoot_request(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    **kwargs,
) -> httpx.Response:
    """
    Make an HTTP request to Chatwoot API with retry logic.

    TECH-029: Uses standardized retry decorator with exponential backoff.
    Retries on: timeout, connection errors, 429 (rate limit), 5xx errors.

    Args:
        client: httpx AsyncClient instance
        method: HTTP method (GET, POST, PUT, etc.)
        url: Full URL to request
        **kwargs: Additional arguments for httpx request

    Returns:
        httpx Response object

    Raises:
        httpx.TimeoutException: After all retries exhausted
        httpx.ConnectError: After all retries exhausted
        RetryableHTTPError: After all retries exhausted for 5xx/429
    """
    if method.upper() == "GET":
        response = await client.get(url, **kwargs)
    elif method.upper() == "POST":
        response = await client.post(url, **kwargs)
    elif method.upper() == "PUT":
        response = await client.put(url, **kwargs)
    else:
        raise ValueError(f"Unsupported HTTP method: {method}")

    # Check for retryable HTTP errors (5xx, 429)
    check_response_for_retry(response, CHATWOOT_RETRY_CONFIG)

    return response


async def create_chatwoot_conversation(phone: str, sender_name: Optional[str] = None) -> Optional[str]:
    """
    Create a Chatwoot conversation for a phone number.

    Args:
        phone: Phone number (will be normalized)
        sender_name: Optional sender name

    Returns:
        Chatwoot conversation ID if created successfully, None otherwise
    """
    normalized_phone = normalize_phone(phone)
    if not normalized_phone:
        logger.warning(f"Invalid phone number: {phone}")
        return None

    if not settings.CHATWOOT_API_URL or not settings.CHATWOOT_API_TOKEN or not settings.CHATWOOT_ACCOUNT_ID:
        logger.debug("Chatwoot not configured - conversation not created")
        return None

    # Check cache first
    if normalized_phone in _conversation_cache:
        cached_id = _conversation_cache[normalized_phone]
        if cached_id:
            logger.debug(
                "Using cached Chatwoot conversation ID",
                extra={"phone": normalized_phone, "conversation_id": cached_id},
            )
            return cached_id

    try:
        # First, try to find existing contact
        contact_id = await _get_or_create_chatwoot_contact(normalized_phone, sender_name)
        if not contact_id:
            logger.warning("Failed to get or create Chatwoot contact", extra={"phone": normalized_phone})
            return None

        # Create or get conversation
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Check if conversation already exists
            list_response = await client.get(
                f"{settings.CHATWOOT_API_URL}/api/v1/accounts/{settings.CHATWOOT_ACCOUNT_ID}/conversations",
                headers={
                    "api_access_token": settings.CHATWOOT_API_TOKEN,
                },
                params={
                    "contact_id": contact_id,
                    "status": "open",
                },
            )

            if list_response.status_code == 200:
                response_data = list_response.json()
                # Chatwoot API returns various formats:
                # - List: [{...}, {...}]
                # - Paginated: {"data": [{...}], "meta": {...}}
                # - Nested: {"data": {"payload": [...], "meta": {...}}}
                conversations = []
                if isinstance(response_data, list):
                    conversations = response_data
                elif isinstance(response_data, dict):
                    data = response_data.get("data", {})
                    if isinstance(data, list):
                        conversations = data
                    elif isinstance(data, dict):
                        # Nested format: {"data": {"payload": [...]}}
                        conversations = data.get("payload", [])
                    else:
                        # Fallback to payload at root level
                        conversations = response_data.get("payload", [])

                # Ensure conversations is a list before indexing
                if isinstance(conversations, list) and len(conversations) > 0:
                    # Use existing conversation
                    conversation_id = str(conversations[0]["id"])
                    _conversation_cache[normalized_phone] = conversation_id
                    logger.info(
                        "Found existing Chatwoot conversation",
                        extra={"phone": normalized_phone, "conversation_id": conversation_id},
                    )
                    return conversation_id

            # Create new conversation
            create_response = await client.post(
                f"{settings.CHATWOOT_API_URL}/api/v1/accounts/{settings.CHATWOOT_ACCOUNT_ID}/conversations",
                headers={
                    "api_access_token": settings.CHATWOOT_API_TOKEN,
                    "Content-Type": "application/json",
                },
                json={
                    "contact_id": contact_id,
                    "inbox_id": settings.CHATWOOT_INBOX_ID,
                },
            )

            if create_response.status_code in (200, 201):
                conversation_data = create_response.json()
                conversation_id = str(conversation_data.get("id"))
                _conversation_cache[normalized_phone] = conversation_id
                logger.info(
                    "Created Chatwoot conversation",
                    extra={"phone": normalized_phone, "conversation_id": conversation_id},
                )
                return conversation_id
            else:
                logger.error(
                    "Failed to create Chatwoot conversation",
                    extra={
                        "phone": normalized_phone,
                        "status_code": create_response.status_code,
                        "response": create_response.text[:200],
                    },
                )
                return None

    except Exception as e:
        logger.error(
            "Error creating Chatwoot conversation",
            extra={
                "phone": normalized_phone,
                "error": str(e),
            },
            exc_info=True,
        )
        return None


async def _get_or_create_chatwoot_contact(phone: str, sender_name: Optional[str] = None) -> Optional[int]:
    """
    Get or create a Chatwoot contact.

    Args:
        phone: Phone number (normalized)
        sender_name: Optional sender name

    Returns:
        Chatwoot contact ID if successful, None otherwise
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Search for existing contact by phone
            search_response = await client.get(
                f"{settings.CHATWOOT_API_URL}/api/v1/accounts/{settings.CHATWOOT_ACCOUNT_ID}/contacts/search",
                headers={
                    "api_access_token": settings.CHATWOOT_API_TOKEN,
                },
                params={
                    "q": phone,
                },
            )

            if search_response.status_code == 200:
                response_data = search_response.json()
                # Chatwoot API returns various formats:
                # - List: [{...}, {...}]
                # - Paginated: {"payload": [...], "meta": {...}}
                # - Nested: {"data": {"payload": [...], "meta": {...}}}
                contacts = []
                if isinstance(response_data, list):
                    contacts = response_data
                elif isinstance(response_data, dict):
                    # Try payload at root level first (most common for contacts)
                    payload = response_data.get("payload")
                    if isinstance(payload, list):
                        contacts = payload
                    else:
                        # Try nested format: {"data": {"payload": [...]}}
                        data = response_data.get("data", {})
                        if isinstance(data, list):
                            contacts = data
                        elif isinstance(data, dict):
                            contacts = data.get("payload", [])

                # Ensure contacts is a list before indexing
                if isinstance(contacts, list) and len(contacts) > 0:
                    # Use existing contact
                    contact_id = contacts[0].get("id")
                    logger.debug(
                        "Found existing Chatwoot contact",
                        extra={"phone": phone, "contact_id": contact_id},
                    )
                    return contact_id

            # Create new contact
            contact_name = sender_name or f"Lead {phone[-4:]}"  # Use last 4 digits if no name
            # Format phone with + prefix for E.164 format expected by Chatwoot
            phone_e164 = f"+{phone}" if not phone.startswith("+") else phone
            create_response = await client.post(
                f"{settings.CHATWOOT_API_URL}/api/v1/accounts/{settings.CHATWOOT_ACCOUNT_ID}/contacts",
                headers={
                    "api_access_token": settings.CHATWOOT_API_TOKEN,
                    "Content-Type": "application/json",
                },
                json={
                    "inbox_id": settings.CHATWOOT_INBOX_ID,
                    "name": contact_name,
                    "phone_number": phone_e164,
                },
            )

            if create_response.status_code in (200, 201):
                contact_data = create_response.json()
                contact_id = contact_data.get("id")
                logger.info(
                    "Created Chatwoot contact",
                    extra={"phone": phone, "contact_id": contact_id},
                )
                return contact_id
            else:
                logger.error(
                    "Failed to create Chatwoot contact",
                    extra={
                        "phone": phone,
                        "status_code": create_response.status_code,
                        "response": create_response.text[:200],
                    },
                )
                return None

    except Exception as e:
        logger.error(
            "Error getting or creating Chatwoot contact",
            extra={
                "phone": phone,
                "error": str(e),
            },
            exc_info=True,
        )
        return None


def sync_message_to_chatwoot(phone: str, role: str, content: str) -> bool:
    """
    Sync a message to Chatwoot (fire-and-forget, non-blocking).

    Args:
        phone: Phone number (will be normalized)
        role: Message role ("user" or "assistant")
        content: Message content

    Returns:
        True if sync was scheduled successfully, False otherwise
    """
    normalized_phone = normalize_phone(phone)
    if not normalized_phone:
        logger.warning(f"Invalid phone number: {phone}")
        return False

    if not settings.CHATWOOT_API_URL or not settings.CHATWOOT_API_TOKEN or not settings.CHATWOOT_ACCOUNT_ID:
        logger.debug("Chatwoot not configured - message not synced")
        return False

    def run_async():
        """Run async sync in a new event loop."""
        asyncio.run(_sync_message_async(normalized_phone, role, content))

    # Run sync in background thread (fire and forget)
    try:
        thread = threading.Thread(target=run_async, daemon=True)
        thread.start()
        return True
    except Exception as e:
        logger.error(
            "Failed to schedule Chatwoot sync",
            extra={
                "phone": normalized_phone,
                "error": str(e),
            },
            exc_info=True,
        )
        return False


async def _sync_message_async(phone: str, role: str, content: str) -> None:
    """
    Internal async function to sync message to Chatwoot.

    Args:
        phone: Normalized phone number
        role: Message role ("user" or "assistant")
        content: Message content
    """
    try:
        # Get or create conversation
        conversation_id = await create_chatwoot_conversation(phone)
        if not conversation_id:
            logger.warning("Failed to get Chatwoot conversation ID", extra={"phone": phone})
            return

        # Map role to Chatwoot message type
        # In Chatwoot, messages from contact are "incoming", from agent are "outgoing"
        message_type = "incoming" if role == "user" else "outgoing"

        # BUG-003 FIX: Register bot messages BEFORE sending to prevent feedback loop
        # When Chatwoot webhook fires back, we'll recognize this message and ignore it
        if role == "assistant":
            _register_sent_message(phone, content)

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{settings.CHATWOOT_API_URL}/api/v1/accounts/{settings.CHATWOOT_ACCOUNT_ID}/conversations/{conversation_id}/messages",
                headers={
                    "api_access_token": settings.CHATWOOT_API_TOKEN,
                    "Content-Type": "application/json",
                },
                json={
                    "content": content,
                    "message_type": message_type,
                    "private": False,
                },
            )

            if response.status_code in (200, 201):
                logger.debug(
                    "Message synced to Chatwoot",
                    extra={
                        "phone": phone,
                        "role": role,
                        "conversation_id": conversation_id,
                    },
                )
            else:
                logger.error(
                    "Failed to sync message to Chatwoot",
                    extra={
                        "phone": phone,
                        "role": role,
                        "status_code": response.status_code,
                        "response": response.text[:200],
                    },
                )

    except Exception as e:
        logger.error(
            "Error syncing message to Chatwoot",
            extra={
                "phone": phone,
                "role": role,
                "error": str(e),
            },
            exc_info=True,
        )


def get_chatwoot_conversation_id(phone: str) -> Optional[str]:
    """
    Get cached Chatwoot conversation ID for a phone number.

    Args:
        phone: Phone number (will be normalized)

    Returns:
        Chatwoot conversation ID if cached, None otherwise
    """
    normalized_phone = normalize_phone(phone)
    if not normalized_phone:
        return None
    return _conversation_cache.get(normalized_phone)


async def send_internal_message_to_chatwoot(
    phone: str,
    content: str,
    sender_name: Optional[str] = None,
) -> bool:
    """
    Send an internal/private message to Chatwoot conversation.

    Internal messages are only visible to agents (SDRs), not to the contact.
    Used for handoff summaries and internal notes.

    Args:
        phone: Phone number of the lead (will be normalized)
        content: Message content
        sender_name: Optional sender name for contact creation

    Returns:
        True if message was sent successfully, False otherwise
    """
    normalized_phone = normalize_phone(phone)
    if not normalized_phone:
        logger.warning(f"Invalid phone number for internal message: {phone}")
        return False

    if not settings.CHATWOOT_API_URL or not settings.CHATWOOT_API_TOKEN or not settings.CHATWOOT_ACCOUNT_ID:
        logger.debug("Chatwoot not configured - internal message not sent")
        return False

    try:
        # Get or create conversation
        conversation_id = await create_chatwoot_conversation(normalized_phone, sender_name)
        if not conversation_id:
            logger.warning(
                "Failed to get Chatwoot conversation for internal message",
                extra={"phone": normalized_phone},
            )
            return False

        async with httpx.AsyncClient(timeout=CHATWOOT_TIMEOUT) as client:
            response = await _make_chatwoot_request(
                client,
                "POST",
                f"{settings.CHATWOOT_API_URL}/api/v1/accounts/{settings.CHATWOOT_ACCOUNT_ID}/conversations/{conversation_id}/messages",
                headers={
                    "api_access_token": settings.CHATWOOT_API_TOKEN,
                    "Content-Type": "application/json",
                },
                json={
                    "content": content,
                    "message_type": "outgoing",
                    "private": True,  # Internal/private message
                },
            )

            if response.status_code in (200, 201):
                logger.info(
                    "Internal message sent to Chatwoot",
                    extra={
                        "phone": normalized_phone,
                        "conversation_id": conversation_id,
                        "content_length": len(content),
                    },
                )
                return True
            else:
                logger.error(
                    "Failed to send internal message to Chatwoot",
                    extra={
                        "phone": normalized_phone,
                        "status_code": response.status_code,
                        "response": response.text[:200],
                    },
                )
                return False

    except Exception as e:
        logger.error(
            "Error sending internal message to Chatwoot",
            extra={
                "phone": normalized_phone,
                "error": str(e),
            },
            exc_info=True,
        )
        return False


async def sync_message_to_chatwoot_async(
    phone: str,
    role: str,
    content: str,
) -> bool:
    """
    Sync a message to Chatwoot (async version with retry).

    This is the async version that can be awaited directly.
    Uses retry with exponential backoff for resilience.

    Args:
        phone: Phone number (will be normalized)
        role: Message role ("user" or "assistant")
        content: Message content

    Returns:
        True if sync was successful, False otherwise
    """
    start_time = time.perf_counter()
    normalized_phone = normalize_phone(phone)
    if not normalized_phone:
        logger.warning(f"Invalid phone number: {phone}")
        return False

    if not settings.CHATWOOT_API_URL or not settings.CHATWOOT_API_TOKEN or not settings.CHATWOOT_ACCOUNT_ID:
        logger.debug("Chatwoot not configured - message not synced")
        return False

    try:
        # Get or create conversation
        conversation_id = await create_chatwoot_conversation(normalized_phone)
        if not conversation_id:
            logger.warning("Failed to get Chatwoot conversation ID", extra={"phone": normalized_phone})
            return False

        # Map role to Chatwoot message type
        message_type = "incoming" if role == "user" else "outgoing"

        async with httpx.AsyncClient(timeout=CHATWOOT_TIMEOUT) as client:
            response = await _make_chatwoot_request(
                client,
                "POST",
                f"{settings.CHATWOOT_API_URL}/api/v1/accounts/{settings.CHATWOOT_ACCOUNT_ID}/conversations/{conversation_id}/messages",
                headers={
                    "api_access_token": settings.CHATWOOT_API_TOKEN,
                    "Content-Type": "application/json",
                },
                json={
                    "content": content,
                    "message_type": message_type,
                    "private": False,
                },
            )

            duration = time.perf_counter() - start_time

            if response.status_code in (200, 201):
                # Record success metric (TECH-023)
                record_integration_request(
                    integration="chatwoot",
                    operation="sync_message",
                    success=True,
                    duration_seconds=duration,
                )
                # Record for alert monitoring (TECH-024)
                record_integration_result("chatwoot", success=True)
                logger.debug(
                    "Message synced to Chatwoot",
                    extra={
                        "phone": normalized_phone,
                        "role": role,
                        "conversation_id": conversation_id,
                    },
                )
                return True
            else:
                # Record failure metric (TECH-023)
                record_integration_request(
                    integration="chatwoot",
                    operation="sync_message",
                    success=False,
                    duration_seconds=duration,
                )
                # Record for alert monitoring (TECH-024)
                record_integration_result("chatwoot", success=False)
                logger.error(
                    "Failed to sync message to Chatwoot",
                    extra={
                        "phone": normalized_phone,
                        "role": role,
                        "status_code": response.status_code,
                        "response": response.text[:200],
                    },
                )
                return False

    except Exception as e:
        duration = time.perf_counter() - start_time
        # Record failure metric (TECH-023)
        record_integration_request(
            integration="chatwoot",
            operation="sync_message",
            success=False,
            duration_seconds=duration,
        )
        # Record for alert monitoring (TECH-024)
        record_integration_result("chatwoot", success=False)
        logger.error(
            "Error syncing message to Chatwoot",
            extra={
                "phone": normalized_phone,
                "role": role,
                "error": str(e),
            },
            exc_info=True,
        )
        return False

