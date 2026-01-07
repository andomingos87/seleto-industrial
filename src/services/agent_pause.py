"""
Agent Pause Service for SDR Agent.

This module manages the pause/resume state of the agent for individual conversations.
When an SDR intervenes (sends a message via Chatwoot), the agent pauses for that
conversation. The agent can be resumed via command or automatically outside business hours.

State is persisted in Supabase `conversation_context.context_data` to survive restarts.
"""

from datetime import datetime
from typing import Dict, Optional, Tuple

from src.services.business_hours import is_business_hours, should_auto_resume
from src.services.conversation_persistence import (
    get_context_from_supabase,
    get_supabase_client,
    save_context_to_supabase,
)
from src.utils.logging import get_logger
from src.utils.validation import normalize_phone

logger = get_logger(__name__)

# In-memory cache for pause states (performance optimization)
# Key: phone, Value: dict with pause info
_pause_cache: Dict[str, dict] = {}

# Resume command patterns
# Note: Chatwoot does NOT send webhooks for messages starting with "/"
# So we accept both with and without "/" prefix
RESUME_COMMANDS = [
    "/retomar", "/continuar",  # With slash (for WhatsApp direct commands)
    "retomar", "continuar",    # Without slash (for Chatwoot - can't start with /)
    "!retomar", "!continuar",  # Alternative prefix for Chatwoot
]


def _get_pause_key(phone: str) -> str:
    """Get the key for pause state in context_data."""
    return "agent_pause_state"


def is_agent_paused(phone: str) -> bool:
    """
    Check if the agent is paused for a given conversation.

    Args:
        phone: Phone number (will be normalized)

    Returns:
        True if agent is paused, False otherwise
    """
    normalized_phone = normalize_phone(phone)
    if not normalized_phone:
        logger.warning(f"Invalid phone number: {phone}")
        return False

    # Check cache first
    if normalized_phone in _pause_cache:
        is_paused = _pause_cache[normalized_phone].get("paused", False)
        logger.debug(
            "Pause state from cache",
            extra={"phone": normalized_phone, "is_paused": is_paused},
        )
        return is_paused

    # Load from Supabase if not in cache
    context = get_context_from_supabase(normalized_phone)
    pause_state = context.get(_get_pause_key(normalized_phone), {})

    # Update cache
    _pause_cache[normalized_phone] = pause_state

    is_paused = pause_state.get("paused", False)
    logger.debug(
        "Pause state from Supabase",
        extra={"phone": normalized_phone, "is_paused": is_paused},
    )

    return is_paused


def get_pause_info(phone: str) -> Optional[dict]:
    """
    Get detailed pause information for a conversation.

    Args:
        phone: Phone number (will be normalized)

    Returns:
        Dictionary with pause info or None if not paused
    """
    normalized_phone = normalize_phone(phone)
    if not normalized_phone:
        return None

    # Check cache first
    if normalized_phone in _pause_cache:
        return _pause_cache[normalized_phone] if _pause_cache[normalized_phone].get("paused") else None

    # Load from Supabase if not in cache
    context = get_context_from_supabase(normalized_phone)
    pause_state = context.get(_get_pause_key(normalized_phone), {})

    # Update cache
    _pause_cache[normalized_phone] = pause_state

    return pause_state if pause_state.get("paused") else None


def pause_agent(
    phone: str,
    reason: str = "sdr_intervention",
    sender_name: Optional[str] = None,
    sender_id: Optional[str] = None,
) -> bool:
    """
    Pause the agent for a specific conversation.

    Args:
        phone: Phone number (will be normalized)
        reason: Reason for pausing (default: sdr_intervention)
        sender_name: Name of the SDR who triggered the pause
        sender_id: ID of the SDR who triggered the pause

    Returns:
        True if agent was paused successfully, False otherwise
    """
    normalized_phone = normalize_phone(phone)
    if not normalized_phone:
        logger.warning(f"Invalid phone number: {phone}")
        return False

    # Get current business hours status for logging
    in_business_hours = is_business_hours()

    pause_state = {
        "paused": True,
        "paused_at": datetime.utcnow().isoformat(),
        "reason": reason,
        "sender_name": sender_name,
        "sender_id": sender_id,
        "business_hours_at_pause": in_business_hours,
    }

    # Update cache
    _pause_cache[normalized_phone] = pause_state

    # Persist to Supabase
    context = get_context_from_supabase(normalized_phone)
    context[_get_pause_key(normalized_phone)] = pause_state

    success = save_context_to_supabase(normalized_phone, context)

    if success:
        logger.info(
            "Agent paused for conversation",
            extra={
                "phone": normalized_phone,
                "reason": reason,
                "sender_name": sender_name,
                "business_hours": in_business_hours,
            },
        )
    else:
        logger.error(
            "Failed to persist pause state",
            extra={"phone": normalized_phone},
        )

    return success


def resume_agent(
    phone: str,
    reason: str = "sdr_command",
    resumed_by: Optional[str] = None,
) -> bool:
    """
    Resume the agent for a specific conversation.

    Args:
        phone: Phone number (will be normalized)
        reason: Reason for resuming (sdr_command, auto_resume_outside_hours)
        resumed_by: Who/what triggered the resume

    Returns:
        True if agent was resumed successfully, False otherwise
    """
    normalized_phone = normalize_phone(phone)
    if not normalized_phone:
        logger.warning(f"Invalid phone number: {phone}")
        return False

    # Get current business hours status for logging
    in_business_hours = is_business_hours()

    pause_state = {
        "paused": False,
        "resumed_at": datetime.utcnow().isoformat(),
        "resume_reason": reason,
        "resumed_by": resumed_by,
        "business_hours_at_resume": in_business_hours,
    }

    # Update cache
    _pause_cache[normalized_phone] = pause_state

    # Persist to Supabase
    context = get_context_from_supabase(normalized_phone)
    context[_get_pause_key(normalized_phone)] = pause_state

    success = save_context_to_supabase(normalized_phone, context)

    if success:
        logger.info(
            "Agent resumed for conversation",
            extra={
                "phone": normalized_phone,
                "reason": reason,
                "resumed_by": resumed_by,
                "business_hours": in_business_hours,
            },
        )
    else:
        logger.error(
            "Failed to persist resume state",
            extra={"phone": normalized_phone},
        )

    return success


