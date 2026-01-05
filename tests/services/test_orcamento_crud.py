"""
Tests for orcamento CRUD operations.

This test file covers CRUD operations for orcamentos table:
- create_orcamento: Create new orcamento linked to a lead
- get_orcamentos_by_lead: Retrieve all orcamentos for a lead
- update_orcamento: Update orcamento fields (partial updates)
"""

import pytest
from unittest.mock import Mock, patch
from uuid import uuid4

from src.services.orcamento_persistence import (
    create_orcamento,
    get_orcamentos_by_lead,
    update_orcamento,
)


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for testing."""
    client = Mock()
    table_mock = Mock()
    client.table.return_value = table_mock
    return client, table_mock


@pytest.fixture
def sample_lead_id():
    """Sample lead ID for testing."""
    return str(uuid4())


@pytest.fixture
def sample_orcamento_data():
    """Sample orcamento data for testing."""
    return {
        "resumo": "Orçamento para FBM100",
        "produto": "FBM100",
        "segmento": "Alimentício",
        "urgencia_compra": "Alta",
        "volume_diario": 1000,
    }


class TestCreateOrcamento:
    """Tests for create_orcamento function."""

    @patch("src.services.orcamento_persistence.get_supabase_client")
    def test_creates_orcamento_linked_to_valid_lead(self, mock_get_client, mock_supabase_client, sample_lead_id, sample_orcamento_data):
        """Test that create_orcamento creates orcamento linked to valid lead."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        orcamento_id = str(uuid4())
        
        # Mock leads table for validation
        leads_table_mock = Mock()
        leads_select_mock = Mock()
        leads_eq_mock = Mock()
        leads_eq_mock.execute.return_value = Mock(data=[{"id": sample_lead_id}])
        leads_select_mock.eq.return_value = leads_eq_mock
        leads_table_mock.select.return_value = leads_select_mock
        
        # Mock orcamentos table for insert
        orcamentos_table_mock = Mock()
        insert_mock = Mock()
        execute_mock = Mock()
        execute_mock.data = [{
            "id": orcamento_id,
            "lead": sample_lead_id,
            **sample_orcamento_data,
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        }]
        insert_mock.execute.return_value = execute_mock
        orcamentos_table_mock.insert.return_value = insert_mock
        
        # Configure table mock to return different tables
        def table_side_effect(table_name):
            if table_name == "leads":
                return leads_table_mock
            elif table_name == "orcamentos":
                return orcamentos_table_mock
            return Mock()
        
        client.table.side_effect = table_side_effect

        result = create_orcamento(sample_lead_id, sample_orcamento_data)

        assert result is not None
        assert result["id"] == orcamento_id
        assert result["lead"] == sample_lead_id
        assert result["produto"] == "FBM100"
        orcamentos_table_mock.insert.assert_called_once()

    @patch("src.services.orcamento_persistence.get_supabase_client")
    def test_fails_with_invalid_lead_id(self, mock_get_client, mock_supabase_client, sample_orcamento_data):
        """Test that create_orcamento fails with invalid lead_id."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        invalid_lead_id = str(uuid4())
        
        # Mock leads table - lead not found
        leads_table_mock = Mock()
        leads_select_mock = Mock()
        leads_eq_mock = Mock()
        leads_eq_mock.execute.return_value = Mock(data=[])  # No lead found
        leads_select_mock.eq.return_value = leads_eq_mock
        leads_table_mock.select.return_value = leads_select_mock
        
        def table_side_effect(table_name):
            if table_name == "leads":
                return leads_table_mock
            return Mock()
        
        client.table.side_effect = table_side_effect

        result = create_orcamento(invalid_lead_id, sample_orcamento_data)

        assert result is None

    @patch("src.services.orcamento_persistence.get_supabase_client")
    def test_returns_none_when_supabase_not_available(self, mock_get_client, sample_lead_id, sample_orcamento_data):
        """Test that None is returned when Supabase is not available."""
        mock_get_client.return_value = None

        result = create_orcamento(sample_lead_id, sample_orcamento_data)

        assert result is None

    def test_returns_none_for_empty_lead_id(self, sample_orcamento_data):
        """Test that None is returned for empty lead_id."""
        result = create_orcamento("", sample_orcamento_data)
        assert result is None

    @patch("src.services.orcamento_persistence.get_supabase_client")
    def test_handles_exception_gracefully(self, mock_get_client, mock_supabase_client, sample_lead_id, sample_orcamento_data):
        """Test that exceptions are handled gracefully."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        # Mock leads table for validation
        leads_table_mock = Mock()
        leads_select_mock = Mock()
        leads_eq_mock = Mock()
        leads_eq_mock.execute.side_effect = Exception("Database error")
        leads_select_mock.eq.return_value = leads_eq_mock
        leads_table_mock.select.return_value = leads_select_mock
        
        def table_side_effect(table_name):
            if table_name == "leads":
                return leads_table_mock
            return Mock()
        
        client.table.side_effect = table_side_effect

        result = create_orcamento(sample_lead_id, sample_orcamento_data)

        assert result is None


