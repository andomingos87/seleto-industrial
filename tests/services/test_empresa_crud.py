"""
Tests for empresa CRUD operations.

This test file covers CRUD operations for empresa table:
- create_empresa: Create new empresa with CNPJ deduplication
- get_empresa_by_cnpj: Retrieve empresa by normalized CNPJ
- update_empresa: Update empresa fields (partial updates)
"""

import pytest
from unittest.mock import Mock, patch
from uuid import uuid4

from src.services.empresa_persistence import (
    create_empresa,
    get_empresa_by_cnpj,
    update_empresa,
)


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for testing."""
    client = Mock()
    table_mock = Mock()
    client.table.return_value = table_mock
    return client, table_mock


@pytest.fixture
def sample_empresa_data():
    """Sample empresa data for testing."""
    # Note: Using valid CNPJ with correct check digits (TECH-026)
    return {
        "nome": "Empresa Teste LTDA",
        "cidade": "São Paulo",
        "uf": "SP",
        "cnpj": "11222333000181",  # Valid CNPJ with correct check digits
        "site": "https://example.com",
        "email": "contato@example.com",
        "telefone": "5511999999999",
    }


# Valid CNPJs for testing (with correct check digits - TECH-026)
VALID_CNPJ_1 = "11222333000181"
VALID_CNPJ_2 = "11444777000161"
VALID_CNPJ_3 = "19131243000197"
# Invalid CNPJ (wrong check digits)
INVALID_CNPJ = "12345678000190"


class TestCreateEmpresa:
    """Tests for create_empresa function."""

    # TODO: Implement tests once create_empresa is implemented
    # - Test: create_empresa creates empresa with normalized CNPJ
    # - Test: create_empresa normalizes CNPJ before insertion
    # - Test: create_empresa validates CNPJ has 14 digits
    # - Test: create_empresa returns created empresa with id
    # - Test: Logging of successful creation

    def test_placeholder(self):
        """Placeholder test to ensure test file structure is valid."""
        assert True


class TestGetEmpresaByCnpj:
    """Tests for get_empresa_by_cnpj function."""

    @patch("src.services.empresa_persistence.get_supabase_client")
    def test_returns_empresa_when_exists(self, mock_get_client, mock_supabase_client):
        """Test that get_empresa_by_cnpj returns empresa when exists."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        empresa_id = str(uuid4())
        select_mock = Mock()
        eq_mock = Mock()
        eq_mock.execute.return_value = Mock(data=[{
            "id": empresa_id,
            "cnpj": VALID_CNPJ_1,
            "nome": "Empresa Teste",
            "cidade": "São Paulo",
        }])

        table_mock.select.return_value = select_mock
        select_mock.eq.return_value = eq_mock

        result = get_empresa_by_cnpj(VALID_CNPJ_1)

        assert result is not None
        assert result["id"] == empresa_id
        assert result["cnpj"] == VALID_CNPJ_1
        select_mock.eq.assert_called_once_with("cnpj", VALID_CNPJ_1)

    @patch("src.services.empresa_persistence.get_supabase_client")
    def test_returns_none_when_not_exists(self, mock_get_client, mock_supabase_client):
        """Test that get_empresa_by_cnpj returns None when not exists."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        select_mock = Mock()
        eq_mock = Mock()
        eq_mock.execute.return_value = Mock(data=[])

        table_mock.select.return_value = select_mock
        select_mock.eq.return_value = eq_mock

        result = get_empresa_by_cnpj(VALID_CNPJ_1)

        assert result is None

    @patch("src.services.empresa_persistence.get_supabase_client")
    def test_normalizes_cnpj_before_search(self, mock_get_client, mock_supabase_client):
        """Test that get_empresa_by_cnpj normalizes CNPJ before search."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        empresa_id = str(uuid4())
        select_mock = Mock()
        eq_mock = Mock()
        eq_mock.execute.return_value = Mock(data=[{"id": empresa_id, "cnpj": VALID_CNPJ_1}])

        table_mock.select.return_value = select_mock
        select_mock.eq.return_value = eq_mock

        # CNPJ with formatting (using valid CNPJ formatted)
        result = get_empresa_by_cnpj("11.222.333/0001-81")

        assert result is not None
        # Verify normalized CNPJ was used in query
        select_mock.eq.assert_called_once_with("cnpj", VALID_CNPJ_1)

    def test_returns_none_for_invalid_cnpj(self):
        """Test that None is returned for invalid CNPJ."""
        # Empty CNPJ
        result = get_empresa_by_cnpj("")
        assert result is None

        # CNPJ with wrong length
        result = get_empresa_by_cnpj("1234567890")  # Only 10 digits
        assert result is None

    @patch("src.services.empresa_persistence.get_supabase_client")
    def test_returns_none_when_supabase_not_available(self, mock_get_client):
        """Test that None is returned when Supabase is not available."""
        mock_get_client.return_value = None

        result = get_empresa_by_cnpj(VALID_CNPJ_1)

        assert result is None

    @patch("src.services.empresa_persistence.get_supabase_client")
    def test_handles_exception_gracefully(self, mock_get_client, mock_supabase_client):
        """Test that exceptions are handled gracefully."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        select_mock = Mock()
        eq_mock = Mock()
        eq_mock.execute.side_effect = Exception("Database error")

        table_mock.select.return_value = select_mock
        select_mock.eq.return_value = eq_mock

        result = get_empresa_by_cnpj(VALID_CNPJ_1)

        assert result is None


class TestUpdateEmpresa:
    """Tests for update_empresa function."""

    @patch("src.services.empresa_persistence.get_supabase_client")
    def test_updates_specified_fields(self, mock_get_client, mock_supabase_client):
        """Test that update_empresa updates specified fields."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        empresa_id = str(uuid4())
        update_mock = Mock()
        eq_mock = Mock()
        execute_mock = Mock()
        execute_mock.data = [{
            "id": empresa_id,
            "nome": "Empresa Atualizada",
            "email": "novo@example.com",
            "updated_at": "2026-01-01T01:00:00Z",
        }]
        eq_mock.execute.return_value = execute_mock

        table_mock.update.return_value = update_mock
        update_mock.eq.return_value = eq_mock

        result = update_empresa(empresa_id, {
            "nome": "Empresa Atualizada",
            "email": "novo@example.com",
        })

        assert result is not None
        assert result["nome"] == "Empresa Atualizada"
        assert result["email"] == "novo@example.com"
        table_mock.update.assert_called_once()
        update_mock.eq.assert_called_once_with("id", empresa_id)

    @patch("src.services.empresa_persistence.get_supabase_client")
    def test_normalizes_cnpj_if_provided(self, mock_get_client, mock_supabase_client):
        """Test that update_empresa normalizes CNPJ if provided."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        empresa_id = str(uuid4())
        update_mock = Mock()
        eq_mock = Mock()
        execute_mock = Mock()
        execute_mock.data = [{"id": empresa_id, "cnpj": VALID_CNPJ_1}]
        eq_mock.execute.return_value = execute_mock

        table_mock.update.return_value = update_mock
        update_mock.eq.return_value = eq_mock

        # CNPJ with formatting (using valid CNPJ formatted)
        result = update_empresa(empresa_id, {
            "cnpj": "11.222.333/0001-81",
        })

        assert result is not None
        # Verify normalized CNPJ was used
        call_args = table_mock.update.call_args
        assert call_args[0][0]["cnpj"] == VALID_CNPJ_1

    @patch("src.services.empresa_persistence.get_supabase_client")
    def test_doesnt_overwrite_fields_with_null(self, mock_get_client, mock_supabase_client):
        """Test that update_empresa doesn't overwrite fields with null."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        empresa_id = str(uuid4())
        update_mock = Mock()
        eq_mock = Mock()
        execute_mock = Mock()
        execute_mock.data = [{
            "id": empresa_id,
            "nome": "Empresa Existente",  # Preserved
            "email": "novo@example.com",  # New field
        }]
        eq_mock.execute.return_value = execute_mock

        table_mock.update.return_value = update_mock
        update_mock.eq.return_value = eq_mock

        result = update_empresa(empresa_id, {
            "email": "novo@example.com",
            "nome": None,  # Should be filtered out
        })

        assert result is not None
        # Verify None values were filtered from payload
        call_args = table_mock.update.call_args
        payload = call_args[0][0]
        assert "email" in payload
        assert "nome" not in payload or payload.get("nome") is not None

    @patch("src.services.empresa_persistence.get_supabase_client")
    def test_updates_updated_at_field(self, mock_get_client, mock_supabase_client):
        """Test that update_empresa updates updated_at field."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        empresa_id = str(uuid4())
        update_mock = Mock()
        eq_mock = Mock()
        execute_mock = Mock()
        execute_mock.data = [{"id": empresa_id, "updated_at": "2026-01-01T01:00:00Z"}]
        eq_mock.execute.return_value = execute_mock

        table_mock.update.return_value = update_mock
        update_mock.eq.return_value = eq_mock

        result = update_empresa(empresa_id, {"nome": "Test"})

        assert result is not None
        # Verify updated_at was added to payload
        call_args = table_mock.update.call_args
        payload = call_args[0][0]
        assert "updated_at" in payload

    @patch("src.services.empresa_persistence.get_supabase_client")
    def test_fails_with_invalid_id(self, mock_get_client, mock_supabase_client):
        """Test that update_empresa fails with invalid id."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        invalid_id = str(uuid4())
        update_mock = Mock()
        eq_mock = Mock()
        eq_mock.execute.return_value = Mock(data=[])  # Not found

        table_mock.update.return_value = eq_mock

        result = update_empresa(invalid_id, {"nome": "Test"})

        assert result is None

    @patch("src.services.empresa_persistence.get_supabase_client")
    def test_validates_cnpj_when_provided(self, mock_get_client, mock_supabase_client):
        """Test that update_empresa validates CNPJ when provided."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        # Invalid CNPJ (too short)
        result = update_empresa(str(uuid4()), {
            "cnpj": "1234567890",  # Only 10 digits
        })

        assert result is None

    @patch("src.services.empresa_persistence.get_supabase_client")
    def test_returns_none_when_supabase_not_available(self, mock_get_client):
        """Test that None is returned when Supabase is not available."""
        mock_get_client.return_value = None

        result = update_empresa(str(uuid4()), {"nome": "Test"})

        assert result is None

    def test_returns_none_for_empty_id(self):
        """Test that None is returned for empty id."""
        result = update_empresa("", {"nome": "Test"})
        assert result is None

    @patch("src.services.empresa_persistence.get_supabase_client")
    def test_returns_none_when_no_valid_fields(self, mock_get_client, mock_supabase_client):
        """Test that None is returned when no valid fields to update."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        result = update_empresa(str(uuid4()), {
            "nome": None,
            "email": None,
        })

        assert result is None

    @patch("src.services.empresa_persistence.get_supabase_client")
    def test_handles_exception_gracefully(self, mock_get_client, mock_supabase_client):
        """Test that exceptions are handled gracefully."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        update_mock = Mock()
        eq_mock = Mock()
        eq_mock.execute.side_effect = Exception("Database error")

        table_mock.update.return_value = eq_mock

        result = update_empresa(str(uuid4()), {"nome": "Test"})

        assert result is None


class TestEmpresaDeduplication:
    """Tests for CNPJ deduplication in empresa operations."""

    @patch("src.services.empresa_persistence.get_supabase_client")
    def test_different_cnpj_formats_recognized_as_duplicates(self, mock_get_client, mock_supabase_client):
        """Test that different CNPJ formats are recognized as duplicates."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        existing_empresa_id = str(uuid4())
        
        # Mock check for existing empresa (found existing)
        select_mock = Mock()
        eq_mock = Mock()
        eq_mock.execute.return_value = Mock(data=[{"id": existing_empresa_id}])
        select_mock.eq.return_value = eq_mock
        table_mock.select.return_value = select_mock

        # Try to create with different CNPJ format (should be recognized as duplicate)
        result = create_empresa({
            "nome": "Empresa Teste",
            "cnpj": "11.222.333/0001-81",  # Different format, same CNPJ (valid)
        })

        assert result is None
        # Verify check was done with normalized CNPJ
        select_mock.eq.assert_called_with("cnpj", VALID_CNPJ_1)


