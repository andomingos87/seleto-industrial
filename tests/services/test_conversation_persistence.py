"""
Tests for conversation persistence service.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.services.conversation_persistence import (
    get_supabase_client,
    save_message_to_supabase,
    get_messages_from_supabase,
    save_context_to_supabase,
    get_context_from_supabase,
)
from src.config.settings import settings


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client."""
    client = Mock()
    table_mock = Mock()
    client.table.return_value = table_mock
    return client, table_mock


@pytest.fixture
def reset_supabase_client():
    """Reset Supabase client singleton."""
    import src.services.conversation_persistence as persistence_module
    persistence_module._supabase_client = None
    yield
    persistence_module._supabase_client = None


class TestGetSupabaseClient:
    """Tests for get_supabase_client."""

    def test_returns_none_when_not_configured(self, reset_supabase_client):
        """Test that None is returned when Supabase is not configured."""
        with patch.object(settings, "SUPABASE_URL", None):
            with patch.object(settings, "SUPABASE_SERVICE_ROLE_KEY", None):
                client = get_supabase_client()
                assert client is None

    @patch("src.services.conversation_persistence.create_client")
    def test_creates_client_when_configured(self, mock_create_client, reset_supabase_client):
        """Test that client is created when Supabase is configured."""
        mock_client = Mock()
        mock_create_client.return_value = mock_client

        with patch.object(settings, "SUPABASE_URL", "https://test.supabase.co"):
            with patch.object(settings, "SUPABASE_SERVICE_ROLE_KEY", "test-key"):
                client = get_supabase_client()
                assert client is not None
                mock_create_client.assert_called_once()

    @patch("src.services.conversation_persistence.create_client")
    def test_returns_cached_client(self, mock_create_client, reset_supabase_client):
        """Test that cached client is returned on subsequent calls."""
        mock_client = Mock()
        mock_create_client.return_value = mock_client

        with patch.object(settings, "SUPABASE_URL", "https://test.supabase.co"):
            with patch.object(settings, "SUPABASE_SERVICE_ROLE_KEY", "test-key"):
                client1 = get_supabase_client()
                client2 = get_supabase_client()
                assert client1 is client2
                assert mock_create_client.call_count == 1


class TestSaveMessageToSupabase:
    """Tests for save_message_to_supabase."""

    def test_returns_false_for_invalid_phone(self):
        """Test that False is returned for invalid phone number."""
        result = save_message_to_supabase("", "user", "test")
        assert result is False

    def test_returns_false_for_invalid_role(self):
        """Test that False is returned for invalid role."""
        result = save_message_to_supabase("5511999999999", "invalid", "test")
        assert result is False

    @patch("src.services.conversation_persistence.get_supabase_client")
    def test_saves_message_successfully(self, mock_get_client, mock_supabase_client):
        """Test that message is saved successfully."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        insert_mock = Mock()
        insert_mock.execute.return_value = Mock(data=[{"id": "test-id"}])
        table_mock.insert.return_value = insert_mock

        result = save_message_to_supabase("5511999999999", "user", "test message")
        assert result is True
        table_mock.insert.assert_called_once()
        insert_mock.execute.assert_called_once()

    @patch("src.services.conversation_persistence.get_supabase_client")
    def test_returns_false_when_supabase_not_available(self, mock_get_client):
        """Test that False is returned when Supabase is not available."""
        mock_get_client.return_value = None

        result = save_message_to_supabase("5511999999999", "user", "test message")
        assert result is False

    @patch("src.services.conversation_persistence.get_supabase_client")
    def test_handles_exception_gracefully(self, mock_get_client, mock_supabase_client):
        """Test that exceptions are handled gracefully."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        insert_mock = Mock()
        insert_mock.execute.side_effect = Exception("Database error")
        table_mock.insert.return_value = insert_mock

        result = save_message_to_supabase("5511999999999", "user", "test message")
        assert result is False