class TestGetOrcamentosByLead:
    """Tests for get_orcamentos_by_lead function."""

    @patch("src.services.orcamento_persistence.get_supabase_client")
    def test_returns_list_of_orcamentos(self, mock_get_client, mock_supabase_client, sample_lead_id):
        """Test that get_orcamentos_by_lead returns list of orcamentos."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        orcamento_id1 = str(uuid4())
        orcamento_id2 = str(uuid4())
        
        select_mock = Mock()
        eq_mock = Mock()
        order_mock = Mock()
        order_mock.execute.return_value = Mock(data=[
            {
                "id": orcamento_id1,
                "lead": sample_lead_id,
                "resumo": "Orçamento 1",
                "created_at": "2026-01-02T00:00:00Z",
            },
            {
                "id": orcamento_id2,
                "lead": sample_lead_id,
                "resumo": "Orçamento 2",
                "created_at": "2026-01-01T00:00:00Z",
            },
        ])

        table_mock.select.return_value = select_mock
        select_mock.eq.return_value = eq_mock
        eq_mock.order.return_value = order_mock

        result = get_orcamentos_by_lead(sample_lead_id)

        assert len(result) == 2
        assert result[0]["id"] == orcamento_id1
        assert result[1]["id"] == orcamento_id2
        select_mock.eq.assert_called_once_with("lead", sample_lead_id)
        eq_mock.order.assert_called_once_with("created_at", desc=True)

    @patch("src.services.orcamento_persistence.get_supabase_client")
    def test_returns_empty_list_when_no_orcamentos(self, mock_get_client, mock_supabase_client, sample_lead_id):
        """Test that get_orcamentos_by_lead returns empty list when no orcamentos."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        select_mock = Mock()
        eq_mock = Mock()
        order_mock = Mock()
        order_mock.execute.return_value = Mock(data=[])

        table_mock.select.return_value = select_mock
        select_mock.eq.return_value = eq_mock
        eq_mock.order.return_value = order_mock

        result = get_orcamentos_by_lead(sample_lead_id)

        assert result == []

    @patch("src.services.orcamento_persistence.get_supabase_client")
    def test_orders_by_created_at_desc(self, mock_get_client, mock_supabase_client, sample_lead_id):
        """Test that get_orcamentos_by_lead orders by created_at desc."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        select_mock = Mock()
        eq_mock = Mock()
        order_mock = Mock()
        order_mock.execute.return_value = Mock(data=[
            {"id": str(uuid4()), "created_at": "2026-01-02T00:00:00Z"},
            {"id": str(uuid4()), "created_at": "2026-01-01T00:00:00Z"},
        ])

        table_mock.select.return_value = select_mock
        select_mock.eq.return_value = eq_mock
        eq_mock.order.return_value = order_mock

        result = get_orcamentos_by_lead(sample_lead_id)

        # Verify order was called with desc=True
        eq_mock.order.assert_called_once_with("created_at", desc=True)
        # Verify most recent is first
        assert result[0]["created_at"] > result[1]["created_at"]

    @patch("src.services.orcamento_persistence.get_supabase_client")
    def test_returns_none_when_supabase_not_available(self, mock_get_client, sample_lead_id):
        """Test that empty list is returned when Supabase is not available."""
        mock_get_client.return_value = None

        result = get_orcamentos_by_lead(sample_lead_id)

        assert result == []

    def test_returns_empty_list_for_empty_lead_id(self):
        """Test that empty list is returned for empty lead_id."""
        result = get_orcamentos_by_lead("")
        assert result == []

    @patch("src.services.orcamento_persistence.get_supabase_client")
    def test_handles_exception_gracefully(self, mock_get_client, mock_supabase_client, sample_lead_id):
        """Test that exceptions are handled gracefully."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        select_mock = Mock()
        eq_mock = Mock()
        order_mock = Mock()
        order_mock.execute.side_effect = Exception("Database error")

        table_mock.select.return_value = select_mock
        select_mock.eq.return_value = eq_mock
        eq_mock.order.return_value = order_mock

        result = get_orcamentos_by_lead(sample_lead_id)

        assert result == []


