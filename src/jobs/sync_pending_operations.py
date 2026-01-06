"""
Job for reprocessing pending CRM operations (TECH-030).

This job periodically processes pending operations that failed to sync
with Piperun CRM and retries them.

Features:
- Batch processing of pending operations
- Individual retry for each operation
- Automatic status updates
- Alert generation for high volume of pending operations
- Configurable batch size and retry limits

Usage:
    # Run manually
    python -m src.jobs.sync_pending_operations

    # Or import and call
    from src.jobs.sync_pending_operations import process_pending_operations
    await process_pending_operations()
"""

import asyncio
from datetime import datetime
from typing import Any

from src.services.alerts import send_alert
from src.services.lead_persistence import update_lead_sync_status
from src.services.pending_operations import (
    OperationStatus,
    OperationType,
    get_pending_operations,
    get_pending_operations_count,
    increment_retry_count,
    mark_operation_completed,
    update_operation_status,
)
from src.services.piperun_sync import sync_lead_to_piperun
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Configuration
DEFAULT_BATCH_SIZE = 50
PENDING_ALERT_THRESHOLD = 50
FAILED_ALERT_THRESHOLD = 10


async def process_single_operation(operation: dict[str, Any]) -> bool:
    """
    Process a single pending operation.

    Args:
        operation: Pending operation record from database

    Returns:
        True if processed successfully, False otherwise
    """
    operation_id = operation.get("id")
    operation_type = operation.get("operation_type")
    payload = operation.get("payload", {})

    logger.info(
        "Processing pending operation",
        extra={
            "operation_id": operation_id,
            "operation_type": operation_type,
            "retry_count": operation.get("retry_count", 0),
        },
    )

    try:
        # Mark as processing
        await update_operation_status(operation_id, OperationStatus.PROCESSING)

        # Process based on operation type
        if operation_type == OperationType.CREATE_DEAL.value:
            result = await _process_create_deal(operation_id, payload)
        else:
            logger.warning(
                f"Unknown operation type: {operation_type}",
                extra={"operation_id": operation_id},
            )
            result = False

        if result:
            # Mark as completed
            await mark_operation_completed(operation_id)

            # Update lead sync status
            phone = payload.get("phone")
            if phone:
                update_lead_sync_status(phone, "synced")

            logger.info(
                "Pending operation completed successfully",
                extra={"operation_id": operation_id},
            )
            return True
        else:
            # Increment retry count (may mark as failed if max retries reached)
            await increment_retry_count(
                operation_id,
                error="Operation returned unsuccessful result",
            )
            return False

    except Exception as e:
        logger.error(
            f"Error processing pending operation: {e}",
            extra={"operation_id": operation_id},
            exc_info=True,
        )

        # Increment retry count with error
        await increment_retry_count(operation_id, error=str(e))
        return False


async def _process_create_deal(operation_id: str, payload: dict[str, Any]) -> bool:
    """
    Process a create_deal pending operation.

    Args:
        operation_id: UUID of the pending operation
        payload: Operation payload with lead data

    Returns:
        True if deal created successfully, False otherwise
    """
    phone = payload.get("phone")
    if not phone:
        logger.error(
            "Missing phone in create_deal payload",
            extra={"operation_id": operation_id},
        )
        return False

    lead_data = payload.get("lead_data", {})
    orcamento_id = payload.get("orcamento_id")
    conversation_summary = payload.get("conversation_summary")
    force_create = payload.get("force_create", False)

    try:
        # Call sync_lead_to_piperun directly (without fallback wrapper)
        deal_id = await sync_lead_to_piperun(
            phone=phone,
            lead_data=lead_data,
            orcamento_id=orcamento_id,
            conversation_summary=conversation_summary,
            force_create=force_create,
        )

        if deal_id:
            logger.info(
                "Pending create_deal operation completed",
                extra={
                    "operation_id": operation_id,
                    "deal_id": deal_id,
                    "phone": phone,
                },
            )
            return True
        else:
            logger.warning(
                "create_deal returned no deal_id",
                extra={"operation_id": operation_id, "phone": phone},
            )
            return False

    except Exception as e:
        logger.error(
            f"Error in create_deal operation: {e}",
            extra={"operation_id": operation_id, "phone": phone},
        )
        raise


async def process_pending_operations(
    batch_size: int = DEFAULT_BATCH_SIZE,
    check_alerts: bool = True,
) -> dict[str, int]:
    """
    Process a batch of pending operations.

    Args:
        batch_size: Maximum number of operations to process
        check_alerts: Whether to check and send alerts for thresholds

    Returns:
        Dictionary with processing results:
        - processed: Number of operations processed
        - succeeded: Number of successful operations
        - failed: Number of failed operations
        - pending_remaining: Number of pending operations remaining
    """
    logger.info(
        "Starting pending operations processing",
        extra={"batch_size": batch_size},
    )

    results = {
        "processed": 0,
        "succeeded": 0,
        "failed": 0,
        "pending_remaining": 0,
        "started_at": datetime.utcnow().isoformat(),
    }

    try:
        # Get pending operations
        operations = await get_pending_operations(
            status=OperationStatus.PENDING,
            limit=batch_size,
        )

        if not operations:
            logger.info("No pending operations to process")
            return results

        logger.info(f"Found {len(operations)} pending operations to process")

        # Process each operation
        for operation in operations:
            try:
                success = await process_single_operation(operation)
                results["processed"] += 1

                if success:
                    results["succeeded"] += 1
                else:
                    results["failed"] += 1

            except Exception as e:
                logger.error(
                    f"Error processing operation {operation.get('id')}: {e}",
                    exc_info=True,
                )
                results["processed"] += 1
                results["failed"] += 1

        # Get remaining count
        counts = await get_pending_operations_count()
        results["pending_remaining"] = counts.get("pending", 0)
        results["completed_at"] = datetime.utcnow().isoformat()

        # Check alerts
        if check_alerts:
            await _check_and_send_alerts(counts)

        logger.info(
            "Pending operations processing completed",
            extra=results,
        )

        return results

    except Exception as e:
        logger.error(
            f"Error in process_pending_operations: {e}",
            exc_info=True,
        )
        results["error"] = str(e)
        return results