class TestEmpresaNormalization:
    """Tests for CNPJ normalization in empresa operations."""

    @patch("src.services.empresa_persistence.get_supabase_client")
    def test_cnpj_normalization_in_create_empresa(self, mock_get_client, mock_supabase_client):
        """Test CNPJ normalization in create_empresa with various formats."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        empresa_id = str(uuid4())
        
        # Mock check for existing empresa
        select_mock = Mock()
        eq_mock = Mock()
        eq_mock.execute.return_value = Mock(data=[])
        select_mock.eq.return_value = eq_mock
        table_mock.select.return_value = select_mock
        
        # Mock insert
        insert_mock = Mock()
        execute_mock = Mock()
        execute_mock.data = [{"id": empresa_id, "cnpj": VALID_CNPJ_1}]
        insert_mock.execute.return_value = execute_mock
        table_mock.insert.return_value = insert_mock

        # Test various CNPJ formats (all normalize to VALID_CNPJ_1)
        # Using valid CNPJ 11222333000181 in different formats
        formats = [
            "11.222.333/0001-81",  # Fully formatted
            "11222333/0001-81",    # Partially formatted
            VALID_CNPJ_1,          # Digits only
        ]

        for cnpj_format in formats:
            create_empresa({"nome": "Test", "cnpj": cnpj_format})
            call_args = table_mock.insert.call_args
            assert call_args[0][0]["cnpj"] == VALID_CNPJ_1

    @patch("src.services.empresa_persistence.get_supabase_client")
    def test_cnpj_normalization_in_get_empresa_by_cnpj(self, mock_get_client, mock_supabase_client):
        """Test CNPJ normalization in get_empresa_by_cnpj with various formats."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        empresa_id = str(uuid4())
        select_mock = Mock()
        eq_mock = Mock()
        eq_mock.execute.return_value = Mock(data=[{"id": empresa_id, "cnpj": VALID_CNPJ_1}])

        table_mock.select.return_value = select_mock
        select_mock.eq.return_value = eq_mock

        # Test various CNPJ formats (all normalize to VALID_CNPJ_1)
        # Using valid CNPJ 11222333000181 in different formats
        formats = [
            "11.222.333/0001-81",  # Fully formatted
            "11222333/0001-81",    # Partially formatted
            VALID_CNPJ_1,          # Digits only
        ]

        for cnpj_format in formats:
            get_empresa_by_cnpj(cnpj_format)
            select_mock.eq.assert_called_with("cnpj", VALID_CNPJ_1)

    @patch("src.services.empresa_persistence.get_supabase_client")
    def test_cnpj_normalization_in_update_empresa(self, mock_get_client, mock_supabase_client):
        """Test CNPJ normalization in update_empresa."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        empresa_id = str(uuid4())
        update_mock = Mock()
        eq_mock = Mock()
        execute_mock = Mock()
        execute_mock.data = [{"id": empresa_id, "cnpj": VALID_CNPJ_1}]
        eq_mock.execute.return_value = execute_mock

        table_mock.update.return_value = update_mock
        update_mock.eq.return_value = eq_mock

        # CNPJ with formatting (using valid CNPJ formatted)
        result = update_empresa(empresa_id, {
            "cnpj": "11.222.333/0001-81",
        })

        assert result is not None
        # Verify normalized CNPJ was used
        call_args = table_mock.update.call_args
        assert call_args[0][0]["cnpj"] == VALID_CNPJ_1

    def test_invalid_cnpj_formats_handled_correctly(self):
        """Test that invalid CNPJ formats are handled correctly."""
        invalid_cnpjs = ["", "abc", "123", "123456789012345"]  # Too long

        for invalid_cnpj in invalid_cnpjs:
            result_create = create_empresa({"nome": "Test", "cnpj": invalid_cnpj})
            result_get = get_empresa_by_cnpj(invalid_cnpj)
            assert result_create is None or result_create is None  # Should fail or return None
            assert result_get is None


class TestEmpresaErrorHandling:
    """Tests for error handling in empresa operations."""

    @patch("src.services.empresa_persistence.get_supabase_client")
    def test_database_connection_errors_handled(self, mock_get_client):
        """Test that database connection errors are handled."""
        mock_get_client.side_effect = Exception("Connection error")

        result = create_empresa({"nome": "Test"})
        assert result is None

        result = get_empresa_by_cnpj(VALID_CNPJ_1)
        assert result is None

        result = update_empresa(str(uuid4()), {"nome": "Test"})
        assert result is None

    @patch("src.services.empresa_persistence.get_supabase_client")
    def test_constraint_violations_handled(self, mock_get_client, mock_supabase_client):
        """Test that constraint violations are handled."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        # Mock check for existing empresa
        select_mock = Mock()
        eq_mock = Mock()
        eq_mock.execute.return_value = Mock(data=[])
        select_mock.eq.return_value = eq_mock
        table_mock.select.return_value = select_mock
        
        # Mock insert with constraint violation
        insert_mock = Mock()
        insert_mock.execute.side_effect = Exception("Unique constraint violation")

        table_mock.insert.return_value = insert_mock

        result = create_empresa({"nome": "Test", "cnpj": VALID_CNPJ_1})
        assert result is None


