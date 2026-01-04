"""
Lead persistence service for saving and retrieving lead data.

This service provides a unified interface for persisting lead data,
with support for Supabase (when available) and in-memory fallback.
"""

from typing import Dict, Optional

from src.config.settings import settings
from src.services.conversation_memory import conversation_memory
from src.utils.logging import get_logger
from src.utils.validation import normalize_phone

logger = get_logger(__name__)


async def persist_lead_data(phone: str, data: Dict[str, Optional[str]]) -> bool:
    """
    Persist lead data (partial or complete) to storage.

    This function:
    1. Updates in-memory conversation memory
    2. Attempts to persist to Supabase if configured (future: TECH-012)
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
        # Update in-memory conversation memory
        conversation_memory.update_lead_data(normalized_phone, data)

        # TODO: When TECH-012 is implemented, add Supabase persistence here
        # For now, we only use in-memory storage
        # This ensures data is available even if conversation is not completed
        if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY:
            # Future: Implement Supabase upsert
            # await upsert_lead_to_supabase(normalized_phone, data)
            logger.debug(
                "Supabase configured but persistence not yet implemented (TECH-012)",
                extra={"phone": normalized_phone},
            )

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

    Args:
        phone: Phone number (will be normalized)

    Returns:
        Dictionary with lead data fields
    """
    normalized_phone = normalize_phone(phone)
    if not normalized_phone:
        return {}

    # Get from conversation memory (in-memory)
    lead_data = conversation_memory.get_lead_data(normalized_phone)

    # TODO: When TECH-012 is implemented, also check Supabase
    # if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY:
    #     supabase_data = get_lead_from_supabase(normalized_phone)
    #     if supabase_data:
    #         # Merge with in-memory data (in-memory takes precedence for current session)
    #         lead_data = {**supabase_data, **lead_data}

    return lead_data

