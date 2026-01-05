"""
Tests for lead CRUD operations.

This test file covers CRUD operations for leads table:
- upsert_lead: Create or update lead with idempotency by phone
- get_lead_by_phone: Retrieve lead by normalized phone number
"""

import pytest
from unittest.mock import Mock, patch
from uuid import uuid4
from typing import Dict, Optional

from src.services.lead_persistence import (
    upsert_lead,
    get_lead_by_phone,
)


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for testing."""
    client = Mock()
    table_mock = Mock()
    client.table.return_value = table_mock
    return client, table_mock


@pytest.fixture
def sample_lead_data():
    """Sample lead data for testing."""
    return {
        "name": "João Silva",
        "email": "joao@example.com",
        "phone": "5511999999999",
        "city": "São Paulo",
        "uf": "SP",
        "produto_interesse": "FBM100",
        "temperatura": "quente",
    }


class TestUpsertLead:
    """Tests for upsert_lead function."""

    @patch("src.services.lead_persistence.get_supabase_client")
    def test_creates_new_lead_when_not_exists(self, mock_get_client, mock_supabase_client):
        """Test that upsert_lead creates new lead when not exists."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        lead_id = str(uuid4())
        upsert_mock = Mock()
        execute_mock = Mock()
        execute_mock.data = [{
            "id": lead_id,
            "phone": "5511999999999",
            "name": "João Silva",
            "city": "São Paulo",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        }]
        upsert_mock.execute.return_value = execute_mock
        table_mock.upsert.return_value = upsert_mock

        result = upsert_lead("5511999999999", {"name": "João Silva", "city": "São Paulo"})

        assert result is not None
        assert result["id"] == lead_id
        assert result["phone"] == "5511999999999"
        assert result["name"] == "João Silva"
        table_mock.upsert.assert_called_once()
        call_args = table_mock.upsert.call_args
        assert call_args[0][0]["phone"] == "5511999999999"
        assert call_args[1]["on_conflict"] == "phone"

    @patch("src.services.lead_persistence.get_supabase_client")
    def test_updates_existing_lead_without_overwriting_with_null(self, mock_get_client, mock_supabase_client):
        """Test that upsert_lead updates existing lead without overwriting fields with null."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        lead_id = str(uuid4())
        upsert_mock = Mock()
        execute_mock = Mock()
        execute_mock.data = [{
            "id": lead_id,
            "phone": "5511999999999",
            "name": "João Silva",  # Existing field preserved
            "email": "joao@example.com",  # New field added
            "city": "São Paulo",  # Existing field preserved
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T01:00:00Z",
        }]
        upsert_mock.execute.return_value = execute_mock
        table_mock.upsert.return_value = upsert_mock

        # Update with partial data (email only, name=None should be filtered)
        result = upsert_lead("5511999999999", {
            "name": "João Silva",  # Existing value
            "email": "joao@example.com",  # New value
            "city": None,  # Should be filtered out
        })

        assert result is not None
        assert result["email"] == "joao@example.com"
        # Verify that None values were filtered out
        call_args = table_mock.upsert.call_args
        assert "city" not in call_args[0][0] or call_args[0][0].get("city") is not None

    @patch("src.services.lead_persistence.get_supabase_client")
    def test_normalizes_phone_before_operation(self, mock_get_client, mock_supabase_client):
        """Test that upsert_lead normalizes phone before operation."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        lead_id = str(uuid4())
        upsert_mock = Mock()
        execute_mock = Mock()
        execute_mock.data = [{"id": lead_id, "phone": "5511999999999"}]
        upsert_mock.execute.return_value = execute_mock
        table_mock.upsert.return_value = upsert_mock

        # Phone with formatting
        result = upsert_lead("+55 11 99999-9999", {"name": "João"})

        assert result is not None
        # Verify normalized phone was used
        call_args = table_mock.upsert.call_args
        assert call_args[0][0]["phone"] == "5511999999999"

    @patch("src.services.lead_persistence.get_supabase_client")
    def test_idempotency_multiple_upserts_same_phone(self, mock_get_client, mock_supabase_client):
        """Test that multiple upserts with same phone result in single lead (idempotency)."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        lead_id = str(uuid4())
        upsert_mock = Mock()
        execute_mock = Mock()
        execute_mock.data = [{"id": lead_id, "phone": "5511999999999", "name": "João"}]
        upsert_mock.execute.return_value = execute_mock
        table_mock.upsert.return_value = upsert_mock

        # First upsert
        result1 = upsert_lead("5511999999999", {"name": "João"})
        # Second upsert with same phone
        result2 = upsert_lead("5511999999999", {"city": "São Paulo"})

        # Both should return the same lead ID (idempotency)
        assert result1["id"] == result2["id"]
        assert table_mock.upsert.call_count == 2
        # Both calls should use on_conflict='phone'
        for call in table_mock.upsert.call_args_list:
            assert call[1]["on_conflict"] == "phone"

    @patch("src.services.lead_persistence.get_supabase_client")
    def test_partial_update_doesnt_overwrite_existing_fields_with_null(self, mock_get_client, mock_supabase_client):
        """Test that partial update doesn't overwrite existing fields with null."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        lead_id = str(uuid4())
        upsert_mock = Mock()
        execute_mock = Mock()
        execute_mock.data = [{
            "id": lead_id,
            "phone": "5511999999999",
            "name": "João Silva",  # Preserved
            "email": "joao@example.com",  # New
        }]
        upsert_mock.execute.return_value = execute_mock
        table_mock.upsert.return_value = upsert_mock

        # Update with None values - should be filtered out
        result = upsert_lead("5511999999999", {
            "email": "joao@example.com",
            "name": None,  # Should be filtered
            "city": None,  # Should be filtered
        })

        assert result is not None
        # Verify None values were filtered from payload
        call_args = table_mock.upsert.call_args
        payload = call_args[0][0]
        assert "email" in payload
        assert "name" not in payload or payload.get("name") is not None
        assert "city" not in payload

    @patch("src.services.lead_persistence.get_supabase_client")
    def test_returns_none_when_supabase_not_available(self, mock_get_client):
        """Test that None is returned when Supabase is not available."""
        mock_get_client.return_value = None

        result = upsert_lead("5511999999999", {"name": "João"})

        assert result is None

    def test_returns_none_for_invalid_phone(self):
        """Test that None is returned for invalid phone number."""
        result = upsert_lead("", {"name": "João"})
        assert result is None

        result = upsert_lead("invalid", {"name": "João"})
        assert result is None

    @patch("src.services.lead_persistence.get_supabase_client")
    def test_handles_exception_gracefully(self, mock_get_client, mock_supabase_client):
        """Test that exceptions are handled gracefully."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        upsert_mock = Mock()
        upsert_mock.execute.side_effect = Exception("Database error")
        table_mock.upsert.return_value = upsert_mock

        result = upsert_lead("5511999999999", {"name": "João"})

        assert result is None


class TestGetLeadByPhone:
    """Tests for get_lead_by_phone function."""

    @patch("src.services.lead_persistence.get_supabase_client")
    def test_returns_lead_when_exists(self, mock_get_client, mock_supabase_client):
        """Test that get_lead_by_phone returns lead when exists."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        lead_id = str(uuid4())
        select_mock = Mock()
        eq_mock = Mock()
        eq_mock.execute.return_value = Mock(data=[{
            "id": lead_id,
            "phone": "5511999999999",
            "name": "João Silva",
            "city": "São Paulo",
        }])

        table_mock.select.return_value = select_mock
        select_mock.eq.return_value = eq_mock

        result = get_lead_by_phone("5511999999999")

        assert result is not None
        assert result["id"] == lead_id
        assert result["phone"] == "5511999999999"
        assert result["name"] == "João Silva"
        select_mock.eq.assert_called_once_with("phone", "5511999999999")

    @patch("src.services.lead_persistence.get_supabase_client")
    def test_returns_none_when_not_exists(self, mock_get_client, mock_supabase_client):
        """Test that get_lead_by_phone returns None when not exists."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        select_mock = Mock()
        eq_mock = Mock()
        eq_mock.execute.return_value = Mock(data=[])

        table_mock.select.return_value = select_mock
        select_mock.eq.return_value = eq_mock

        result = get_lead_by_phone("5511999999999")

        assert result is None

    @patch("src.services.lead_persistence.get_supabase_client")
    def test_normalizes_phone_before_search(self, mock_get_client, mock_supabase_client):
        """Test that get_lead_by_phone normalizes phone before search."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        lead_id = str(uuid4())
        select_mock = Mock()
        eq_mock = Mock()
        eq_mock.execute.return_value = Mock(data=[{"id": lead_id, "phone": "5511999999999"}])

        table_mock.select.return_value = select_mock
        select_mock.eq.return_value = eq_mock

        # Phone with formatting
        result = get_lead_by_phone("+55 11 99999-9999")

        assert result is not None
        # Verify normalized phone was used in query
        select_mock.eq.assert_called_once_with("phone", "5511999999999")

    @patch("src.services.lead_persistence.get_supabase_client")
    def test_returns_none_when_supabase_not_available(self, mock_get_client):
        """Test that None is returned when Supabase is not available."""
        mock_get_client.return_value = None

        result = get_lead_by_phone("5511999999999")

        assert result is None

    def test_returns_none_for_invalid_phone(self):
        """Test that None is returned for invalid phone number."""
        result = get_lead_by_phone("")
        assert result is None

        result = get_lead_by_phone("invalid")
        assert result is None

    @patch("src.services.lead_persistence.get_supabase_client")
    def test_handles_exception_gracefully(self, mock_get_client, mock_supabase_client):
        """Test that exceptions are handled gracefully."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        select_mock = Mock()
        eq_mock = Mock()
        eq_mock.execute.side_effect = Exception("Database error")

        table_mock.select.return_value = select_mock
        select_mock.eq.return_value = eq_mock

        result = get_lead_by_phone("5511999999999")

        assert result is None


class TestLeadNormalization:
    """Tests for phone normalization in lead operations."""

    @patch("src.services.lead_persistence.get_supabase_client")
    def test_phone_normalization_in_upsert_lead(self, mock_get_client, mock_supabase_client):
        """Test phone normalization in upsert_lead with various formats."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        upsert_mock = Mock()
        execute_mock = Mock()
        execute_mock.data = [{"id": str(uuid4()), "phone": "5511999999999"}]
        upsert_mock.execute.return_value = execute_mock
        table_mock.upsert.return_value = upsert_mock

        # Test various phone formats with expected normalized values
        # normalize_phone() only removes non-digit characters, doesn't add country code
        formats_and_expected = [
            ("+55 11 99999-9999", "5511999999999"),  # Has country code
            ("(11) 99999-9999", "11999999999"),      # No country code - preserved as is
            ("11 99999-9999", "11999999999"),        # No country code - preserved as is
            ("5511999999999", "5511999999999"),      # Already normalized with country code
        ]

        for phone_format, expected in formats_and_expected:
            upsert_lead(phone_format, {"name": "Test"})
            call_args = table_mock.upsert.call_args
            assert call_args[0][0]["phone"] == expected

    @patch("src.services.lead_persistence.get_supabase_client")
    def test_phone_normalization_in_get_lead_by_phone(self, mock_get_client, mock_supabase_client):
        """Test phone normalization in get_lead_by_phone with various formats."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        select_mock = Mock()
        eq_mock = Mock()
        eq_mock.execute.return_value = Mock(data=[{"id": str(uuid4()), "phone": "5511999999999"}])

        table_mock.select.return_value = select_mock
        select_mock.eq.return_value = eq_mock

        # Test various phone formats with expected normalized values
        # normalize_phone() only removes non-digit characters, doesn't add country code
        formats_and_expected = [
            ("+55 11 99999-9999", "5511999999999"),  # Has country code
            ("(11) 99999-9999", "11999999999"),      # No country code - preserved as is
            ("11 99999-9999", "11999999999"),        # No country code - preserved as is
            ("5511999999999", "5511999999999"),      # Already normalized with country code
        ]

        for phone_format, expected in formats_and_expected:
            get_lead_by_phone(phone_format)
            select_mock.eq.assert_called_with("phone", expected)

    def test_invalid_phone_numbers_handled_correctly(self):
        """Test that invalid phone numbers are handled correctly."""
        invalid_phones = ["", "abc", "123", None]

        for invalid_phone in invalid_phones:
            if invalid_phone is None:
                continue
            result_upsert = upsert_lead(invalid_phone, {"name": "Test"})
            result_get = get_lead_by_phone(invalid_phone)
            assert result_upsert is None
            assert result_get is None


class TestLeadErrorHandling:
    """Tests for error handling in lead operations."""

    @patch("src.services.lead_persistence.get_supabase_client")
    def test_database_connection_errors_handled(self, mock_get_client):
        """Test that database connection errors are handled."""
        mock_get_client.side_effect = Exception("Connection error")

        result = upsert_lead("5511999999999", {"name": "Test"})
        assert result is None

        result = get_lead_by_phone("5511999999999")
        assert result is None

    @patch("src.services.lead_persistence.get_supabase_client")
    def test_constraint_violations_handled(self, mock_get_client, mock_supabase_client):
        """Test that constraint violations are handled."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        # Simulate constraint violation
        upsert_mock = Mock()
        upsert_mock.execute.side_effect = Exception("Unique constraint violation")

        table_mock.upsert.return_value = upsert_mock

        result = upsert_lead("5511999999999", {"name": "Test"})
        # Should return None on error
        assert result is None

    @patch("src.services.lead_persistence.get_supabase_client")
    def test_timeout_errors_handled(self, mock_get_client, mock_supabase_client):
        """Test that timeout errors are handled."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        upsert_mock = Mock()
        upsert_mock.execute.side_effect = TimeoutError("Request timeout")

        table_mock.upsert.return_value = upsert_mock

        result = upsert_lead("5511999999999", {"name": "Test"})
        assert result is None


class TestLeadIntegration:
    """Integration tests for lead CRUD operations."""

    @pytest.mark.integration
    @patch("src.services.lead_persistence.get_supabase_client")
    def test_end_to_end_lead_operations(self, mock_get_client, mock_supabase_client):
        """Test end-to-end: create lead, retrieve, update, verify idempotency."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        lead_id = str(uuid4())
        test_phone = "5511999999999"

        # Mock upsert response for creation
        upsert_mock = Mock()
        execute_mock = Mock()
        execute_mock.data = [{
            "id": lead_id,
            "phone": test_phone,
            "name": "João Silva",
            "city": "São Paulo",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        }]
        upsert_mock.execute.return_value = execute_mock
        table_mock.upsert.return_value = upsert_mock

        # Mock select response for retrieval
        select_mock = Mock()
        eq_mock = Mock()
        eq_mock.execute.return_value = Mock(data=[{
            "id": lead_id,
            "phone": test_phone,
            "name": "João Silva",
            "city": "São Paulo",
        }])
        table_mock.select.return_value = select_mock
        select_mock.eq.return_value = eq_mock

        # 1. Create lead
        created_lead = upsert_lead(test_phone, {"name": "João Silva", "city": "São Paulo"})
        assert created_lead is not None
        assert created_lead["id"] == lead_id
        assert created_lead["name"] == "João Silva"

        # 2. Retrieve lead
        retrieved_lead = get_lead_by_phone(test_phone)
        assert retrieved_lead is not None
        assert retrieved_lead["id"] == lead_id
        assert retrieved_lead["name"] == "João Silva"

        # 3. Update lead (partial update)
        execute_mock.data = [{
            "id": lead_id,
            "phone": test_phone,
            "name": "João Silva",
            "email": "joao@example.com",
            "city": "São Paulo",
            "updated_at": "2026-01-01T01:00:00Z",
        }]
        updated_lead = upsert_lead(test_phone, {"email": "joao@example.com"})
        assert updated_lead is not None
        assert updated_lead["email"] == "joao@example.com"
        assert updated_lead["name"] == "João Silva"  # Existing field preserved

        # 4. Verify idempotency - multiple upserts with same phone
        lead1 = upsert_lead(test_phone, {"name": "João"})
        lead2 = upsert_lead(test_phone, {"city": "SP"})
        # Both should refer to same lead (idempotency)
        assert lead1["id"] == lead2["id"]