class TestEmpresaIntegration:
    """Integration tests for empresa CRUD operations."""

    @pytest.mark.integration
    @patch("src.services.empresa_persistence.get_supabase_client")
    def test_end_to_end_empresa_operations(self, mock_get_client, mock_supabase_client, sample_empresa_data):
        """Test end-to-end: create empresa, retrieve by CNPJ, update."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        empresa_id = str(uuid4())
        test_cnpj = VALID_CNPJ_1

        # Track which select call we're on
        select_call_count = [0]

        def select_side_effect(*args, **kwargs):
            select_call_count[0] += 1
            select_mock = Mock()
            eq_mock = Mock()

            if select_call_count[0] == 1:
                # First call: check for existing empresa (none found)
                eq_mock.execute.return_value = Mock(data=[])
            else:
                # Subsequent calls: return the empresa
                eq_mock.execute.return_value = Mock(data=[{
                    "id": empresa_id,
                    **sample_empresa_data,
                    "cnpj": test_cnpj,
                }])

            select_mock.eq.return_value = eq_mock
            return select_mock

        table_mock.select.side_effect = select_side_effect

        # Mock insert
        insert_mock = Mock()
        execute_insert_mock = Mock()
        execute_insert_mock.data = [{
            "id": empresa_id,
            **sample_empresa_data,
            "cnpj": test_cnpj,
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        }]
        insert_mock.execute.return_value = execute_insert_mock
        table_mock.insert.return_value = insert_mock

        # Mock update
        update_mock = Mock()
        eq_update_mock = Mock()
        execute_update_mock = Mock()
        execute_update_mock.data = [{
            "id": empresa_id,
            **sample_empresa_data,
            "email": "novo@example.com",
            "cnpj": test_cnpj,
        }]
        eq_update_mock.execute.return_value = execute_update_mock
        table_mock.update.return_value = update_mock
        update_mock.eq.return_value = eq_update_mock

        # 1. Create empresa
        created_empresa = create_empresa(sample_empresa_data)
        assert created_empresa is not None
        assert created_empresa["id"] == empresa_id
        assert created_empresa["cnpj"] == test_cnpj

        # 2. Retrieve empresa by CNPJ
        retrieved_empresa = get_empresa_by_cnpj("12.345.678/0001-90")  # With formatting
        assert retrieved_empresa is not None
        assert retrieved_empresa["id"] == empresa_id

        # 3. Update empresa
        updated_empresa = update_empresa(empresa_id, {
            "email": "novo@example.com",
        })
        assert updated_empresa is not None
        assert updated_empresa["email"] == "novo@example.com"

    @pytest.mark.integration
    @patch("src.services.empresa_persistence.get_supabase_client")
    def test_dedupe_by_cnpj(self, mock_get_client, mock_supabase_client):
        """Test deduplication by CNPJ."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        existing_empresa_id = str(uuid4())
        test_cnpj = VALID_CNPJ_1

        # Mock check for existing empresa (found existing)
        select_mock = Mock()
        eq_mock = Mock()
        eq_mock.execute.return_value = Mock(data=[{"id": existing_empresa_id}])
        select_mock.eq.return_value = eq_mock
        table_mock.select.return_value = select_mock

        # Try to create empresa with same CNPJ (different format)
        result = create_empresa({
            "nome": "Nova Empresa",
            "cnpj": "12.345.678/0001-90",  # Same CNPJ, different format
        })

        assert result is None
        # Verify insert was not called
        table_mock.insert.assert_not_called()

