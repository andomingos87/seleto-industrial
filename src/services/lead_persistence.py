"""
Lead persistence service for saving and retrieving lead data.

This service provides a unified interface for persisting lead data,
with support for Supabase (TECH-008) and in-memory fallback.

CRUD operations for leads table (TECH-012):
- upsert_lead: Create or update lead with idempotency by phone
- get_lead_by_phone: Retrieve lead by normalized phone number
"""

from datetime import datetime
from typing import Any

from src.services.audit_trail import (
    EntityType,
    log_entity_create_sync,
    log_entity_update_sync,
)
from src.services.conversation_memory import conversation_memory
from src.services.conversation_persistence import get_supabase_client
from src.utils.logging import get_logger
from src.utils.validation import normalize_phone, validate_phone

logger = get_logger(__name__)


async def persist_lead_data(phone: str, data: dict[str, str | None]) -> bool:
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


def get_persisted_lead_data(phone: str) -> dict[str, str | None]:
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


def upsert_lead(phone: str, data: dict[str, Any | None]) -> dict[str, Any] | None:
    """
    Create or update a lead in Supabase with idempotency by phone.

    This function:
    1. Normalizes the phone number before operations
    2. Filters out None/null fields for partial updates
    3. Uses upsert with on_conflict='phone' for idempotency
    4. Ensures existing fields are not overwritten with null
    5. Returns the created/updated lead or None on error

    Args:
        phone: Phone number (will be normalized to E.164 format)
        data: Dictionary with lead data fields (name, email, city, uf, etc.)
              Fields with None/null values are filtered out for partial updates

    Returns:
        Dictionary with lead data (including id, created_at, updated_at) or None on error

    Examples:
        >>> # Create new lead
        >>> lead = upsert_lead("5511999999999", {"name": "João Silva", "city": "São Paulo"})
        >>> # Update existing lead (partial update)
        >>> lead = upsert_lead("5511999999999", {"email": "joao@example.com"})
        >>> # Multiple upserts with same phone result in single lead (idempotency)
        >>> lead1 = upsert_lead("5511999999999", {"name": "João"})
        >>> lead2 = upsert_lead("5511999999999", {"city": "SP"})
        >>> # lead1 and lead2 refer to the same lead record
    """
    normalized_phone = normalize_phone(phone)
    if not normalized_phone:
        logger.warning(
            "Invalid phone number for upsert_lead",
            extra={"phone": phone, "operation": "upsert_lead"},
        )
        return None

    # Validate phone number format (at least 10 digits)
    if not validate_phone(normalized_phone):
        logger.warning(
            "Invalid phone number format for upsert_lead",
            extra={"phone": normalized_phone, "operation": "upsert_lead"},
        )
        return None

    try:
        client = get_supabase_client()
    except Exception as e:
        logger.error(
            "Failed to get Supabase client",
            extra={"error": str(e), "operation": "upsert_lead"},
        )
        return None

    if not client:
        logger.debug(
            "Supabase not available - lead not persisted",
            extra={"phone": normalized_phone, "operation": "upsert_lead"},
        )
        return None

    try:
        # Check if lead already exists (for audit trail - CREATE vs UPDATE)
        existing_lead = None
        try:
            existing_response = (
                client.table("leads")
                .select("*")
                .eq("phone", normalized_phone)
                .execute()
            )
            if existing_response.data and len(existing_response.data) > 0:
                existing_lead = existing_response.data[0]
        except Exception:
            # If we can't check, continue with upsert (audit will be CREATE)
            pass

        # Filter out None/null values for partial updates
        # This ensures existing fields are not overwritten with null
        filtered_data = {k: v for k, v in data.items() if v is not None}

        # Prepare upsert payload with normalized phone
        upsert_payload = {
            "phone": normalized_phone,
            **filtered_data,
            "updated_at": datetime.utcnow().isoformat(),
        }

        # Use upsert with on_conflict='phone' for idempotency
        response = (
            client.table("leads")
            .upsert(upsert_payload, on_conflict="phone")
            .execute()
        )

        if response.data and len(response.data) > 0:
            lead = response.data[0]
            lead_id = lead.get("id")

            # Audit trail (TECH-028): Log CREATE or UPDATE
            if existing_lead:
                log_entity_update_sync(
                    entity_type=EntityType.LEAD,
                    entity_id=str(lead_id),
                    old_data=existing_lead,
                    new_data=lead,
                )
            else:
                log_entity_create_sync(
                    entity_type=EntityType.LEAD,
                    entity_id=str(lead_id),
                    data=lead,
                )

            logger.info(
                "Lead upserted successfully",
                extra={
                    "phone": normalized_phone,
                    "lead_id": lead_id,
                    "fields_updated": list(filtered_data.keys()),
                    "operation": "upsert_lead",
                    "audit_action": "UPDATE" if existing_lead else "CREATE",
                },
            )
            return lead
        else:
            logger.warning(
                "No data returned from Supabase upsert",
                extra={"phone": normalized_phone, "operation": "upsert_lead"},
            )
            return None

    except Exception as e:
        logger.error(
            "Failed to upsert lead",
            extra={
                "phone": normalized_phone,
                "error": str(e),
                "operation": "upsert_lead",
            },
            exc_info=True,
        )
        return None


