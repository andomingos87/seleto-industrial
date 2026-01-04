"""
Conversation persistence service for storing and retrieving conversation history from Supabase.

This service provides functions to save and retrieve conversation messages and context
from Supabase, with fallback to in-memory storage if Supabase is not configured.
"""

from datetime import datetime
from typing import Dict, List, Optional

from supabase import create_client, Client

from src.config.settings import settings
from src.utils.logging import get_logger
from src.utils.validation import normalize_phone

logger = get_logger(__name__)

# Global Supabase client instance
_supabase_client: Optional[Client] = None


def get_supabase_client() -> Optional[Client]:
    """
    Get or create Supabase client instance.

    Returns:
        Supabase client if configured, None otherwise
    """
    global _supabase_client

    if _supabase_client is not None:
        return _supabase_client

    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        logger.debug("Supabase not configured - persistence will use in-memory fallback")
        return None

    try:
        _supabase_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_ROLE_KEY,
        )
        logger.info("Supabase client initialized successfully")
        return _supabase_client
    except Exception as e:
        logger.error(
            "Failed to initialize Supabase client",
            extra={"error": str(e)},
            exc_info=True,
        )
        return None


def save_message_to_supabase(phone: str, role: str, content: str) -> bool:
    """
    Save a message to Supabase.

    Args:
        phone: Phone number (will be normalized)
        role: Message role ("user" or "assistant")
        content: Message content

    Returns:
        True if message was saved successfully, False otherwise
    """
    normalized_phone = normalize_phone(phone)
    if not normalized_phone:
        logger.warning(f"Invalid phone number: {phone}")
        return False

    if role not in ("user", "assistant"):
        logger.warning(f"Invalid role: {role}")
        return False

    client = get_supabase_client()
    if not client:
        logger.debug("Supabase not available - message not persisted")
        return False

    try:
        response = (
            client.table("conversation_messages")
            .insert(
                {
                    "lead_phone": normalized_phone,
                    "role": role,
                    "content": content,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
            .execute()
        )

        if response.data:
            logger.debug(
                "Message saved to Supabase",
                extra={
                    "phone": normalized_phone,
                    "role": role,
                    "message_id": response.data[0].get("id") if response.data else None,
                },
            )
            return True
        else:
            logger.warning("No data returned from Supabase insert")
            return False

    except Exception as e:
        logger.error(
            "Failed to save message to Supabase",
            extra={
                "phone": normalized_phone,
                "role": role,
                "error": str(e),
            },
            exc_info=True,
        )
        return False


def get_messages_from_supabase(
    phone: str, max_messages: Optional[int] = None
) -> List[Dict[str, any]]:
    """
    Get conversation messages from Supabase.

    Args:
        phone: Phone number (will be normalized)
        max_messages: Maximum number of messages to return (None = all)

    Returns:
        List of message dictionaries with keys: role, content, timestamp
    """
    normalized_phone = normalize_phone(phone)
    if not normalized_phone:
        logger.warning(f"Invalid phone number: {phone}")
        return []

    client = get_supabase_client()
    if not client:
        logger.debug("Supabase not available - returning empty list")
        return []

    try:
        query = (
            client.table("conversation_messages")
            .select("role, content, timestamp")
            .eq("lead_phone", normalized_phone)
            .order("timestamp", desc=False)  # Oldest first
        )

        if max_messages:
            query = query.limit(max_messages)

        response = query.execute()

        messages = []
        if response.data:
            for msg in response.data:
                messages.append(
                    {
                        "role": msg.get("role"),
                        "content": msg.get("content"),
                        "timestamp": msg.get("timestamp"),
                    }
                )

        logger.debug(
            "Messages retrieved from Supabase",
            extra={
                "phone": normalized_phone,
                "message_count": len(messages),
            },
        )
        return messages

    except Exception as e:
        logger.error(
            "Failed to retrieve messages from Supabase",
            extra={
                "phone": normalized_phone,
                "error": str(e),
            },
            exc_info=True,
        )
        return []


def save_context_to_supabase(phone: str, context: Dict[str, any]) -> bool:
    """
    Save conversation context to Supabase.

    Args:
        phone: Phone number (will be normalized)
        context: Dictionary with context data

    Returns:
        True if context was saved successfully, False otherwise
    """
    normalized_phone = normalize_phone(phone)
    if not normalized_phone:
        logger.warning(f"Invalid phone number: {phone}")
        return False

    client = get_supabase_client()
    if not client:
        logger.debug("Supabase not available - context not persisted")
        return False

    try:
        # Use upsert to update or insert
        response = (
            client.table("conversation_context")
            .upsert(
                {
                    "lead_phone": normalized_phone,
                    "context_data": context,
                    "updated_at": datetime.utcnow().isoformat(),
                },
                on_conflict="lead_phone",
            )
            .execute()
        )

        if response.data:
            logger.debug(
                "Context saved to Supabase",
                extra={
                    "phone": normalized_phone,
                    "context_keys": list(context.keys()),
                },
            )
            return True
        else:
            logger.warning("No data returned from Supabase upsert")
            return False

    except Exception as e:
        logger.error(
            "Failed to save context to Supabase",
            extra={
                "phone": normalized_phone,
                "error": str(e),
            },
            exc_info=True,
        )
        return False


def get_context_from_supabase(phone: str) -> Dict[str, any]:
    """
    Get conversation context from Supabase.

    Args:
        phone: Phone number (will be normalized)

    Returns:
        Dictionary with context data (empty dict if not found)
    """
    normalized_phone = normalize_phone(phone)
    if not normalized_phone:
        logger.warning(f"Invalid phone number: {phone}")
        return {}

    client = get_supabase_client()
    if not client:
        logger.debug("Supabase not available - returning empty context")
        return {}

    try:
        response = (
            client.table("conversation_context")
            .select("context_data")
            .eq("lead_phone", normalized_phone)
            .execute()
        )

        if response.data and len(response.data) > 0:
            context_data = response.data[0].get("context_data", {})
            logger.debug(
                "Context retrieved from Supabase",
                extra={
                    "phone": normalized_phone,
                    "context_keys": list(context_data.keys()) if isinstance(context_data, dict) else [],
                },
            )
            return context_data if isinstance(context_data, dict) else {}
        else:
            logger.debug("No context found in Supabase", extra={"phone": normalized_phone})
            return {}

    except Exception as e:
        logger.error(
            "Failed to retrieve context from Supabase",
            extra={
                "phone": normalized_phone,
                "error": str(e),
            },
            exc_info=True,
        )
        return {}