class TestUpdateOrcamento:
    """Tests for update_orcamento function."""

    @patch("src.services.orcamento_persistence.get_supabase_client")
    def test_updates_specified_fields(self, mock_get_client, mock_supabase_client):
        """Test that update_orcamento updates specified fields."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        orcamento_id = str(uuid4())
        update_mock = Mock()
        eq_mock = Mock()
        execute_mock = Mock()
        execute_mock.data = [{
            "id": orcamento_id,
            "resumo": "Orçamento atualizado",
            "volume_diario": 2000,
            "updated_at": "2026-01-01T01:00:00Z",
        }]
        eq_mock.execute.return_value = execute_mock

        table_mock.update.return_value = update_mock
        update_mock.eq.return_value = eq_mock

        result = update_orcamento(orcamento_id, {
            "resumo": "Orçamento atualizado",
            "volume_diario": 2000,
        })

        assert result is not None
        assert result["resumo"] == "Orçamento atualizado"
        assert result["volume_diario"] == 2000
        table_mock.update.assert_called_once()
        update_mock.eq.assert_called_once_with("id", orcamento_id)

    @patch("src.services.orcamento_persistence.get_supabase_client")
    def test_doesnt_overwrite_fields_with_null(self, mock_get_client, mock_supabase_client):
        """Test that update_orcamento doesn't overwrite fields with null."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        orcamento_id = str(uuid4())
        update_mock = Mock()
        eq_mock = Mock()
        execute_mock = Mock()
        execute_mock.data = [{
            "id": orcamento_id,
            "resumo": "Orçamento existente",  # Preserved
            "oportunidade_pipe_id": "pipe-123",  # New field
        }]
        eq_mock.execute.return_value = execute_mock

        table_mock.update.return_value = update_mock
        update_mock.eq.return_value = eq_mock

        result = update_orcamento(orcamento_id, {
            "oportunidade_pipe_id": "pipe-123",
            "resumo": None,  # Should be filtered out
        })

        assert result is not None
        # Verify None values were filtered from payload
        call_args = table_mock.update.call_args
        payload = call_args[0][0]
        assert "oportunidade_pipe_id" in payload
        assert "resumo" not in payload or payload.get("resumo") is not None

    @patch("src.services.orcamento_persistence.get_supabase_client")
    def test_fails_with_invalid_id(self, mock_get_client, mock_supabase_client):
        """Test that update_orcamento fails with invalid id."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        invalid_id = str(uuid4())
        update_mock = Mock()
        eq_mock = Mock()
        eq_mock.execute.return_value = Mock(data=[])  # Not found

        table_mock.update.return_value = eq_mock

        result = update_orcamento(invalid_id, {"resumo": "Test"})

        assert result is None

    @patch("src.services.orcamento_persistence.get_supabase_client")
    def test_updates_updated_at_field(self, mock_get_client, mock_supabase_client):
        """Test that update_orcamento updates updated_at field."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        orcamento_id = str(uuid4())
        update_mock = Mock()
        eq_mock = Mock()
        execute_mock = Mock()
        execute_mock.data = [{
            "id": orcamento_id,
            "updated_at": "2026-01-01T01:00:00Z",
        }]
        eq_mock.execute.return_value = execute_mock

        table_mock.update.return_value = update_mock
        update_mock.eq.return_value = eq_mock

        result = update_orcamento(orcamento_id, {"resumo": "Test"})

        assert result is not None
        # Verify updated_at was added to payload
        call_args = table_mock.update.call_args
        payload = call_args[0][0]
        assert "updated_at" in payload

    @patch("src.services.orcamento_persistence.get_supabase_client")
    def test_returns_none_when_supabase_not_available(self, mock_get_client):
        """Test that None is returned when Supabase is not available."""
        mock_get_client.return_value = None

        result = update_orcamento(str(uuid4()), {"resumo": "Test"})

        assert result is None

    def test_returns_none_for_empty_id(self):
        """Test that None is returned for empty id."""
        result = update_orcamento("", {"resumo": "Test"})
        assert result is None

    @patch("src.services.orcamento_persistence.get_supabase_client")
    def test_returns_none_when_no_valid_fields(self, mock_get_client, mock_supabase_client):
        """Test that None is returned when no valid fields to update."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        result = update_orcamento(str(uuid4()), {
            "resumo": None,
            "produto": None,
        })

        assert result is None

    @patch("src.services.orcamento_persistence.get_supabase_client")
    def test_handles_exception_gracefully(self, mock_get_client, mock_supabase_client):
        """Test that exceptions are handled gracefully."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        update_mock = Mock()
        eq_mock = Mock()
        eq_mock.execute.side_effect = Exception("Database error")

        table_mock.update.return_value = eq_mock

        result = update_orcamento(str(uuid4()), {"resumo": "Test"})

        assert result is None