async def _check_and_send_alerts(counts: dict[str, int]) -> None:
    """
    Check operation counts and send alerts if thresholds exceeded.

    Args:
        counts: Dictionary with operation counts by status
    """
    pending_count = counts.get("pending", 0)
    failed_count = counts.get("failed", 0)

    # Alert for high number of pending operations
    if pending_count >= PENDING_ALERT_THRESHOLD:
        await send_alert(
            title="Alto volume de operações pendentes CRM",
            message=f"Há {pending_count} operações pendentes aguardando sincronização com o Piperun CRM. "
            f"Verifique se o CRM está acessível e se há problemas de conexão.",
            severity="warning",
            context={
                "pending_count": pending_count,
                "threshold": PENDING_ALERT_THRESHOLD,
                "failed_count": failed_count,
            },
        )
        logger.warning(
            f"Alert sent: {pending_count} pending operations (threshold: {PENDING_ALERT_THRESHOLD})"
        )

    # Alert for high number of failed operations
    if failed_count >= FAILED_ALERT_THRESHOLD:
        await send_alert(
            title="Operações CRM falharam permanentemente",
            message=f"Há {failed_count} operações que falharam após atingir o limite de tentativas. "
            f"Intervenção manual pode ser necessária.",
            severity="error",
            context={
                "failed_count": failed_count,
                "threshold": FAILED_ALERT_THRESHOLD,
                "pending_count": pending_count,
            },
        )
        logger.error(
            f"Alert sent: {failed_count} failed operations (threshold: {FAILED_ALERT_THRESHOLD})"
        )


async def retry_failed_operation(operation_id: str) -> bool:
    """
    Retry a specific failed operation.

    Args:
        operation_id: UUID of the operation to retry

    Returns:
        True if retried successfully, False otherwise
    """
    from src.services.pending_operations import get_operation_by_id, reset_failed_operation

    logger.info(f"Retrying failed operation {operation_id}")

    try:
        # Reset operation to pending
        reset_success = await reset_failed_operation(operation_id)
        if not reset_success:
            logger.warning(f"Could not reset operation {operation_id}")
            return False

        # Get operation and process it
        operation = await get_operation_by_id(operation_id)
        if not operation:
            logger.warning(f"Operation {operation_id} not found after reset")
            return False

        return await process_single_operation(operation)

    except Exception as e:
        logger.error(f"Error retrying operation {operation_id}: {e}")
        return False


async def retry_all_failed_operations(batch_size: int = DEFAULT_BATCH_SIZE) -> dict[str, int]:
    """
    Retry all failed operations.

    Args:
        batch_size: Maximum number of operations to retry

    Returns:
        Dictionary with retry results
    """
    from src.services.pending_operations import get_failed_operations, reset_failed_operation

    logger.info("Retrying all failed operations")

    results = {
        "total": 0,
        "reset": 0,
        "succeeded": 0,
        "failed": 0,
    }

    try:
        # Get failed operations
        failed_ops = await get_failed_operations(limit=batch_size)
        results["total"] = len(failed_ops)

        if not failed_ops:
            logger.info("No failed operations to retry")
            return results

        # Reset and process each operation
        for operation in failed_ops:
            operation_id = operation.get("id")

            try:
                # Reset to pending
                reset_success = await reset_failed_operation(operation_id)
                if reset_success:
                    results["reset"] += 1

                    # Process operation
                    success = await process_single_operation(operation)
                    if success:
                        results["succeeded"] += 1
                    else:
                        results["failed"] += 1

            except Exception as e:
                logger.error(f"Error retrying operation {operation_id}: {e}")
                results["failed"] += 1

        logger.info("Retry all failed operations completed", extra=results)
        return results

    except Exception as e:
        logger.error(f"Error in retry_all_failed_operations: {e}")
        results["error"] = str(e)
        return results


# Entry point for running as script
if __name__ == "__main__":
    import sys

    async def main():
        """Main entry point for the job."""
        print("Starting pending operations sync job...")
        results = await process_pending_operations()
        print(f"Results: {results}")
        return results

    try:
        results = asyncio.run(main())
        sys.exit(0 if results.get("failed", 0) == 0 else 1)
    except KeyboardInterrupt:
        print("\nJob interrupted")
        sys.exit(130)
    except Exception as e:
        print(f"Job failed: {e}")
        sys.exit(1)