def check_auto_resume(phone: str) -> Tuple[bool, Optional[str]]:
    """
    Check if the agent should auto-resume for a conversation.

    According to PRD:
    - During business hours: SDR must use command (no auto-resume)
    - Outside business hours: Agent auto-resumes when lead sends new message

    Args:
        phone: Phone number (will be normalized)

    Returns:
        Tuple of (should_resume, reason)
        - (True, "outside_business_hours") if should auto-resume
        - (False, "within_business_hours") if should stay paused
        - (False, None) if not paused
    """
    normalized_phone = normalize_phone(phone)
    if not normalized_phone:
        return (False, None)

    # Check if currently paused
    if not is_agent_paused(normalized_phone):
        logger.debug(
            "Agent not paused - no auto-resume check needed",
            extra={"phone": normalized_phone},
        )
        return (False, None)

    # Check business hours
    if should_auto_resume():
        logger.info(
            "Auto-resume triggered - outside business hours",
            extra={"phone": normalized_phone},
        )
        return (True, "outside_business_hours")
    else:
        logger.debug(
            "Auto-resume blocked - within business hours",
            extra={"phone": normalized_phone},
        )
        return (False, "within_business_hours")


def try_auto_resume(phone: str) -> bool:
    """
    Try to auto-resume the agent if conditions are met.

    This is a convenience function that combines check_auto_resume and resume_agent.

    Args:
        phone: Phone number (will be normalized)

    Returns:
        True if agent was auto-resumed, False otherwise
    """
    should_resume, reason = check_auto_resume(phone)

    if should_resume:
        return resume_agent(
            phone,
            reason="auto_resume_outside_hours",
            resumed_by="system",
        )

    return False


def is_resume_command(message: str) -> bool:
    """
    Check if a message is a resume command (/retomar or /continuar).

    Args:
        message: Message content

    Returns:
        True if message is a resume command, False otherwise
    """
    if not message:
        return False

    # Normalize message for comparison
    normalized_message = message.strip().lower()

    # Check for exact match or message starting with command
    for command in RESUME_COMMANDS:
        if normalized_message == command or normalized_message.startswith(command + " "):
            return True

    return False


def process_sdr_command(phone: str, message: str, sender_name: Optional[str] = None) -> Tuple[bool, str]:
    """
    Process a command from the SDR.

    Currently supports:
    - /retomar: Resume the agent
    - /continuar: Resume the agent (alias)

    Args:
        phone: Phone number (will be normalized)
        message: Message content
        sender_name: Name of the SDR

    Returns:
        Tuple of (was_command, response_message)
        - (True, response) if a command was processed
        - (False, "") if not a command
    """
    if not is_resume_command(message):
        return (False, "")

    normalized_phone = normalize_phone(phone)
    if not normalized_phone:
        return (False, "")

    # Check if agent is actually paused
    if not is_agent_paused(normalized_phone):
        logger.info(
            "Resume command received but agent not paused",
            extra={"phone": normalized_phone, "sender_name": sender_name},
        )
        return (True, "O agente ja esta ativo para esta conversa.")

    # Resume the agent
    success = resume_agent(
        normalized_phone,
        reason="sdr_command",
        resumed_by=sender_name or "SDR",
    )

    if success:
        return (True, "Agente retomado com sucesso. O bot voltara a responder automaticamente.")
    else:
        return (True, "Erro ao retomar o agente. Por favor, tente novamente.")


def clear_cache(phone: Optional[str] = None) -> None:
    """
    Clear the pause state cache.

    Args:
        phone: If provided, clear only for this phone. Otherwise, clear all.
    """
    global _pause_cache

    if phone:
        normalized_phone = normalize_phone(phone)
        if normalized_phone and normalized_phone in _pause_cache:
            del _pause_cache[normalized_phone]
            logger.debug("Pause cache cleared for phone", extra={"phone": normalized_phone})
    else:
        _pause_cache.clear()
        logger.debug("Pause cache cleared completely")


def load_pause_states_from_supabase() -> int:
    """
    Load all pause states from Supabase into cache.

    This should be called at application startup to recover state.

    Returns:
        Number of paused conversations loaded
    """
    global _pause_cache

    client = get_supabase_client()
    if not client:
        logger.warning("Supabase not available - cannot load pause states")
        return 0

    try:
        # Query all conversation contexts
        response = (
            client.table("conversation_context")
            .select("lead_phone, context_data")
            .execute()
        )

        loaded_count = 0
        if response.data:
            for row in response.data:
                phone = row.get("lead_phone")
                context_data = row.get("context_data", {})

                if not phone or not isinstance(context_data, dict):
                    continue

                pause_state = context_data.get(_get_pause_key(phone), {})
                if pause_state.get("paused", False):
                    _pause_cache[phone] = pause_state
                    loaded_count += 1

        logger.info(
            "Pause states loaded from Supabase",
            extra={"count": loaded_count},
        )
        return loaded_count

    except Exception as e:
        logger.error(
            "Failed to load pause states from Supabase",
            extra={"error": str(e)},
            exc_info=True,
        )
        return 0