class TestGetMessagesFromSupabase:
    """Tests for get_messages_from_supabase."""

    def test_returns_empty_list_for_invalid_phone(self):
        """Test that empty list is returned for invalid phone number."""
        result = get_messages_from_supabase("")
        assert result == []

    @patch("src.services.conversation_persistence.get_supabase_client")
    def test_retrieves_messages_successfully(self, mock_get_client, mock_supabase_client):
        """Test that messages are retrieved successfully."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        select_mock = Mock()
        eq_mock = Mock()
        order_mock = Mock()
        order_mock.execute.return_value = Mock(
            data=[
                {"role": "user", "content": "Hello", "timestamp": "2024-01-01T00:00:00Z"},
                {"role": "assistant", "content": "Hi", "timestamp": "2024-01-01T00:01:00Z"},
            ]
        )

        table_mock.select.return_value = select_mock
        select_mock.eq.return_value = eq_mock
        eq_mock.order.return_value = order_mock

        result = get_messages_from_supabase("5511999999999")
        assert len(result) == 2
        assert result[0]["role"] == "user"
        assert result[1]["role"] == "assistant"

    @patch("src.services.conversation_persistence.get_supabase_client")
    def test_applies_max_messages_limit(self, mock_get_client, mock_supabase_client):
        """Test that max_messages limit is applied."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        select_mock = Mock()
        eq_mock = Mock()
        order_mock = Mock()
        limit_mock = Mock()
        limit_mock.execute.return_value = Mock(
            data=[{"role": "user", "content": "Hello", "timestamp": "2024-01-01T00:00:00Z"}]
        )

        table_mock.select.return_value = select_mock
        select_mock.eq.return_value = eq_mock
        eq_mock.order.return_value = order_mock
        order_mock.limit.return_value = limit_mock

        result = get_messages_from_supabase("5511999999999", max_messages=1)
        assert len(result) == 1
        order_mock.limit.assert_called_once_with(1)

    @patch("src.services.conversation_persistence.get_supabase_client")
    def test_returns_empty_list_when_supabase_not_available(self, mock_get_client):
        """Test that empty list is returned when Supabase is not available."""
        mock_get_client.return_value = None

        result = get_messages_from_supabase("5511999999999")
        assert result == []


class TestSaveContextToSupabase:
    """Tests for save_context_to_supabase."""

    def test_returns_false_for_invalid_phone(self):
        """Test that False is returned for invalid phone number."""
        result = save_context_to_supabase("", {"name": "Test"})
        assert result is False

    @patch("src.services.conversation_persistence.get_supabase_client")
    def test_saves_context_successfully(self, mock_get_client, mock_supabase_client):
        """Test that context is saved successfully."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        upsert_mock = Mock()
        upsert_mock.execute.return_value = Mock(data=[{"lead_phone": "5511999999999"}])
        table_mock.upsert.return_value = upsert_mock

        context = {"name": "Test", "city": "São Paulo"}
        result = save_context_to_supabase("5511999999999", context)
        assert result is True
        table_mock.upsert.assert_called_once()

    @patch("src.services.conversation_persistence.get_supabase_client")
    def test_returns_false_when_supabase_not_available(self, mock_get_client):
        """Test that False is returned when Supabase is not available."""
        mock_get_client.return_value = None

        result = save_context_to_supabase("5511999999999", {"name": "Test"})
        assert result is False


class TestGetContextFromSupabase:
    """Tests for get_context_from_supabase."""

    def test_returns_empty_dict_for_invalid_phone(self):
        """Test that empty dict is returned for invalid phone number."""
        result = get_context_from_supabase("")
        assert result == {}

    @patch("src.services.conversation_persistence.get_supabase_client")
    def test_retrieves_context_successfully(self, mock_get_client, mock_supabase_client):
        """Test that context is retrieved successfully."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        select_mock = Mock()
        eq_mock = Mock()
        eq_mock.execute.return_value = Mock(
            data=[{"context_data": {"name": "Test", "city": "São Paulo"}}]
        )

        table_mock.select.return_value = select_mock
        select_mock.eq.return_value = eq_mock

        result = get_context_from_supabase("5511999999999")
        assert result == {"name": "Test", "city": "São Paulo"}

    @patch("src.services.conversation_persistence.get_supabase_client")
    def test_returns_empty_dict_when_not_found(self, mock_get_client, mock_supabase_client):
        """Test that empty dict is returned when context is not found."""
        client, table_mock = mock_supabase_client
        mock_get_client.return_value = client

        select_mock = Mock()
        eq_mock = Mock()
        eq_mock.execute.return_value = Mock(data=[])

        table_mock.select.return_value = select_mock
        select_mock.eq.return_value = eq_mock

        result = get_context_from_supabase("5511999999999")
        assert result == {}

    @patch("src.services.conversation_persistence.get_supabase_client")
    def test_returns_empty_dict_when_supabase_not_available(self, mock_get_client):
        """Test that empty dict is returned when Supabase is not available."""
        mock_get_client.return_value = None

        result = get_context_from_supabase("5511999999999")
        assert result == {}

