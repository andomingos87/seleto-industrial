"""
Lead persistence service for saving and retrieving lead data.

This service provides a unified interface for persisting lead data,
with support for Supabase (TECH-008) and in-memory fallback.
"""

from typing import Dict, Optional

from src.services.conversation_memory import conversation_memory
from src.utils.logging import get_logger
from src.utils.validation import normalize_phone

logger = get_logger(__name__)


async def persist_lead_data(phone: str, data: Dict[str, Optional[str]]) -> bool:
    """
    Persist lead data (partial or complete) to storage.

    This function:
    1. Updates in-memory conversation memory (which persists to Supabase - TECH-008)
    2. Context is also persisted to conversation_context table
    3. Logs the operation

    Args:
        phone: Phone number (will be normalized)
        data: Dictionary with lead data fields

    Returns:
        True if data was persisted successfully, False otherwise
    """
    normalized_phone = normalize_phone(phone)
    if not normalized_phone:
        logger.warning(f"Invalid phone number: {phone}")
        return False

    try:
        # Update in-memory conversation memory (this also persists to Supabase via update_lead_data)
        conversation_memory.update_lead_data(normalized_phone, data)

        logger.info(
            "Lead data persisted",
            extra={
                "phone": normalized_phone,
                "fields": list(data.keys()),
            },
        )

        return True

    except Exception as e:
        logger.error(
            "Failed to persist lead data",
            extra={
                "phone": normalized_phone,
                "error": str(e),
            },
            exc_info=True,
        )
        return False


def get_persisted_lead_data(phone: str) -> Dict[str, Optional[str]]:
    """
    Get persisted lead data for a phone number.

    Gets from conversation memory, which loads from Supabase if needed (TECH-008).

    Args:
        phone: Phone number (will be normalized)

    Returns:
        Dictionary with lead data fields
    """
    normalized_phone = normalize_phone(phone)
    if not normalized_phone:
        return {}

    # Get from conversation memory (loads from Supabase if not cached)
    lead_data = conversation_memory.get_lead_data(normalized_phone)

    return lead_data

