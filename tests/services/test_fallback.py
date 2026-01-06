"""
Tests for CRM fallback service (TECH-030).

This module tests the fallback mechanism for CRM operations,
including local persistence and async reprocessing of pending operations.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from src.services.pending_operations import (
    EntityType,
    OperationStatus,
    OperationType,
    PendingOperationsError,
    create_pending_operation,
    delete_completed_operations,
    get_failed_operations,
    get_operation_by_id,
    get_pending_operations,
    get_pending_operations_count,
    increment_retry_count,
    mark_operation_completed,
    reset_failed_operation,
    update_operation_status,
)


class TestPendingOperationsCRUD:
    """Tests for pending operations CRUD functions."""

    @pytest.mark.asyncio
    async def test_create_pending_operation_success(self):
        """Test creating a new pending operation."""
        mock_result = MagicMock()
        mock_result.data = [
            {
                "id": "test-uuid-123",
                "operation_type": "create_deal",
                "entity_type": "deal",
                "entity_id": "lead-123",
                "payload": {"title": "Test Deal"},
                "status": "pending",
                "retry_count": 0,
                "max_retries": 10,
            }
        ]

        mock_client = MagicMock()
        mock_client.table.return_value.insert.return_value.execute.return_value = mock_result

        with patch(
            "src.services.pending_operations.get_supabase_client",
            return_value=mock_client,
        ):
            operation = await create_pending_operation(
                operation_type=OperationType.CREATE_DEAL,
                entity_type=EntityType.DEAL,
                payload={"title": "Test Deal"},
                entity_id="lead-123",
            )

            assert operation is not None
            assert operation["id"] == "test-uuid-123"
            assert operation["status"] == "pending"
            assert operation["operation_type"] == "create_deal"

    @pytest.mark.asyncio
    async def test_create_pending_operation_no_client(self):
        """Test that creation fails gracefully when client unavailable."""
        with patch(
            "src.services.pending_operations.get_supabase_client",
            return_value=None,
        ):
            with pytest.raises(PendingOperationsError) as exc_info:
                await create_pending_operation(
                    operation_type=OperationType.CREATE_DEAL,
                    entity_type=EntityType.DEAL,
                    payload={"title": "Test"},
                )

            assert "Supabase client not available" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_pending_operations_success(self):
        """Test retrieving pending operations."""
        mock_result = MagicMock()
        mock_result.data = [
            {"id": "op-1", "status": "pending"},
            {"id": "op-2", "status": "pending"},
        ]

        mock_client = MagicMock()
        mock_query = MagicMock()
        mock_query.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.range.return_value = mock_query
        mock_query.execute.return_value = mock_result
        mock_client.table.return_value = mock_query

        with patch(
            "src.services.pending_operations.get_supabase_client",
            return_value=mock_client,
        ):
            operations = await get_pending_operations(
                status=OperationStatus.PENDING,
                limit=10,
            )

            assert len(operations) == 2
            assert operations[0]["id"] == "op-1"

    @pytest.mark.asyncio
    async def test_get_pending_operations_empty(self):
        """Test retrieving when no pending operations exist."""
        mock_result = MagicMock()
        mock_result.data = []

        mock_client = MagicMock()
        mock_query = MagicMock()
        mock_query.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.range.return_value = mock_query
        mock_query.execute.return_value = mock_result
        mock_client.table.return_value = mock_query

        with patch(
            "src.services.pending_operations.get_supabase_client",
            return_value=mock_client,
        ):
            operations = await get_pending_operations()

            assert len(operations) == 0

    @pytest.mark.asyncio
    async def test_update_operation_status_success(self):
        """Test updating operation status."""
        mock_result = MagicMock()
        mock_result.data = [{"id": "op-1", "status": "completed"}]

        mock_client = MagicMock()
        mock_query = MagicMock()
        mock_query.update.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.execute.return_value = mock_result
        mock_client.table.return_value = mock_query

        with patch(
            "src.services.pending_operations.get_supabase_client",
            return_value=mock_client,
        ):
            result = await update_operation_status(
                operation_id="op-1",
                status=OperationStatus.COMPLETED,
            )

            assert result is True

    @pytest.mark.asyncio
    async def test_update_operation_status_not_found(self):
        """Test updating non-existent operation."""
        mock_result = MagicMock()
        mock_result.data = []

        mock_client = MagicMock()
        mock_query = MagicMock()
        mock_query.update.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.execute.return_value = mock_result
        mock_client.table.return_value = mock_query

        with patch(
            "src.services.pending_operations.get_supabase_client",
            return_value=mock_client,
        ):
            result = await update_operation_status(
                operation_id="non-existent",
                status=OperationStatus.COMPLETED,
            )

            assert result is False

    @pytest.mark.asyncio
    async def test_increment_retry_count_success(self):
        """Test incrementing retry count."""
        # Mock get_operation_by_id
        operation_data = {
            "id": "op-1",
            "retry_count": 2,
            "max_retries": 10,
            "status": "pending",
        }

        mock_update_result = MagicMock()
        mock_update_result.data = [{"id": "op-1", "retry_count": 3}]

        mock_client = MagicMock()
        mock_query = MagicMock()
        mock_query.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.update.return_value = mock_query
        mock_query.execute.return_value = mock_update_result
        mock_client.table.return_value = mock_query

        with patch(
            "src.services.pending_operations.get_supabase_client",
            return_value=mock_client,
        ), patch(
            "src.services.pending_operations.get_operation_by_id",
            return_value=operation_data,
        ):
            result = await increment_retry_count(
                operation_id="op-1",
                error="Connection timeout",
            )

            assert result is not None
            assert result["retry_count"] == 3

    @pytest.mark.asyncio
    async def test_increment_retry_count_marks_failed(self):
        """Test that operation is marked failed after max retries."""
        operation_data = {
            "id": "op-1",
            "retry_count": 9,
            "max_retries": 10,
            "status": "pending",
        }

        mock_update_result = MagicMock()
        mock_update_result.data = [{"id": "op-1", "retry_count": 10, "status": "failed"}]

        mock_client = MagicMock()
        mock_query = MagicMock()
        mock_query.update.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.execute.return_value = mock_update_result
        mock_client.table.return_value = mock_query

        with patch(
            "src.services.pending_operations.get_supabase_client",
            return_value=mock_client,
        ), patch(
            "src.services.pending_operations.get_operation_by_id",
            return_value=operation_data,
        ):
            result = await increment_retry_count(operation_id="op-1")

            assert result is not None
            # Check that update was called with failed status
            call_args = mock_query.update.call_args
            assert call_args[0][0]["status"] == "failed"


class TestGetOperationsCount:
    """Tests for pending operations count function."""

    @pytest.mark.asyncio
    async def test_get_pending_operations_count_success(self):
        """Test getting counts by status."""
        mock_client = MagicMock()

        # Mock different counts for each status
        def mock_count_response(status):
            mock_result = MagicMock()
            counts = {"pending": 5, "processing": 2, "completed": 10, "failed": 1}
            mock_result.count = counts.get(status, 0)
            return mock_result

        mock_query = MagicMock()
        mock_query.select.return_value = mock_query
        mock_query.eq.side_effect = lambda key, value: mock_query
        mock_query.execute.side_effect = [
            mock_count_response("pending"),
            mock_count_response("processing"),
            mock_count_response("completed"),
            mock_count_response("failed"),
        ]
        mock_client.table.return_value = mock_query

        with patch(
            "src.services.pending_operations.get_supabase_client",
            return_value=mock_client,
        ):
            counts = await get_pending_operations_count()

            assert counts["pending"] == 5
            assert counts["processing"] == 2
            assert counts["completed"] == 10
            assert counts["failed"] == 1
            assert counts["total"] == 18


class TestMarkOperationCompleted:
    """Tests for marking operations as completed."""

    @pytest.mark.asyncio
    async def test_mark_operation_completed_success(self):
        """Test marking operation as completed."""
        mock_result = MagicMock()
        mock_result.data = [{"id": "op-1", "status": "completed"}]

        mock_client = MagicMock()
        mock_query = MagicMock()
        mock_query.update.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.execute.return_value = mock_result
        mock_client.table.return_value = mock_query

        with patch(
            "src.services.pending_operations.get_supabase_client",
            return_value=mock_client,
        ):
            result = await mark_operation_completed(operation_id="op-1")

            assert result is True


class TestResetFailedOperation:
    """Tests for resetting failed operations."""

    @pytest.mark.asyncio
    async def test_reset_failed_operation_success(self):
        """Test resetting failed operation to pending."""
        mock_result = MagicMock()
        mock_result.data = [{"id": "op-1", "status": "pending", "retry_count": 0}]

        mock_client = MagicMock()
        mock_query = MagicMock()
        mock_query.update.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.execute.return_value = mock_result
        mock_client.table.return_value = mock_query

        with patch(
            "src.services.pending_operations.get_supabase_client",
            return_value=mock_client,
        ):
            result = await reset_failed_operation(operation_id="op-1")

            assert result is True

    @pytest.mark.asyncio
    async def test_reset_failed_operation_not_found(self):
        """Test resetting non-existent or non-failed operation."""
        mock_result = MagicMock()
        mock_result.data = []

        mock_client = MagicMock()
        mock_query = MagicMock()
        mock_query.update.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.execute.return_value = mock_result
        mock_client.table.return_value = mock_query

        with patch(
            "src.services.pending_operations.get_supabase_client",
            return_value=mock_client,
        ):
            result = await reset_failed_operation(operation_id="non-existent")

            assert result is False


class TestGetFailedOperations:
    """Tests for getting failed operations."""

    @pytest.mark.asyncio
    async def test_get_failed_operations_success(self):
        """Test getting failed operations."""
        mock_result = MagicMock()
        mock_result.data = [
            {"id": "op-1", "status": "failed"},
            {"id": "op-2", "status": "failed"},
        ]

        mock_client = MagicMock()
        mock_query = MagicMock()
        mock_query.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.range.return_value = mock_query
        mock_query.execute.return_value = mock_result
        mock_client.table.return_value = mock_query

        with patch(
            "src.services.pending_operations.get_supabase_client",
            return_value=mock_client,
        ):
            operations = await get_failed_operations(limit=10)

            assert len(operations) == 2


class TestDeleteCompletedOperations:
    """Tests for cleaning up completed operations."""

    @pytest.mark.asyncio
    async def test_delete_completed_operations_success(self):
        """Test deleting old completed operations."""
        mock_result = MagicMock()
        mock_result.data = [{"id": "op-1"}, {"id": "op-2"}, {"id": "op-3"}]

        mock_client = MagicMock()
        mock_query = MagicMock()
        mock_query.delete.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.lt.return_value = mock_query
        mock_query.execute.return_value = mock_result
        mock_client.table.return_value = mock_query

        with patch(
            "src.services.pending_operations.get_supabase_client",
            return_value=mock_client,
        ):
            deleted_count = await delete_completed_operations(days_old=30)

            assert deleted_count == 3


class TestOperationEnums:
    """Tests for operation type and status enums."""

    def test_operation_type_values(self):
        """Test operation type enum values."""
        assert OperationType.CREATE_DEAL.value == "create_deal"
        assert OperationType.CREATE_PERSON.value == "create_person"
        assert OperationType.CREATE_COMPANY.value == "create_company"
        assert OperationType.CREATE_NOTE.value == "create_note"
        assert OperationType.UPDATE_DEAL.value == "update_deal"

    def test_entity_type_values(self):
        """Test entity type enum values."""
        assert EntityType.DEAL.value == "deal"
        assert EntityType.PERSON.value == "person"
        assert EntityType.COMPANY.value == "company"
        assert EntityType.NOTE.value == "note"

    def test_operation_status_values(self):
        """Test operation status enum values."""
        assert OperationStatus.PENDING.value == "pending"
        assert OperationStatus.PROCESSING.value == "processing"
        assert OperationStatus.COMPLETED.value == "completed"
        assert OperationStatus.FAILED.value == "failed"
