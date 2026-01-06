"""
API routes for pending operations management (TECH-030).

Provides endpoints for:
- Monitoring pending operations status
- Manual retry of failed operations
- Triggering batch processing

All endpoints require authentication (admin access).
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.jobs.sync_pending_operations import (
    process_pending_operations,
    retry_all_failed_operations,
    retry_failed_operation,
)
from src.services.pending_operations import (
    OperationStatus,
    get_failed_operations,
    get_operation_by_id,
    get_pending_operations,
    get_pending_operations_count,
    reset_failed_operation,
)
from src.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/pending-operations", tags=["pending-operations"])


class OperationStatusResponse(BaseModel):
    """Response model for pending operations status."""

    pending: int
    processing: int
    completed: int
    failed: int
    total: int


class ProcessingResultResponse(BaseModel):
    """Response model for processing results."""

    processed: int
    succeeded: int
    failed: int
    pending_remaining: int
    started_at: str | None = None
    completed_at: str | None = None
    error: str | None = None


class RetryResultResponse(BaseModel):
    """Response model for retry results."""

    total: int
    reset: int
    succeeded: int
    failed: int
    error: str | None = None


class OperationResponse(BaseModel):
    """Response model for a single operation."""

    id: str
    operation_type: str
    entity_type: str
    entity_id: str | None
    status: str
    retry_count: int
    max_retries: int
    last_error: str | None
    created_at: str
    updated_at: str


@router.get("/status", response_model=OperationStatusResponse)
async def get_status():
    """
    Get count of pending operations by status.

    Returns counts for: pending, processing, completed, failed, and total.

    **Authentication**: Admin access required.
    """
    logger.info("Getting pending operations status")

    try:
        counts = await get_pending_operations_count()
        return OperationStatusResponse(**counts)

    except Exception as e:
        logger.error(f"Error getting pending operations status: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/list")
async def list_operations(
    status: str = Query(default="pending", description="Filter by status"),
    limit: int = Query(default=50, ge=1, le=200, description="Max operations to return"),
    offset: int = Query(default=0, ge=0, description="Offset for pagination"),
):
    """
    List pending operations with optional filtering.

    **Parameters**:
    - status: Filter by status (pending, processing, completed, failed)
    - limit: Maximum number of operations to return (1-200)
    - offset: Offset for pagination

    **Authentication**: Admin access required.
    """
    logger.info(
        "Listing pending operations",
        extra={"status": status, "limit": limit, "offset": offset},
    )

    try:
        # Validate status
        valid_statuses = [s.value for s in OperationStatus]
        if status not in valid_statuses:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {valid_statuses}",
            )

        operations = await get_pending_operations(
            status=status,
            limit=limit,
            offset=offset,
        )

        return {
            "operations": operations,
            "count": len(operations),
            "status_filter": status,
            "limit": limit,
            "offset": offset,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing pending operations: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/{operation_id}")
async def get_operation(operation_id: str):
    """
    Get details of a specific pending operation.

    **Parameters**:
    - operation_id: UUID of the operation

    **Authentication**: Admin access required.
    """
    logger.info(f"Getting operation {operation_id}")

    try:
        operation = await get_operation_by_id(operation_id)

        if not operation:
            raise HTTPException(
                status_code=404,
                detail=f"Operation {operation_id} not found",
            )

        return operation

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting operation {operation_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/{operation_id}/retry")
async def retry_operation(operation_id: str):
    """
    Retry a specific failed operation.

    Resets the operation to pending status and attempts to process it.

    **Parameters**:
    - operation_id: UUID of the operation to retry

    **Authentication**: Admin access required.
    """
    logger.info(f"Retrying operation {operation_id}")

    try:
        success = await retry_failed_operation(operation_id)

        if success:
            return {
                "success": True,
                "message": f"Operation {operation_id} processed successfully",
            }
        else:
            return {
                "success": False,
                "message": f"Operation {operation_id} retry failed or not found",
            }

    except Exception as e:
        logger.error(f"Error retrying operation {operation_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/{operation_id}/reset")
async def reset_operation(operation_id: str):
    """
    Reset a failed operation to pending status (without processing).

    This allows the operation to be picked up by the next job run.

    **Parameters**:
    - operation_id: UUID of the operation to reset

    **Authentication**: Admin access required.
    """
    logger.info(f"Resetting operation {operation_id}")

    try:
        success = await reset_failed_operation(operation_id)

        if success:
            return {
                "success": True,
                "message": f"Operation {operation_id} reset to pending",
            }
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Operation {operation_id} not found or not in failed status",
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resetting operation {operation_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/retry-all-failed", response_model=RetryResultResponse)
async def retry_all_failed(
    batch_size: int = Query(default=50, ge=1, le=200, description="Max operations to retry"),
):
    """
    Retry all failed operations.

    Resets all failed operations to pending and processes them.

    **Parameters**:
    - batch_size: Maximum number of operations to retry (1-200)

    **Authentication**: Admin access required.
    """
    logger.info(f"Retrying all failed operations (batch_size={batch_size})")

    try:
        results = await retry_all_failed_operations(batch_size=batch_size)
        return RetryResultResponse(**results)

    except Exception as e:
        logger.error(f"Error retrying all failed operations: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/process", response_model=ProcessingResultResponse)
async def trigger_processing(
    batch_size: int = Query(default=50, ge=1, le=200, description="Max operations to process"),
    check_alerts: bool = Query(default=True, description="Check and send alerts"),
):
    """
    Trigger processing of pending operations.

    Processes a batch of pending operations and returns results.

    **Parameters**:
    - batch_size: Maximum number of operations to process (1-200)
    - check_alerts: Whether to check thresholds and send alerts

    **Authentication**: Admin access required.
    """
    logger.info(
        f"Triggering pending operations processing (batch_size={batch_size})",
    )

    try:
        results = await process_pending_operations(
            batch_size=batch_size,
            check_alerts=check_alerts,
        )
        return ProcessingResultResponse(**results)

    except Exception as e:
        logger.error(f"Error processing pending operations: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/failed/list")
async def list_failed_operations(
    limit: int = Query(default=50, ge=1, le=200, description="Max operations to return"),
):
    """
    List all failed operations.

    Returns operations that have reached their max retry limit.

    **Parameters**:
    - limit: Maximum number of operations to return (1-200)

    **Authentication**: Admin access required.
    """
    logger.info(f"Listing failed operations (limit={limit})")

    try:
        operations = await get_failed_operations(limit=limit)

        return {
            "operations": operations,
            "count": len(operations),
        }

    except Exception as e:
        logger.error(f"Error listing failed operations: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e