class TestOrcamentoErrorHandling:
    """Tests for error handling in orcamento operations."""

    @patch("src.services.orcamento_persistence.get_supabase_client")
    def test_foreign_key_constraint_violations_handled(self, mock_get_client, mock_supabase_client, sample_lead_id, sample_orcamento_data):
        """Test that foreign key constraint violations are handled."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        # Mock leads table - lead exists
        leads_table_mock = Mock()
        leads_select_mock = Mock()
        leads_eq_mock = Mock()
        leads_eq_mock.execute.return_value = Mock(data=[{"id": sample_lead_id}])
        leads_select_mock.eq.return_value = leads_eq_mock
        leads_table_mock.select.return_value = leads_select_mock
        
        # Mock orcamentos table - foreign key violation
        orcamentos_table_mock = Mock()
        insert_mock = Mock()
        insert_mock.execute.side_effect = Exception("Foreign key constraint violation")

        def table_side_effect(table_name):
            if table_name == "leads":
                return leads_table_mock
            elif table_name == "orcamentos":
                return orcamentos_table_mock
            return Mock()
        
        client.table.side_effect = table_side_effect
        orcamentos_table_mock.insert.return_value = insert_mock

        result = create_orcamento(sample_lead_id, sample_orcamento_data)

        assert result is None

    @patch("src.services.orcamento_persistence.get_supabase_client")
    def test_database_connection_errors_handled(self, mock_get_client):
        """Test that database connection errors are handled."""
        mock_get_client.side_effect = Exception("Connection error")

        result = create_orcamento(str(uuid4()), {"resumo": "Test"})
        assert result is None

        result = get_orcamentos_by_lead(str(uuid4()))
        assert result == []

        result = update_orcamento(str(uuid4()), {"resumo": "Test"})
        assert result is None


class TestOrcamentoIntegration:
    """Integration tests for orcamento CRUD operations."""

    @pytest.mark.integration
    @patch("src.services.orcamento_persistence.get_supabase_client")
    def test_end_to_end_orcamento_operations(self, mock_get_client, mock_supabase_client, sample_lead_id):
        """Test end-to-end: create lead, create orcamento, retrieve, update."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        orcamento_id = str(uuid4())
        test_data = {
            "resumo": "Orçamento para FBM100",
            "produto": "FBM100",
            "segmento": "Alimentício",
            "urgencia_compra": "Alta",
            "volume_diario": 1000,
        }

        # Mock leads table for validation
        leads_table_mock = Mock()
        leads_select_mock = Mock()
        leads_eq_mock = Mock()
        leads_eq_mock.execute.return_value = Mock(data=[{"id": sample_lead_id}])
        leads_select_mock.eq.return_value = leads_eq_mock
        leads_table_mock.select.return_value = leads_select_mock

        # Mock orcamentos table for create
        orcamentos_table_mock = Mock()
        insert_mock = Mock()
        execute_insert_mock = Mock()
        execute_insert_mock.data = [{
            "id": orcamento_id,
            "lead": sample_lead_id,
            **test_data,
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        }]
        insert_mock.execute.return_value = execute_insert_mock
        orcamentos_table_mock.insert.return_value = insert_mock

        # Mock orcamentos table for get
        select_mock = Mock()
        eq_mock = Mock()
        order_mock = Mock()
        order_mock.execute.return_value = Mock(data=[{
            "id": orcamento_id,
            "lead": sample_lead_id,
            **test_data,
        }])
        orcamentos_table_mock.select.return_value = select_mock
        select_mock.eq.return_value = eq_mock
        eq_mock.order.return_value = order_mock

        # Mock orcamentos table for update
        update_mock = Mock()
        eq_update_mock = Mock()
        execute_update_mock = Mock()
        execute_update_mock.data = [{
            "id": orcamento_id,
            "lead": sample_lead_id,
            "resumo": "Orçamento atualizado",
            "oportunidade_pipe_id": "pipe-123",
            **{k: v for k, v in test_data.items() if k != "resumo"},
        }]
        eq_update_mock.execute.return_value = execute_update_mock
        orcamentos_table_mock.update.return_value = update_mock
        update_mock.eq.return_value = eq_update_mock

        def table_side_effect(table_name):
            if table_name == "leads":
                return leads_table_mock
            elif table_name == "orcamentos":
                return orcamentos_table_mock
            return Mock()

        client.table.side_effect = table_side_effect

        # 1. Create orcamento
        created_orcamento = create_orcamento(sample_lead_id, test_data)
        assert created_orcamento is not None
        assert created_orcamento["id"] == orcamento_id
        assert created_orcamento["produto"] == "FBM100"

        # 2. Retrieve orcamentos
        orcamentos = get_orcamentos_by_lead(sample_lead_id)
        assert len(orcamentos) == 1
        assert orcamentos[0]["id"] == orcamento_id

        # 3. Update orcamento
        updated_orcamento = update_orcamento(orcamento_id, {
            "resumo": "Orçamento atualizado",
            "oportunidade_pipe_id": "pipe-123",
        })
        assert updated_orcamento is not None
        assert updated_orcamento["resumo"] == "Orçamento atualizado"
        assert updated_orcamento["oportunidade_pipe_id"] == "pipe-123"

    @pytest.mark.integration
    @patch("src.services.orcamento_persistence.get_supabase_client")
    def test_multiple_orcamentos_per_lead(self, mock_get_client, mock_supabase_client, sample_lead_id):
        """Test that multiple orcamentos per lead are returned correctly."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        orcamento_id1 = str(uuid4())
        orcamento_id2 = str(uuid4())

        # Mock leads table
        leads_table_mock = Mock()
        leads_select_mock = Mock()
        leads_eq_mock = Mock()
        leads_eq_mock.execute.return_value = Mock(data=[{"id": sample_lead_id}])
        leads_select_mock.eq.return_value = leads_eq_mock
        leads_table_mock.select.return_value = leads_select_mock

        # Mock orcamentos table for creates
        orcamentos_table_mock = Mock()
        insert_mock = Mock()
        execute_mock = Mock()
        execute_mock.data = [{"id": orcamento_id1, "lead": sample_lead_id}]
        insert_mock.execute.return_value = execute_mock
        orcamentos_table_mock.insert.return_value = insert_mock

        # Mock orcamentos table for get
        select_mock = Mock()
        eq_mock = Mock()
        order_mock = Mock()
        order_mock.execute.return_value = Mock(data=[
            {"id": orcamento_id1, "lead": sample_lead_id, "created_at": "2026-01-02T00:00:00Z"},
            {"id": orcamento_id2, "lead": sample_lead_id, "created_at": "2026-01-01T00:00:00Z"},
        ])
        orcamentos_table_mock.select.return_value = select_mock
        select_mock.eq.return_value = eq_mock
        eq_mock.order.return_value = order_mock

        def table_side_effect(table_name):
            if table_name == "leads":
                return leads_table_mock
            elif table_name == "orcamentos":
                return orcamentos_table_mock
            return Mock()

        client.table.side_effect = table_side_effect

        # Create first orcamento
        create_orcamento(sample_lead_id, {"resumo": "Orçamento 1"})

        # Create second orcamento
        execute_mock.data = [{"id": orcamento_id2, "lead": sample_lead_id}]
        create_orcamento(sample_lead_id, {"resumo": "Orçamento 2"})

        # Get all orcamentos
        orcamentos = get_orcamentos_by_lead(sample_lead_id)
        assert len(orcamentos) == 2
        # Verify ordering (most recent first)
        assert orcamentos[0]["id"] == orcamento_id1
        assert orcamentos[1]["id"] == orcamento_id2

