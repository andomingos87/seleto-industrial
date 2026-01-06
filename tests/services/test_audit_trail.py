"""
Tests for audit trail service (TECH-028).

Tests cover:
- Sensitive data masking (phone, email, CNPJ)
- Change computation for UPDATE operations
- Audit logging functions (with mocked Supabase)
"""

from unittest.mock import MagicMock, patch

import pytest

from src.services.audit_trail import (
    AuditAction,
    EntityType,
    compute_changes,
    log_api_call_sync,
    log_audit_sync,
    log_entity_create_sync,
    log_entity_update_sync,
    mask_cnpj,
    mask_email,
    mask_phone,
    mask_sensitive_data,
)


class TestMaskPhone:
    """Tests for mask_phone function."""

    def test_mask_phone_standard_brazilian(self):
        """Test masking standard Brazilian phone number."""
        result = mask_phone("5511999999999")
        assert result == "5511***9999"

    def test_mask_phone_without_country_code(self):
        """Test masking phone without country code."""
        result = mask_phone("11999999999")
        # First 4 digits + *** + last 4 digits
        assert result == "1199***9999"

    def test_mask_phone_with_formatting(self):
        """Test masking phone with formatting characters."""
        result = mask_phone("+55 (11) 99999-9999")
        assert result == "5511***9999"

    def test_mask_phone_short_number(self):
        """Test masking very short phone number."""
        result = mask_phone("12345")
        assert result == "***"

    def test_mask_phone_empty(self):
        """Test masking empty phone."""
        result = mask_phone("")
        assert result == ""

    def test_mask_phone_none_like(self):
        """Test masking None-like value."""
        result = mask_phone(None)
        assert result == ""


class TestMaskEmail:
    """Tests for mask_email function."""

    def test_mask_email_standard(self):
        """Test masking standard email."""
        result = mask_email("user@example.com")
        assert result == "u***@example.com"

    def test_mask_email_short_local(self):
        """Test masking email with short local part."""
        result = mask_email("ab@test.com")
        assert result == "a***@test.com"

    def test_mask_email_single_char_local(self):
        """Test masking email with single character local part."""
        result = mask_email("a@test.com")
        assert result == "***@test.com"

    def test_mask_email_no_at_sign(self):
        """Test masking invalid email without @."""
        result = mask_email("notanemail")
        assert result == "***"

    def test_mask_email_empty(self):
        """Test masking empty email."""
        result = mask_email("")
        assert result == "***"


class TestMaskCnpj:
    """Tests for mask_cnpj function."""

    def test_mask_cnpj_standard(self):
        """Test masking standard CNPJ."""
        result = mask_cnpj("12345678000190")
        assert result == "12.***.***/0001-90"

    def test_mask_cnpj_with_formatting(self):
        """Test masking CNPJ with formatting."""
        result = mask_cnpj("12.345.678/0001-90")
        assert result == "12.***.***/0001-90"

    def test_mask_cnpj_invalid_length(self):
        """Test masking CNPJ with invalid length."""
        result = mask_cnpj("123456")
        assert result == "***"

    def test_mask_cnpj_empty(self):
        """Test masking empty CNPJ."""
        result = mask_cnpj("")
        assert result == ""


class TestMaskSensitiveData:
    """Tests for mask_sensitive_data function."""

    def test_mask_phone_field(self):
        """Test masking phone field in dictionary."""
        data = {"phone": "5511999999999", "name": "Test"}
        result = mask_sensitive_data(data)
        assert result["phone"] == "5511***9999"
        assert result["name"] == "Test"

    def test_mask_email_field(self):
        """Test masking email field in dictionary."""
        data = {"email": "user@example.com", "name": "Test"}
        result = mask_sensitive_data(data)
        assert result["email"] == "u***@example.com"
        assert result["name"] == "Test"

    def test_mask_cnpj_field(self):
        """Test masking cnpj field in dictionary."""
        data = {"cnpj": "12345678000190", "name": "Test"}
        result = mask_sensitive_data(data)
        assert result["cnpj"] == "12.***.***/0001-90"
        assert result["name"] == "Test"

    def test_mask_token_field(self):
        """Test that token fields are completely redacted."""
        data = {"api_token": "secret123", "name": "Test"}
        result = mask_sensitive_data(data)
        assert result["api_token"] == "[REDACTED]"
        assert result["name"] == "Test"

    def test_mask_password_field(self):
        """Test that password fields are completely redacted."""
        data = {"password": "mypassword", "name": "Test"}
        result = mask_sensitive_data(data)
        assert result["password"] == "[REDACTED]"

    def test_mask_nested_dict(self):
        """Test masking nested dictionary."""
        data = {
            "user": {
                "phone": "5511999999999",
                "email": "user@example.com",
            },
            "name": "Test",
        }
        result = mask_sensitive_data(data)
        assert result["user"]["phone"] == "5511***9999"
        assert result["user"]["email"] == "u***@example.com"
        assert result["name"] == "Test"

    def test_mask_none_values(self):
        """Test handling of None values."""
        data = {"phone": None, "name": "Test"}
        result = mask_sensitive_data(data)
        assert result["phone"] is None
        assert result["name"] == "Test"

    def test_mask_empty_dict(self):
        """Test masking empty dictionary."""
        result = mask_sensitive_data({})
        assert result == {}

    def test_mask_telefone_field(self):
        """Test masking 'telefone' field (Portuguese)."""
        data = {"telefone": "5511999999999"}
        result = mask_sensitive_data(data)
        assert result["telefone"] == "5511***9999"

    def test_mask_cpf_field(self):
        """Test masking CPF field."""
        data = {"cpf": "12345678901"}
        result = mask_sensitive_data(data)
        assert result["cpf"] == "123.***.***-01"


