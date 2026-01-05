"""
Tests for Chatwoot synchronization service.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import asyncio

from src.services.chatwoot_sync import (
    create_chatwoot_conversation,
    sync_message_to_chatwoot,
    get_chatwoot_conversation_id,
    _get_or_create_chatwoot_contact,
)
from src.config.settings import settings


@pytest.fixture
def reset_conversation_cache():
    """Reset conversation cache."""
    import src.services.chatwoot_sync as sync_module
    sync_module._conversation_cache.clear()
    yield
    sync_module._conversation_cache.clear()


class TestCreateChatwootConversation:
    """Tests for create_chatwoot_conversation."""

    def test_returns_none_for_invalid_phone(self):
        """Test that None is returned for invalid phone number."""
        result = asyncio.run(create_chatwoot_conversation(""))
        assert result is None

    @patch("src.services.chatwoot_sync.httpx.AsyncClient")
    @patch("src.services.chatwoot_sync._get_or_create_chatwoot_contact")
    def test_creates_conversation_successfully(
        self, mock_get_contact, mock_client_class, reset_conversation_cache
    ):
        """Test that conversation is created successfully."""
        mock_get_contact.return_value = 123

        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        # Mock list conversations (empty paginated response)
        mock_client.get.return_value = Mock(
            status_code=200,
            json=lambda: {"data": [], "meta": {"count": 0, "current_page": 1}},
        )

        # Mock create conversation
        mock_client.post.return_value = Mock(
            status_code=201, json=lambda: {"id": 456}
        )

        with patch.object(settings, "CHATWOOT_API_URL", "https://test.chatwoot.com"):
            with patch.object(settings, "CHATWOOT_API_TOKEN", "test-token"):
                with patch.object(settings, "CHATWOOT_ACCOUNT_ID", 1):
                    result = asyncio.run(create_chatwoot_conversation("5511999999999"))
                    assert result == "456"

    @patch("src.services.chatwoot_sync.httpx.AsyncClient")
    @patch("src.services.chatwoot_sync._get_or_create_chatwoot_contact")
    def test_uses_existing_conversation_paginated(
        self, mock_get_contact, mock_client_class, reset_conversation_cache
    ):
        """Test that existing conversation is used when API returns paginated response."""
        mock_get_contact.return_value = 123

        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        # Mock list conversations (paginated response with data key)
        mock_client.get.return_value = Mock(
            status_code=200,
            json=lambda: {
                "data": [{"id": 789}],
                "meta": {"count": 1, "current_page": 1},
            },
        )

        with patch.object(settings, "CHATWOOT_API_URL", "https://test.chatwoot.com"):
            with patch.object(settings, "CHATWOOT_API_TOKEN", "test-token"):
                with patch.object(settings, "CHATWOOT_ACCOUNT_ID", 1):
                    result = asyncio.run(create_chatwoot_conversation("5511999999999"))
                    assert result == "789"

    @patch("src.services.chatwoot_sync.httpx.AsyncClient")
    @patch("src.services.chatwoot_sync._get_or_create_chatwoot_contact")
    def test_uses_existing_conversation_list_format(
        self, mock_get_contact, mock_client_class, reset_conversation_cache
    ):
        """Test backward compatibility: existing conversation with list format."""
        mock_get_contact.return_value = 123

        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        # Mock list conversations (legacy list format)
        mock_client.get.return_value = Mock(
            status_code=200, json=lambda: [{"id": 789}]
        )

        with patch.object(settings, "CHATWOOT_API_URL", "https://test.chatwoot.com"):
            with patch.object(settings, "CHATWOOT_API_TOKEN", "test-token"):
                with patch.object(settings, "CHATWOOT_ACCOUNT_ID", 1):
                    result = asyncio.run(create_chatwoot_conversation("5511999999999"))
                    assert result == "789"

    def test_returns_none_when_chatwoot_not_configured(self):
        """Test that None is returned when Chatwoot is not configured."""
        with patch.object(settings, "CHATWOOT_API_URL", None):
            result = asyncio.run(create_chatwoot_conversation("5511999999999"))
            assert result is None


class TestSyncMessageToChatwoot:
    """Tests for sync_message_to_chatwoot."""

    def test_returns_false_for_invalid_phone(self):
        """Test that False is returned for invalid phone number."""
        result = sync_message_to_chatwoot("", "user", "test")
        assert result is False

    @patch("src.services.chatwoot_sync.threading.Thread")
    def test_schedules_sync_successfully(self, mock_thread_class):
        """Test that sync is scheduled successfully."""
        mock_thread = Mock()
        mock_thread_class.return_value = mock_thread

        with patch.object(settings, "CHATWOOT_API_URL", "https://test.chatwoot.com"):
            with patch.object(settings, "CHATWOOT_API_TOKEN", "test-token"):
                with patch.object(settings, "CHATWOOT_ACCOUNT_ID", 1):
                    result = sync_message_to_chatwoot("5511999999999", "user", "test")
                    assert result is True
                    # Verify thread was created and started
                    mock_thread_class.assert_called_once()
                    mock_thread.start.assert_called_once()

    def test_returns_false_when_chatwoot_not_configured(self):
        """Test that False is returned when Chatwoot is not configured."""
        with patch.object(settings, "CHATWOOT_API_URL", None):
            result = sync_message_to_chatwoot("5511999999999", "user", "test")
            assert result is False


class TestGetChatwootConversationId:
    """Tests for get_chatwoot_conversation_id."""

    def test_returns_none_for_invalid_phone(self):
        """Test that None is returned for invalid phone number."""
        result = get_chatwoot_conversation_id("")
        assert result is None

    def test_returns_cached_id(self, reset_conversation_cache):
        """Test that cached conversation ID is returned."""
        import src.services.chatwoot_sync as sync_module
        sync_module._conversation_cache["5511999999999"] = "cached-id"

        result = get_chatwoot_conversation_id("5511999999999")
        assert result == "cached-id"

    def test_returns_none_when_not_cached(self, reset_conversation_cache):
        """Test that None is returned when not cached."""
        result = get_chatwoot_conversation_id("5511999999999")
        assert result is None


class TestGetOrCreateChatwootContact:
    """Tests for _get_or_create_chatwoot_contact with paginated responses."""

    @patch("src.services.chatwoot_sync.httpx.AsyncClient")
    def test_finds_contact_with_paginated_response(self, mock_client_class):
        """Test that contact is found when API returns paginated response."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        # Mock search contacts (paginated response with payload key)
        mock_client.get.return_value = Mock(
            status_code=200,
            json=lambda: {
                "payload": [{"id": 123, "name": "Test Contact", "phone_number": "+5511999999999"}],
                "meta": {"count": 1, "current_page": 1},
            },
        )

        with patch.object(settings, "CHATWOOT_API_URL", "https://test.chatwoot.com"):
            with patch.object(settings, "CHATWOOT_API_TOKEN", "test-token"):
                with patch.object(settings, "CHATWOOT_ACCOUNT_ID", 1):
                    result = asyncio.run(_get_or_create_chatwoot_contact("5511999999999"))
                    assert result == 123
                    # Verify that post was NOT called (contact already exists)
                    mock_client.post.assert_not_called()

    @patch("src.services.chatwoot_sync.httpx.AsyncClient")
    def test_finds_contact_with_list_response(self, mock_client_class):
        """Test backward compatibility: contact found with list response."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        # Mock search contacts (legacy list format)
        mock_client.get.return_value = Mock(
            status_code=200,
            json=lambda: [{"id": 456, "name": "Test Contact"}],
        )

        with patch.object(settings, "CHATWOOT_API_URL", "https://test.chatwoot.com"):
            with patch.object(settings, "CHATWOOT_API_TOKEN", "test-token"):
                with patch.object(settings, "CHATWOOT_ACCOUNT_ID", 1):
                    result = asyncio.run(_get_or_create_chatwoot_contact("5511999999999"))
                    assert result == 456

    @patch("src.services.chatwoot_sync.httpx.AsyncClient")
    def test_creates_contact_when_paginated_response_empty(self, mock_client_class):
        """Test that contact is created when paginated response has empty payload."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        # Mock search contacts (empty paginated response)
        mock_client.get.return_value = Mock(
            status_code=200,
            json=lambda: {"payload": [], "meta": {"count": 0, "current_page": 1}},
        )

        # Mock create contact
        mock_client.post.return_value = Mock(
            status_code=201, json=lambda: {"id": 789}
        )

        with patch.object(settings, "CHATWOOT_API_URL", "https://test.chatwoot.com"):
            with patch.object(settings, "CHATWOOT_API_TOKEN", "test-token"):
                with patch.object(settings, "CHATWOOT_ACCOUNT_ID", 1):
                    result = asyncio.run(_get_or_create_chatwoot_contact("5511999999999"))
                    assert result == 789
                    mock_client.post.assert_called_once()

    @patch("src.services.chatwoot_sync.httpx.AsyncClient")
    def test_creates_contact_when_list_response_empty(self, mock_client_class):
        """Test that contact is created when list response is empty."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        # Mock search contacts (empty list)
        mock_client.get.return_value = Mock(status_code=200, json=lambda: [])

        # Mock create contact
        mock_client.post.return_value = Mock(
            status_code=201, json=lambda: {"id": 999}
        )

        with patch.object(settings, "CHATWOOT_API_URL", "https://test.chatwoot.com"):
            with patch.object(settings, "CHATWOOT_API_TOKEN", "test-token"):
                with patch.object(settings, "CHATWOOT_ACCOUNT_ID", 1):
                    result = asyncio.run(_get_or_create_chatwoot_contact("5511999999999"))
                    assert result == 999

    @patch("src.services.chatwoot_sync.httpx.AsyncClient")
    def test_handles_unexpected_response_format(self, mock_client_class):
        """Test that unexpected response format is handled gracefully."""
        mock_client = AsyncMock()
        mock_client_class.return_value.__aenter__.return_value = mock_client

        # Mock search contacts (unexpected format - string)
        mock_client.get.return_value = Mock(status_code=200, json=lambda: "unexpected")

        # Mock create contact (should be called since search returns unexpected format)
        mock_client.post.return_value = Mock(
            status_code=201, json=lambda: {"id": 111}
        )

        with patch.object(settings, "CHATWOOT_API_URL", "https://test.chatwoot.com"):
            with patch.object(settings, "CHATWOOT_API_TOKEN", "test-token"):
                with patch.object(settings, "CHATWOOT_ACCOUNT_ID", 1):
                    result = asyncio.run(_get_or_create_chatwoot_contact("5511999999999"))
                    assert result == 111
                    mock_client.post.assert_called_once()

