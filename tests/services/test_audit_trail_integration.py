"""
Integration tests for audit trail service (TECH-028).

These tests require a real Supabase connection and the audit_logs table.
Run with: pytest tests/services/test_audit_trail_integration.py -v
"""

import os
from datetime import datetime

import pytest

from src.services.audit_trail import (
    AuditAction,
    EntityType,
    get_audit_logs,
    log_api_call_sync,
    log_audit_sync,
    log_entity_create_sync,
    log_entity_update_sync,
)
from src.services.conversation_persistence import get_supabase_client


# Skip all tests if Supabase is not configured
pytestmark = pytest.mark.skipif(
    not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
    reason="Supabase not configured - skipping integration tests",
)


class TestAuditTrailIntegration:
    """Integration tests for audit trail with real Supabase."""

    def test_supabase_client_available(self):
        """Test that Supabase client is available."""
        client = get_supabase_client()
        assert client is not None, "Supabase client should be available"

    def test_log_audit_sync_creates_record(self):
        """Test that log_audit_sync creates a record in the database."""
        test_entity_id = f"test-{datetime.utcnow().timestamp()}"

        result = log_audit_sync(
            action=AuditAction.CREATE,
            entity_type=EntityType.LEAD,
            entity_id=test_entity_id,
            changes={"after": {"name": "Test Lead", "phone": "5511999999999"}},
            metadata={"test": True, "source": "integration_test"},
        )

        assert result is True, "log_audit_sync should return True on success"

        # Cleanup: delete test record
        client = get_supabase_client()
        if client:
            client.table("audit_logs").delete().eq("entity_id", test_entity_id).execute()

    def test_log_entity_create_sync(self):
        """Test logging entity creation."""
        test_entity_id = f"test-create-{datetime.utcnow().timestamp()}"

        result = log_entity_create_sync(
            entity_type=EntityType.LEAD,
            entity_id=test_entity_id,
            data={"name": "Test", "phone": "5511999999999", "email": "test@example.com"},
        )

        assert result is True

        # Cleanup
        client = get_supabase_client()
        if client:
            client.table("audit_logs").delete().eq("entity_id", test_entity_id).execute()

    def test_log_entity_update_sync(self):
        """Test logging entity update with diff."""
        test_entity_id = f"test-update-{datetime.utcnow().timestamp()}"

        result = log_entity_update_sync(
            entity_type=EntityType.LEAD,
            entity_id=test_entity_id,
            old_data={"name": "Old Name", "city": "São Paulo"},
            new_data={"name": "New Name", "city": "São Paulo"},
        )

        assert result is True

        # Cleanup
        client = get_supabase_client()
        if client:
            client.table("audit_logs").delete().eq("entity_id", test_entity_id).execute()

    def test_log_api_call_sync(self):
        """Test logging API call."""
        test_entity_id = f"test-api-{datetime.utcnow().timestamp()}"

        result = log_api_call_sync(
            service="piperun",
            operation="create_deal",
            entity_id=test_entity_id,
            status="success",
            metadata={"duration_ms": 150},
        )

        assert result is True

        # Cleanup
        client = get_supabase_client()
        if client:
            client.table("audit_logs").delete().eq("entity_id", test_entity_id).execute()

    def test_sensitive_data_is_masked_in_database(self):
        """Test that sensitive data is masked when stored in database."""
        test_entity_id = f"test-mask-{datetime.utcnow().timestamp()}"

        # Log with sensitive data
        log_audit_sync(
            action=AuditAction.CREATE,
            entity_type=EntityType.LEAD,
            entity_id=test_entity_id,
            changes={
                "after": {
                    "phone": "5511999999999",
                    "email": "user@example.com",
                    "cnpj": "12345678000190",
                    "api_token": "secret123",
                }
            },
        )

        # Query the record
        client = get_supabase_client()
        if client:
            response = (
                client.table("audit_logs")
                .select("changes")
                .eq("entity_id", test_entity_id)
                .execute()
            )

            if response.data and len(response.data) > 0:
                changes = response.data[0]["changes"]
                after = changes.get("after", {})

                # Verify masking
                assert after.get("phone") == "5511***9999", "Phone should be masked"
                assert after.get("email") == "u***@example.com", "Email should be masked"
                assert "***" in after.get("cnpj", ""), "CNPJ should be masked"
                assert after.get("api_token") == "[REDACTED]", "Token should be redacted"

            # Cleanup
            client.table("audit_logs").delete().eq("entity_id", test_entity_id).execute()


@pytest.mark.asyncio
class TestAuditTrailAsyncIntegration:
    """Async integration tests for audit trail."""

    async def test_get_audit_logs_returns_records(self):
        """Test querying audit logs."""
        # First create a test record
        test_entity_id = f"test-query-{datetime.utcnow().timestamp()}"

        log_audit_sync(
            action=AuditAction.CREATE,
            entity_type=EntityType.ORCAMENTO,
            entity_id=test_entity_id,
            changes={"after": {"resumo": "Test"}},
        )

        # Query the logs
        logs = await get_audit_logs(
            entity_type=EntityType.ORCAMENTO,
            entity_id=test_entity_id,
            limit=10,
        )

        assert len(logs) >= 1, "Should find at least one audit log"
        assert logs[0]["entity_id"] == test_entity_id

        # Cleanup
        client = get_supabase_client()
        if client:
            client.table("audit_logs").delete().eq("entity_id", test_entity_id).execute()

    async def test_get_audit_logs_filters_by_action(self):
        """Test filtering audit logs by action type."""
        logs = await get_audit_logs(
            action=AuditAction.API_CALL,
            limit=5,
        )

        # All returned logs should have API_CALL action
        for log in logs:
            assert log["action"] == "API_CALL"
