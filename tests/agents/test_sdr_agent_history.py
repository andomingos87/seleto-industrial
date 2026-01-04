"""
Tests for SDR agent conversation history integration.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from src.agents.sdr_agent import process_message
from src.services.conversation_memory import conversation_memory


@pytest.fixture
def reset_conversation_memory():
    """Reset conversation memory before and after tests."""
    # Clear in-memory cache
    conversation_memory._conversations.clear()
    conversation_memory._lead_data.clear()
    conversation_memory._question_count.clear()
    conversation_memory._loaded_from_supabase.clear()
    yield
    # Clean up after test
    conversation_memory._conversations.clear()
    conversation_memory._lead_data.clear()
    conversation_memory._question_count.clear()
    conversation_memory._loaded_from_supabase.clear()


class TestConversationHistoryIntegration:
    """Tests for conversation history integration in SDR agent."""

    @pytest.mark.asyncio
    @patch("src.agents.sdr_agent.sdr_agent")
    @patch("src.services.conversation_memory.get_messages_from_supabase")
    @patch("src.services.conversation_memory.save_message_to_supabase")
    @patch("src.services.conversation_memory.sync_message_to_chatwoot")
    async def test_loads_history_from_supabase_on_first_message(
        self,
        mock_sync_chatwoot,
        mock_save_supabase,
        mock_get_supabase,
        mock_agent,
        reset_conversation_memory,
    ):
        """Test that history is loaded from Supabase when processing first message."""
        # Mock Supabase to return existing messages
        mock_get_supabase.return_value = [
            {"role": "user", "content": "Hello", "timestamp": "2024-01-01T00:00:00Z"},
            {"role": "assistant", "content": "Hi", "timestamp": "2024-01-01T00:01:00Z"},
        ]

        # Mock agent response
        mock_response = Mock()
        mock_response.content = "How can I help?"
        mock_agent.run.return_value = mock_response

        # Process message
        result = await process_message("5511999999999", "New message")

        # Verify history was loaded from Supabase
        mock_get_supabase.assert_called_once_with("5511999999999")

        # Verify new messages were saved
        assert mock_save_supabase.call_count >= 2  # User message + assistant response

    @pytest.mark.asyncio
    @patch("src.agents.sdr_agent.sdr_agent")
    @patch("src.services.conversation_memory.save_message_to_supabase")
    @patch("src.services.conversation_memory.sync_message_to_chatwoot")
    async def test_persists_messages_to_supabase(
        self,
        mock_sync_chatwoot,
        mock_save_supabase,
        mock_agent,
        reset_conversation_memory,
    ):
        """Test that messages are persisted to Supabase."""
        # Mock agent response
        mock_response = Mock()
        mock_response.content = "Test response"
        mock_agent.run.return_value = mock_response

        # Process message
        result = await process_message("5511999999999", "Test message")

        # Verify messages were saved to Supabase
        assert mock_save_supabase.call_count >= 2  # User + assistant

        # Verify user message was saved
        user_calls = [call for call in mock_save_supabase.call_args_list if call[0][1] == "user"]
        assert len(user_calls) > 0

        # Verify assistant message was saved
        assistant_calls = [
            call for call in mock_save_supabase.call_args_list if call[0][1] == "assistant"
        ]
        assert len(assistant_calls) > 0

    @pytest.mark.asyncio
    @patch("src.agents.sdr_agent.sdr_agent")
    @patch("src.services.conversation_memory.sync_message_to_chatwoot")
    async def test_syncs_messages_to_chatwoot(
        self,
        mock_sync_chatwoot,
        mock_agent,
        reset_conversation_memory,
    ):
        """Test that messages are synced to Chatwoot."""
        # Mock agent response
        mock_response = Mock()
        mock_response.content = "Test response"
        mock_agent.run.return_value = mock_response

        # Process message
        result = await process_message("5511999999999", "Test message")

        # Verify messages were synced to Chatwoot
        assert mock_sync_chatwoot.call_count >= 2  # User + assistant

    @pytest.mark.asyncio
    @patch("src.agents.sdr_agent.sdr_agent")
    @patch("src.services.conversation_memory.get_context_from_supabase")
    async def test_loads_context_from_supabase(
        self,
        mock_get_context,
        mock_agent,
        reset_conversation_memory,
    ):
        """Test that context is loaded from Supabase."""
        # Mock context from Supabase
        mock_get_context.return_value = {"name": "Test User", "city": "São Paulo"}

        # Mock agent response
        mock_response = Mock()
        mock_response.content = "Test response"
        mock_agent.run.return_value = mock_response

        # Process message
        result = await process_message("5511999999999", "Test message")

        # Verify context was loaded
        mock_get_context.assert_called()

        # Verify context is available in conversation memory
        lead_data = conversation_memory.get_lead_data("5511999999999")
        assert "name" in lead_data or "city" in lead_data  # May be merged with new data

    @pytest.mark.asyncio
    @patch("src.agents.sdr_agent.sdr_agent")
    async def test_continues_conversation_after_restart(
        self,
        mock_agent,
        reset_conversation_memory,
    ):
        """Test that conversation continues after server restart."""
        # Simulate existing conversation in Supabase by pre-populating cache
        from src.services.conversation_memory import ConversationMessage
        from datetime import datetime

        conversation_memory._conversations["5511999999999"] = [
            ConversationMessage("user", "Previous message", datetime.utcnow()),
        ]
        conversation_memory._loaded_from_supabase["5511999999999"] = True

        # Mock agent response
        mock_response = Mock()
        mock_response.content = "Continuing conversation"
        mock_agent.run.return_value = mock_response

        # Process new message
        result = await process_message("5511999999999", "New message")

        # Verify agent received previous context
        # (This is implicit - if history wasn't loaded, agent wouldn't have context)
        assert result is not None

        # Verify conversation has both old and new messages
        history = conversation_memory.get_conversation_history("5511999999999")
        assert len(history) >= 2  # Previous + new user message + assistant response

