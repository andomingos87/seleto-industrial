"""
Pending operations service for CRM fallback (TECH-030).

This service manages operations that failed to sync with CRM and need to be retried.
When CRM is unavailable after retries, operations are stored locally for later sync.

Features:
- Create pending operations with payload
- Query pending operations by status
- Update operation status and retry count
- Track last error and attempt timestamp
"""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from src.services.conversation_persistence import get_supabase_client
from src.utils.logging import get_logger

logger = get_logger(__name__)


class OperationType(str, Enum):
    """Valid operation types for CRM sync."""

    CREATE_DEAL = "create_deal"
    CREATE_PERSON = "create_person"
    CREATE_COMPANY = "create_company"
    CREATE_NOTE = "create_note"
    UPDATE_DEAL = "update_deal"


class EntityType(str, Enum):
    """Valid entity types for CRM operations."""

    DEAL = "deal"
    PERSON = "person"
    COMPANY = "company"
    NOTE = "note"


class OperationStatus(str, Enum):
    """Status values for pending operations."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class PendingOperationsError(Exception):
    """Base exception for pending operations errors."""

    pass


async def create_pending_operation(
    operation_type: OperationType | str,
    entity_type: EntityType | str,
    payload: dict[str, Any],
    entity_id: str | None = None,
    max_retries: int = 10,
) -> dict[str, Any] | None:
    """
    Create a new pending operation for later CRM sync.

    Args:
        operation_type: Type of operation (create_deal, create_person, etc.)
        entity_type: Type of entity (deal, person, company, note)
        payload: Operation payload to be sent to CRM
        entity_id: Optional local entity ID (lead_id, orcamento_id, etc.)
        max_retries: Maximum retry attempts (default 10)

    Returns:
        Created operation record or None if failed

    Raises:
        PendingOperationsError: If creation fails
    """
    # Convert enums to strings if needed
    op_type = operation_type.value if isinstance(operation_type, OperationType) else operation_type
    ent_type = entity_type.value if isinstance(entity_type, EntityType) else entity_type

    logger.info(
        "Creating pending operation",
        extra={
            "operation_type": op_type,
            "entity_type": ent_type,
            "entity_id": entity_id,
        },
    )

    try:
        client = get_supabase_client()
        if not client:
            logger.error("Supabase client not available")
            raise PendingOperationsError("Supabase client not available")

        data = {
            "operation_type": op_type,
            "entity_type": ent_type,
            "entity_id": entity_id,
            "payload": payload,
            "status": OperationStatus.PENDING.value,
            "retry_count": 0,
            "max_retries": max_retries,
        }

        result = client.table("pending_operations").insert(data).execute()

        if result.data:
            operation = result.data[0]
            logger.info(
                "Pending operation created",
                extra={
                    "operation_id": operation.get("id"),
                    "operation_type": op_type,
                    "entity_type": ent_type,
                },
            )
            return operation

        logger.warning("No data returned from pending operation creation")
        return None

    except PendingOperationsError:
        raise
    except Exception as e:
        logger.error(
            f"Error creating pending operation: {e}",
            extra={
                "operation_type": op_type,
                "entity_type": ent_type,
                "error": str(e),
            },
        )
        raise PendingOperationsError(f"Failed to create pending operation: {e}") from e


async def get_pending_operations(
    status: OperationStatus | str = OperationStatus.PENDING,
    limit: int = 100,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """
    Get pending operations by status, ordered by created_at.

    Args:
        status: Operation status to filter by (default: pending)
        limit: Maximum number of operations to return (default: 100)
        offset: Number of operations to skip (default: 0)

    Returns:
        List of pending operation records
    """
    status_value = status.value if isinstance(status, OperationStatus) else status

    logger.debug(
        "Fetching pending operations",
        extra={"status": status_value, "limit": limit, "offset": offset},
    )

    try:
        client = get_supabase_client()
        if not client:
            logger.error("Supabase client not available")
            return []

        result = (
            client.table("pending_operations")
            .select("*")
            .eq("status", status_value)
            .order("created_at", desc=False)
            .range(offset, offset + limit - 1)
            .execute()
        )

        operations = result.data or []
        logger.debug(f"Found {len(operations)} pending operations with status={status_value}")
        return operations

    except Exception as e:
        logger.error(f"Error fetching pending operations: {e}")
        return []


async def get_pending_operations_count() -> dict[str, int]:
    """
    Get count of operations by status.

    Returns:
        Dictionary with counts by status: {"pending": N, "processing": N, "completed": N, "failed": N}
    """
    counts = {
        "pending": 0,
        "processing": 0,
        "completed": 0,
        "failed": 0,
        "total": 0,
    }

    try:
        client = get_supabase_client()
        if not client:
            logger.error("Supabase client not available")
            return counts

        for status in OperationStatus:
            result = (
                client.table("pending_operations")
                .select("id", count="exact")
                .eq("status", status.value)
                .execute()
            )
            counts[status.value] = result.count or 0

        counts["total"] = sum(counts[s.value] for s in OperationStatus)
        return counts

    except Exception as e:
        logger.error(f"Error getting pending operations count: {e}")
        return counts


async def get_operation_by_id(operation_id: str | UUID) -> dict[str, Any] | None:
    """
    Get a specific pending operation by ID.

    Args:
        operation_id: UUID of the operation

    Returns:
        Operation record or None if not found
    """
    try:
        client = get_supabase_client()
        if not client:
            logger.error("Supabase client not available")
            return None

        result = (
            client.table("pending_operations")
            .select("*")
            .eq("id", str(operation_id))
            .execute()
        )

        if result.data:
            return result.data[0]
        return None

    except Exception as e:
        logger.error(f"Error fetching operation {operation_id}: {e}")
        return None


async def update_operation_status(
    operation_id: str | UUID,
    status: OperationStatus | str,
    error: str | None = None,
) -> bool:
    """
    Update the status of a pending operation.

    Args:
        operation_id: UUID of the operation
        status: New status value
        error: Optional error message (for failed operations)

    Returns:
        True if updated successfully, False otherwise
    """
    status_value = status.value if isinstance(status, OperationStatus) else status

    logger.info(
        "Updating operation status",
        extra={
            "operation_id": str(operation_id),
            "new_status": status_value,
        },
    )

    try:
        client = get_supabase_client()
        if not client:
            logger.error("Supabase client not available")
            return False

        update_data: dict[str, Any] = {
            "status": status_value,
            "updated_at": datetime.utcnow().isoformat(),
        }

        if error:
            update_data["last_error"] = error

        if status_value == OperationStatus.COMPLETED.value:
            update_data["completed_at"] = datetime.utcnow().isoformat()

        if status_value == OperationStatus.PROCESSING.value:
            update_data["last_attempt_at"] = datetime.utcnow().isoformat()

        result = (
            client.table("pending_operations")
            .update(update_data)
            .eq("id", str(operation_id))
            .execute()
        )

        if result.data:
            logger.info(f"Operation {operation_id} status updated to {status_value}")
            return True

        logger.warning(f"No operation found with id {operation_id}")
        return False

    except Exception as e:
        logger.error(f"Error updating operation {operation_id} status: {e}")
        return False


async def increment_retry_count(
    operation_id: str | UUID,
    error: str | None = None,
) -> dict[str, Any] | None:
    """
    Increment the retry count for an operation and update last_error.

    If max_retries is reached, status is changed to 'failed'.

    Args:
        operation_id: UUID of the operation
        error: Optional error message from the last attempt

    Returns:
        Updated operation record or None if failed
    """
    logger.info(f"Incrementing retry count for operation {operation_id}")

    try:
        # First get current operation
        operation = await get_operation_by_id(operation_id)
        if not operation:
            logger.warning(f"Operation {operation_id} not found")
            return None

        client = get_supabase_client()
        if not client:
            logger.error("Supabase client not available")
            return None

        new_retry_count = operation["retry_count"] + 1
        max_retries = operation.get("max_retries", 10)

        update_data: dict[str, Any] = {
            "retry_count": new_retry_count,
            "last_attempt_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        if error:
            update_data["last_error"] = error

        # Check if max retries reached
        if new_retry_count >= max_retries:
            update_data["status"] = OperationStatus.FAILED.value
            logger.warning(
                f"Operation {operation_id} reached max retries ({max_retries}), marking as failed"
            )

        result = (
            client.table("pending_operations")
            .update(update_data)
            .eq("id", str(operation_id))
            .execute()
        )

        if result.data:
            return result.data[0]
        return None

    except Exception as e:
        logger.error(f"Error incrementing retry count for operation {operation_id}: {e}")
        return None


async def mark_operation_completed(
    operation_id: str | UUID,
    result_data: dict[str, Any] | None = None,
) -> bool:
    """
    Mark an operation as completed successfully.

    Args:
        operation_id: UUID of the operation
        result_data: Optional result data from CRM (stored in payload)

    Returns:
        True if marked successfully, False otherwise
    """
    logger.info(f"Marking operation {operation_id} as completed")

    try:
        client = get_supabase_client()
        if not client:
            logger.error("Supabase client not available")
            return False

        update_data: dict[str, Any] = {
            "status": OperationStatus.COMPLETED.value,
            "completed_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

        # Optionally update payload with result data
        if result_data:
            operation = await get_operation_by_id(operation_id)
            if operation:
                payload = operation.get("payload", {})
                payload["_crm_result"] = result_data
                update_data["payload"] = payload

        result = (
            client.table("pending_operations")
            .update(update_data)
            .eq("id", str(operation_id))
            .execute()
        )

        if result.data:
            logger.info(f"Operation {operation_id} marked as completed")
            return True

        return False

    except Exception as e:
        logger.error(f"Error marking operation {operation_id} as completed: {e}")
        return False


async def get_failed_operations(limit: int = 100) -> list[dict[str, Any]]:
    """
    Get operations that have failed (reached max retries).

    Args:
        limit: Maximum number of operations to return

    Returns:
        List of failed operation records
    """
    return await get_pending_operations(status=OperationStatus.FAILED, limit=limit)


async def reset_failed_operation(operation_id: str | UUID) -> bool:
    """
    Reset a failed operation to pending for retry.

    Args:
        operation_id: UUID of the operation

    Returns:
        True if reset successfully, False otherwise
    """
    logger.info(f"Resetting failed operation {operation_id} to pending")

    try:
        client = get_supabase_client()
        if not client:
            logger.error("Supabase client not available")
            return False

        update_data = {
            "status": OperationStatus.PENDING.value,
            "retry_count": 0,
            "last_error": None,
            "updated_at": datetime.utcnow().isoformat(),
        }

        result = (
            client.table("pending_operations")
            .update(update_data)
            .eq("id", str(operation_id))
            .eq("status", OperationStatus.FAILED.value)
            .execute()
        )

        if result.data:
            logger.info(f"Operation {operation_id} reset to pending")
            return True

        logger.warning(f"Operation {operation_id} not found or not in failed status")
        return False

    except Exception as e:
        logger.error(f"Error resetting operation {operation_id}: {e}")
        return False


async def delete_completed_operations(days_old: int = 30) -> int:
    """
    Delete completed operations older than specified days.

    Args:
        days_old: Delete operations completed more than this many days ago

    Returns:
        Number of deleted operations
    """
    from datetime import timedelta

    cutoff_date = datetime.utcnow() - timedelta(days=days_old)

    logger.info(f"Deleting completed operations older than {days_old} days")

    try:
        client = get_supabase_client()
        if not client:
            logger.error("Supabase client not available")
            return 0

        result = (
            client.table("pending_operations")
            .delete()
            .eq("status", OperationStatus.COMPLETED.value)
            .lt("completed_at", cutoff_date.isoformat())
            .execute()
        )

        deleted_count = len(result.data) if result.data else 0
        logger.info(f"Deleted {deleted_count} completed operations")
        return deleted_count

    except Exception as e:
        logger.error(f"Error deleting completed operations: {e}")
        return 0