class TestComputeChanges:
    """Tests for compute_changes function."""

    def test_compute_changes_create(self):
        """Test computing changes for CREATE operation (no old data)."""
        new_data = {"name": "Test", "phone": "5511999999999"}
        result = compute_changes(None, new_data)

        assert "after" in result
        assert "before" not in result
        # Sensitive data should be masked in 'after'
        assert result["after"]["phone"] == "5511***9999"

    def test_compute_changes_update(self):
        """Test computing changes for UPDATE operation."""
        old_data = {"name": "Old Name", "city": "São Paulo"}
        new_data = {"name": "New Name", "city": "São Paulo"}

        result = compute_changes(old_data, new_data)

        assert result["before"]["name"] == "Old Name"
        assert result["after"]["name"] == "New Name"
        # Unchanged fields should not appear
        assert "city" not in result["before"]
        assert "city" not in result["after"]

    def test_compute_changes_with_sensitive_data(self):
        """Test that sensitive data is masked in changes."""
        old_data = {"phone": "5511111111111", "name": "Test"}
        new_data = {"phone": "5511999999999", "name": "Test"}

        result = compute_changes(old_data, new_data)

        # Phone should be masked
        assert result["before"]["phone"] == "5511***1111"
        assert result["after"]["phone"] == "5511***9999"

    def test_compute_changes_no_changes(self):
        """Test computing changes when nothing changed."""
        old_data = {"name": "Test", "city": "SP"}
        new_data = {"name": "Test", "city": "SP"}

        result = compute_changes(old_data, new_data)

        assert result["before"] == {}
        assert result["after"] == {}


class TestLogAuditSync:
    """Tests for log_audit_sync function."""

    @patch("src.services.audit_trail.get_supabase_client")
    def test_log_audit_sync_success(self, mock_get_client):
        """Test successful audit log creation."""
        mock_client = MagicMock()
        mock_client.table.return_value.insert.return_value.execute.return_value.data = [
            {"id": "test-uuid"}
        ]
        mock_get_client.return_value = mock_client

        result = log_audit_sync(
            action=AuditAction.CREATE,
            entity_type=EntityType.LEAD,
            entity_id="lead-123",
            changes={"after": {"name": "Test"}},
        )

        assert result is True
        mock_client.table.assert_called_with("audit_logs")

    @patch("src.services.audit_trail.get_supabase_client")
    def test_log_audit_sync_no_client(self, mock_get_client):
        """Test audit log when Supabase not configured."""
        mock_get_client.return_value = None

        result = log_audit_sync(
            action=AuditAction.CREATE,
            entity_type=EntityType.LEAD,
            entity_id="lead-123",
        )

        assert result is False

    @patch("src.services.audit_trail.get_supabase_client")
    def test_log_audit_sync_exception(self, mock_get_client):
        """Test audit log handles exceptions gracefully."""
        mock_client = MagicMock()
        mock_client.table.return_value.insert.return_value.execute.side_effect = Exception(
            "DB Error"
        )
        mock_get_client.return_value = mock_client

        # Should not raise exception
        result = log_audit_sync(
            action=AuditAction.CREATE,
            entity_type=EntityType.LEAD,
            entity_id="lead-123",
        )

        assert result is False

    @patch("src.services.audit_trail.get_supabase_client")
    def test_log_audit_sync_masks_sensitive_data(self, mock_get_client):
        """Test that sensitive data is masked before logging."""
        mock_client = MagicMock()
        mock_client.table.return_value.insert.return_value.execute.return_value.data = [
            {"id": "test-uuid"}
        ]
        mock_get_client.return_value = mock_client

        log_audit_sync(
            action=AuditAction.CREATE,
            entity_type=EntityType.LEAD,
            entity_id="lead-123",
            changes={"after": {"phone": "5511999999999"}},
        )

        # Verify the insert was called with masked data
        insert_call = mock_client.table.return_value.insert.call_args
        inserted_data = insert_call[0][0]
        assert inserted_data["changes"]["after"]["phone"] == "5511***9999"