def get_lead_by_phone(phone: str) -> dict[str, Any] | None:
    """
    Get a lead by phone number from Supabase.

    This function:
    1. Normalizes the phone number before search
    2. Queries Supabase for lead with matching phone
    3. Returns lead as dict or None if not found

    Args:
        phone: Phone number (will be normalized to E.164 format)

    Returns:
        Dictionary with lead data (including id, created_at, updated_at) or None if not found

    Examples:
        >>> lead = get_lead_by_phone("5511999999999")
        >>> if lead:
        ...     print(lead["name"])
        >>> # Returns None if lead doesn't exist
        >>> lead = get_lead_by_phone("5511888888888")
        >>> assert lead is None
    """
    normalized_phone = normalize_phone(phone)
    if not normalized_phone:
        logger.warning(
            "Invalid phone number for get_lead_by_phone",
            extra={"phone": phone, "operation": "get_lead_by_phone"},
        )
        return None

    # Validate phone number format (at least 10 digits)
    if not validate_phone(normalized_phone):
        logger.warning(
            "Invalid phone number format for get_lead_by_phone",
            extra={"phone": normalized_phone, "operation": "get_lead_by_phone"},
        )
        return None

    try:
        client = get_supabase_client()
    except Exception as e:
        logger.error(
            "Failed to get Supabase client",
            extra={"error": str(e), "operation": "get_lead_by_phone"},
        )
        return None

    if not client:
        logger.debug(
            "Supabase not available - returning None",
            extra={"phone": normalized_phone, "operation": "get_lead_by_phone"},
        )
        return None

    try:
        response = (
            client.table("leads")
            .select("*")
            .eq("phone", normalized_phone)
            .execute()
        )

        if response.data and len(response.data) > 0:
            lead = response.data[0]
            logger.debug(
                "Lead retrieved successfully",
                extra={
                    "phone": normalized_phone,
                    "lead_id": lead.get("id"),
                    "operation": "get_lead_by_phone",
                },
            )
            return lead
        else:
            logger.debug(
                "Lead not found",
                extra={"phone": normalized_phone, "operation": "get_lead_by_phone"},
            )
            return None

    except Exception as e:
        logger.error(
            "Failed to get lead by phone",
            extra={
                "phone": normalized_phone,
                "error": str(e),
                "operation": "get_lead_by_phone",
            },
            exc_info=True,
        )
        return None


def update_lead_sync_status(phone: str, status: str) -> bool:
    """
    Update the CRM sync status of a lead (TECH-030).

    Args:
        phone: Phone number (will be normalized)
        status: Sync status ('synced', 'pending', 'failed')

    Returns:
        True if updated successfully, False otherwise
    """
    valid_statuses = ("synced", "pending", "failed")
    if status not in valid_statuses:
        logger.warning(
            f"Invalid sync status: {status}. Must be one of {valid_statuses}",
            extra={"phone": phone, "status": status},
        )
        return False

    normalized_phone = normalize_phone(phone)
    if not normalized_phone:
        logger.warning(
            "Invalid phone number for update_lead_sync_status",
            extra={"phone": phone, "operation": "update_lead_sync_status"},
        )
        return False

    try:
        client = get_supabase_client()
    except Exception as e:
        logger.error(
            "Failed to get Supabase client",
            extra={"error": str(e), "operation": "update_lead_sync_status"},
        )
        return False

    if not client:
        logger.debug(
            "Supabase not available - skipping sync status update",
            extra={"phone": normalized_phone, "operation": "update_lead_sync_status"},
        )
        return False

    try:
        response = (
            client.table("leads")
            .update({"crm_sync_status": status})
            .eq("phone", normalized_phone)
            .execute()
        )

        if response.data and len(response.data) > 0:
            logger.info(
                "Lead sync status updated",
                extra={
                    "phone": normalized_phone,
                    "status": status,
                    "operation": "update_lead_sync_status",
                },
            )
            return True
        else:
            logger.warning(
                "Lead not found for sync status update",
                extra={"phone": normalized_phone, "operation": "update_lead_sync_status"},
            )
            return False

    except Exception as e:
        logger.error(
            "Failed to update lead sync status",
            extra={
                "phone": normalized_phone,
                "status": status,
                "error": str(e),
                "operation": "update_lead_sync_status",
            },
            exc_info=True,
        )
        return False

