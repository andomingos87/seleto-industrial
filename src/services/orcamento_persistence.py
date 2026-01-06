"""
Orcamento persistence service for saving and retrieving orcamento data.

This service provides CRUD operations for orcamentos table (TECH-013):
- create_orcamento: Create new orcamento linked to a lead
- get_orcamentos_by_lead: Retrieve all orcamentos for a lead
- update_orcamento: Update orcamento fields (partial updates)
"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

from src.services.audit_trail import (
    EntityType,
    log_entity_create_sync,
    log_entity_update_sync,
)
from src.services.conversation_persistence import get_supabase_client
from src.utils.logging import get_logger

logger = get_logger(__name__)


def create_orcamento(lead_id: str, data: Dict[str, Optional[Any]]) -> Optional[Dict[str, Any]]:
    """
    Create a new orcamento linked to a lead in Supabase.

    This function:
    1. Validates that lead_id exists in the leads table
    2. Creates orcamento with fields: resumo, produto, segmento, urgencia_compra, volume_diario
    3. Returns the created orcamento with id

    Args:
        lead_id: UUID of the lead (must exist in leads table)
        data: Dictionary with orcamento data fields
              - resumo: Summary of the orcamento
              - produto: Product name
              - segmento: Market segment
              - urgencia_compra: Purchase urgency
              - volume_diario: Daily volume (integer)

    Returns:
        Dictionary with orcamento data (including id, created_at, updated_at) or None on error

    Examples:
        >>> # Create orcamento for existing lead
        >>> orcamento = create_orcamento(lead_id, {
        ...     "resumo": "Orçamento para FBM100",
        ...     "produto": "FBM100",
        ...     "segmento": "Alimentício",
        ...     "urgencia_compra": "Alta",
        ...     "volume_diario": 1000
        ... })
    """
    if not lead_id:
        logger.warning(
            "Invalid lead_id for create_orcamento",
            extra={"lead_id": lead_id, "operation": "create_orcamento"},
        )
        return None

    try:
        client = get_supabase_client()
    except Exception as e:
        logger.error(
            "Failed to get Supabase client",
            extra={"error": str(e), "operation": "create_orcamento"},
        )
        return None

    if not client:
        logger.debug(
            "Supabase not available - orcamento not persisted",
            extra={"lead_id": lead_id, "operation": "create_orcamento"},
        )
        return None

    try:
        # Validate that lead exists
        # Note: We can't use get_lead_by_phone here since we have lead_id, not phone
        # We'll validate by attempting to get the lead by id
        lead_check = (
            client.table("leads")
            .select("id")
            .eq("id", lead_id)
            .execute()
        )

        if not lead_check.data or len(lead_check.data) == 0:
            logger.warning(
                "Lead not found for create_orcamento",
                extra={"lead_id": lead_id, "operation": "create_orcamento"},
            )
            return None

        # Filter out None/null values
        filtered_data = {k: v for k, v in data.items() if v is not None}

        # Prepare insert payload
        insert_payload = {
            "lead": lead_id,
            **filtered_data,
        }

        # Insert orcamento
        response = (
            client.table("orcamentos")
            .insert(insert_payload)
            .execute()
        )

        if response.data and len(response.data) > 0:
            orcamento = response.data[0]
            orcamento_id = orcamento.get("id")

            # Audit trail (TECH-028): Log CREATE
            log_entity_create_sync(
                entity_type=EntityType.ORCAMENTO,
                entity_id=str(orcamento_id),
                data=orcamento,
            )

            logger.info(
                "Orcamento created successfully",
                extra={
                    "lead_id": lead_id,
                    "orcamento_id": orcamento_id,
                    "fields": list(filtered_data.keys()),
                    "operation": "create_orcamento",
                },
            )
            return orcamento
        else:
            logger.warning(
                "No data returned from Supabase insert",
                extra={"lead_id": lead_id, "operation": "create_orcamento"},
            )
            return None

    except Exception as e:
        logger.error(
            "Failed to create orcamento",
            extra={
                "lead_id": lead_id,
                "error": str(e),
                "operation": "create_orcamento",
            },
            exc_info=True,
        )
        return None


def get_orcamentos_by_lead(lead_id: str) -> List[Dict[str, Any]]:
    """
    Get all orcamentos linked to a lead from Supabase.

    This function:
    1. Queries Supabase for all orcamentos with matching lead_id
    2. Orders results by created_at desc (most recent first)
    3. Returns list of orcamentos (can be empty)

    Args:
        lead_id: UUID of the lead

    Returns:
        List of dictionaries with orcamento data, ordered by created_at desc

    Examples:
        >>> # Get all orcamentos for a lead
        >>> orcamentos = get_orcamentos_by_lead(lead_id)
        >>> for orcamento in orcamentos:
        ...     print(orcamento["resumo"])
    """
    if not lead_id:
        logger.warning(
            "Invalid lead_id for get_orcamentos_by_lead",
            extra={"lead_id": lead_id, "operation": "get_orcamentos_by_lead"},
        )
        return []

    try:
        client = get_supabase_client()
    except Exception as e:
        logger.error(
            "Failed to get Supabase client",
            extra={"error": str(e), "operation": "get_orcamentos_by_lead"},
        )
        return []

    if not client:
        logger.debug(
            "Supabase not available - returning empty list",
            extra={"lead_id": lead_id, "operation": "get_orcamentos_by_lead"},
        )
        return []

    try:
        response = (
            client.table("orcamentos")
            .select("*")
            .eq("lead", lead_id)
            .order("created_at", desc=True)
            .execute()
        )

        orcamentos = response.data if response.data else []
        logger.debug(
            "Orcamentos retrieved successfully",
            extra={
                "lead_id": lead_id,
                "count": len(orcamentos),
                "operation": "get_orcamentos_by_lead",
            },
        )
        return orcamentos

    except Exception as e:
        logger.error(
            "Failed to get orcamentos by lead",
            extra={
                "lead_id": lead_id,
                "error": str(e),
                "operation": "get_orcamentos_by_lead",
            },
            exc_info=True,
        )
        return []


def update_orcamento(orcamento_id: str, data: Dict[str, Optional[Any]]) -> Optional[Dict[str, Any]]:
    """
    Update an orcamento in Supabase.

    This function:
    1. Filters out None/null fields for partial updates
    2. Updates orcamento with specified fields
    3. Updates updated_at field automatically
    4. Returns the updated orcamento

    Args:
        orcamento_id: UUID of the orcamento to update
        data: Dictionary with fields to update
              Fields with None/null values are filtered out for partial updates

    Returns:
        Dictionary with updated orcamento data or None on error

    Examples:
        >>> # Update orcamento fields
        >>> orcamento = update_orcamento(orcamento_id, {
        ...     "resumo": "Orçamento atualizado",
        ...     "volume_diario": 2000
        ... })
        >>> # Partial update (None values filtered)
        >>> orcamento = update_orcamento(orcamento_id, {
        ...     "oportunidade_pipe_id": "pipe-123",
        ...     "resumo": None  # This will be filtered out
        ... })
    """
    if not orcamento_id:
        logger.warning(
            "Invalid orcamento_id for update_orcamento",
            extra={"orcamento_id": orcamento_id, "operation": "update_orcamento"},
        )
        return None

    try:
        client = get_supabase_client()
    except Exception as e:
        logger.error(
            "Failed to get Supabase client",
            extra={"error": str(e), "operation": "update_orcamento"},
        )
        return None

    if not client:
        logger.debug(
            "Supabase not available - orcamento not updated",
            extra={"orcamento_id": orcamento_id, "operation": "update_orcamento"},
        )
        return None

    try:
        # Get existing orcamento for audit trail (before state)
        existing_orcamento = None
        try:
            existing_response = (
                client.table("orcamentos")
                .select("*")
                .eq("id", orcamento_id)
                .execute()
            )
            if existing_response.data and len(existing_response.data) > 0:
                existing_orcamento = existing_response.data[0]
        except Exception:
            # If we can't get existing, continue with update
            pass

        # Filter out None/null values for partial updates
        filtered_data = {k: v for k, v in data.items() if v is not None}

        if not filtered_data:
            logger.warning(
                "No valid fields to update",
                extra={"orcamento_id": orcamento_id, "operation": "update_orcamento"},
            )
            return None

        # Add updated_at timestamp
        filtered_data["updated_at"] = datetime.utcnow().isoformat()

        # Update orcamento
        response = (
            client.table("orcamentos")
            .update(filtered_data)
            .eq("id", orcamento_id)
            .execute()
        )

        if response.data and len(response.data) > 0:
            orcamento = response.data[0]

            # Audit trail (TECH-028): Log UPDATE
            if existing_orcamento:
                log_entity_update_sync(
                    entity_type=EntityType.ORCAMENTO,
                    entity_id=str(orcamento_id),
                    old_data=existing_orcamento,
                    new_data=orcamento,
                )

            logger.info(
                "Orcamento updated successfully",
                extra={
                    "orcamento_id": orcamento_id,
                    "fields_updated": list(filtered_data.keys()),
                    "operation": "update_orcamento",
                },
            )
            return orcamento
        else:
            logger.warning(
                "Orcamento not found or no data returned",
                extra={"orcamento_id": orcamento_id, "operation": "update_orcamento"},
            )
            return None

    except Exception as e:
        logger.error(
            "Failed to update orcamento",
            extra={
                "orcamento_id": orcamento_id,
                "error": str(e),
                "operation": "update_orcamento",
            },
            exc_info=True,
        )
        return None

