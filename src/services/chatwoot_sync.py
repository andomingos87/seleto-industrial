"""
Chatwoot synchronization service for replicating conversation messages to Chatwoot.

This service provides functions to sync messages to Chatwoot for visual interface
and human monitoring in real-time.
"""

import asyncio
import threading
from typing import Optional

import httpx

from src.config.settings import settings
from src.utils.logging import get_logger
from src.utils.validation import normalize_phone

logger = get_logger(__name__)

# Cache for conversation IDs (phone -> chatwoot_conversation_id)
_conversation_cache: dict[str, Optional[str]] = {}


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
                # Chatwoot API returns paginated response: {data: {...}, meta: {...}}
                # Support both formats for defensive coding
                if isinstance(response_data, list):
                    conversations = response_data
                elif isinstance(response_data, dict):
                    conversations = response_data.get("data", response_data.get("payload", []))
                else:
                    conversations = []

                if conversations and len(conversations) > 0:
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
                    "source_id": contact_id,
                    "inbox_id": None,  # Will use default inbox if not specified
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
                # Chatwoot API returns paginated response: {payload: [...], meta: {...}}
                # Support both formats for defensive coding
                if isinstance(response_data, list):
                    contacts = response_data
                elif isinstance(response_data, dict):
                    contacts = response_data.get("payload", [])
                else:
                    contacts = []

                if contacts and len(contacts) > 0:
                    # Use existing contact
                    contact_id = contacts[0].get("id")
                    logger.debug(
                        "Found existing Chatwoot contact",
                        extra={"phone": phone, "contact_id": contact_id},
                    )
                    return contact_id

            # Create new contact
            contact_name = sender_name or f"Lead {phone[-4:]}"  # Use last 4 digits if no name
            create_response = await client.post(
                f"{settings.CHATWOOT_API_URL}/api/v1/accounts/{settings.CHATWOOT_ACCOUNT_ID}/contacts",
                headers={
                    "api_access_token": settings.CHATWOOT_API_TOKEN,
                    "Content-Type": "application/json",
                },
                json={
                    "name": contact_name,
                    "phone_number": phone,
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