class TestLogEntityCreateSync:
    """Tests for log_entity_create_sync function."""

    @patch("src.services.audit_trail.log_audit_sync")
    def test_log_entity_create_sync(self, mock_log_audit):
        """Test logging entity creation."""
        mock_log_audit.return_value = True

        result = log_entity_create_sync(
            entity_type=EntityType.LEAD,
            entity_id="lead-123",
            data={"name": "Test", "phone": "5511999999999"},
        )

        assert result is True
        mock_log_audit.assert_called_once()
        call_kwargs = mock_log_audit.call_args[1]
        assert call_kwargs["action"] == AuditAction.CREATE
        assert call_kwargs["entity_type"] == EntityType.LEAD
        assert call_kwargs["entity_id"] == "lead-123"


class TestLogEntityUpdateSync:
    """Tests for log_entity_update_sync function."""

    @patch("src.services.audit_trail.log_audit_sync")
    def test_log_entity_update_sync(self, mock_log_audit):
        """Test logging entity update."""
        mock_log_audit.return_value = True

        result = log_entity_update_sync(
            entity_type=EntityType.LEAD,
            entity_id="lead-123",
            old_data={"name": "Old"},
            new_data={"name": "New"},
        )

        assert result is True
        mock_log_audit.assert_called_once()
        call_kwargs = mock_log_audit.call_args[1]
        assert call_kwargs["action"] == AuditAction.UPDATE
        assert call_kwargs["entity_type"] == EntityType.LEAD


class TestLogApiCallSync:
    """Tests for log_api_call_sync function."""

    @patch("src.services.audit_trail.log_audit_sync")
    def test_log_api_call_sync_success(self, mock_log_audit):
        """Test logging successful API call."""
        mock_log_audit.return_value = True

        result = log_api_call_sync(
            service="piperun",
            operation="create_deal",
            entity_id="deal-123",
            status="success",
            metadata={"duration_ms": 150},
        )

        assert result is True
        mock_log_audit.assert_called_once()
        call_kwargs = mock_log_audit.call_args[1]
        assert call_kwargs["action"] == AuditAction.API_CALL
        assert call_kwargs["entity_type"] == EntityType.API_CALL
        assert call_kwargs["metadata"]["service"] == "piperun"
        assert call_kwargs["metadata"]["operation"] == "create_deal"
        assert call_kwargs["metadata"]["status"] == "success"

    @patch("src.services.audit_trail.log_audit_sync")
    def test_log_api_call_sync_error(self, mock_log_audit):
        """Test logging failed API call."""
        mock_log_audit.return_value = True

        result = log_api_call_sync(
            service="piperun",
            operation="create_deal",
            status="error",
            metadata={"error_type": "validation"},
        )

        assert result is True
        call_kwargs = mock_log_audit.call_args[1]
        assert call_kwargs["metadata"]["status"] == "error"
        assert call_kwargs["metadata"]["error_type"] == "validation"


class TestAuditActionEnum:
    """Tests for AuditAction enum."""

    def test_audit_action_values(self):
        """Test AuditAction enum values."""
        assert AuditAction.CREATE.value == "CREATE"
        assert AuditAction.UPDATE.value == "UPDATE"
        assert AuditAction.DELETE.value == "DELETE"
        assert AuditAction.API_CALL.value == "API_CALL"


class TestEntityTypeEnum:
    """Tests for EntityType enum."""

    def test_entity_type_values(self):
        """Test EntityType enum values."""
        assert EntityType.LEAD.value == "lead"
        assert EntityType.ORCAMENTO.value == "orcamento"
        assert EntityType.EMPRESA.value == "empresa"
        assert EntityType.API_CALL.value == "api_call"
        assert EntityType.CONVERSATION.value == "conversation"
