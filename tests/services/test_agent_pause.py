"""
Tests for agent pause/resume service.

This module tests the agent pause functionality including:
- Pausing and resuming the agent
- Auto-resume logic based on business hours
- Command detection (/retomar, /continuar)
- State persistence and cache management
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock

from src.services.agent_pause import (
    is_agent_paused,
    get_pause_info,
    pause_agent,
    resume_agent,
    check_auto_resume,
    try_auto_resume,
    is_resume_command,
    process_sdr_command,
    clear_cache,
    load_pause_states_from_supabase,
    RESUME_COMMANDS,
    _pause_cache,
)


@pytest.fixture
def reset_cache():
    """Reset the pause cache before and after each test."""
    clear_cache()
    yield
    clear_cache()


@pytest.fixture
def mock_supabase():
    """Mock Supabase context functions."""
    with patch("src.services.agent_pause.get_context_from_supabase") as mock_get, \
         patch("src.services.agent_pause.save_context_to_supabase") as mock_save, \
         patch("src.services.agent_pause.get_supabase_client") as mock_client:
        mock_get.return_value = {}
        mock_save.return_value = True
        mock_client.return_value = MagicMock()
        yield {"get": mock_get, "save": mock_save, "client": mock_client}


class TestIsAgentPaused:
    """Tests for is_agent_paused function."""

    def test_returns_false_when_not_paused(self, reset_cache, mock_supabase):
        """Test that False is returned when agent is not paused."""
        mock_supabase["get"].return_value = {}

        result = is_agent_paused("5511999999999")

        assert result is False

    def test_returns_true_when_paused(self, reset_cache, mock_supabase):
        """Test that True is returned when agent is paused."""
        mock_supabase["get"].return_value = {
            "agent_pause_state": {"paused": True}
        }

        result = is_agent_paused("5511999999999")

        assert result is True

    def test_uses_cache_on_subsequent_calls(self, reset_cache, mock_supabase):
        """Test that cache is used on subsequent calls."""
        mock_supabase["get"].return_value = {"agent_pause_state": {"paused": True}}

        # First call should hit Supabase
        is_agent_paused("5511999999999")
        # Second call should use cache
        is_agent_paused("5511999999999")

        # Should only be called once due to caching
        assert mock_supabase["get"].call_count == 1

    def test_handles_invalid_phone(self, reset_cache, mock_supabase):
        """Test that invalid phone returns False."""
        result = is_agent_paused("")

        assert result is False


class TestPauseAgent:
    """Tests for pause_agent function."""

    def test_pauses_agent_successfully(self, reset_cache, mock_supabase):
        """Test that agent is paused successfully."""
        with patch("src.services.agent_pause.is_business_hours", return_value=True):
            result = pause_agent("5511999999999", reason="sdr_intervention")

        assert result is True
        assert mock_supabase["save"].called

    def test_sets_pause_state_correctly(self, reset_cache, mock_supabase):
        """Test that pause state is set correctly."""
        with patch("src.services.agent_pause.is_business_hours", return_value=True):
            pause_agent(
                "5511999999999",
                reason="sdr_intervention",
                sender_name="John",
                sender_id="123",
            )

        # Check that the saved context contains pause state
        saved_context = mock_supabase["save"].call_args[0][1]
        pause_state = saved_context.get("agent_pause_state", {})

        assert pause_state.get("paused") is True
        assert pause_state.get("reason") == "sdr_intervention"
        assert pause_state.get("sender_name") == "John"
        assert pause_state.get("sender_id") == "123"

    def test_handles_save_failure(self, reset_cache, mock_supabase):
        """Test handling of Supabase save failure."""
        mock_supabase["save"].return_value = False

        with patch("src.services.agent_pause.is_business_hours", return_value=True):
            result = pause_agent("5511999999999")

        assert result is False


class TestResumeAgent:
    """Tests for resume_agent function."""

    def test_resumes_agent_successfully(self, reset_cache, mock_supabase):
        """Test that agent is resumed successfully."""
        with patch("src.services.agent_pause.is_business_hours", return_value=True):
            result = resume_agent("5511999999999", reason="sdr_command")

        assert result is True

    def test_sets_resume_state_correctly(self, reset_cache, mock_supabase):
        """Test that resume state is set correctly."""
        with patch("src.services.agent_pause.is_business_hours", return_value=True):
            resume_agent(
                "5511999999999",
                reason="sdr_command",
                resumed_by="SDR John",
            )

        saved_context = mock_supabase["save"].call_args[0][1]
        pause_state = saved_context.get("agent_pause_state", {})

        assert pause_state.get("paused") is False
        assert pause_state.get("resume_reason") == "sdr_command"
        assert pause_state.get("resumed_by") == "SDR John"


class TestCheckAutoResume:
    """Tests for check_auto_resume function."""

    def test_returns_false_when_not_paused(self, reset_cache, mock_supabase):
        """Test that auto-resume check returns False when not paused."""
        mock_supabase["get"].return_value = {}

        should_resume, reason = check_auto_resume("5511999999999")

        assert should_resume is False
        assert reason is None

    def test_returns_true_outside_business_hours(self, reset_cache, mock_supabase):
        """Test that auto-resume is triggered outside business hours."""
        mock_supabase["get"].return_value = {"agent_pause_state": {"paused": True}}

        with patch("src.services.agent_pause.should_auto_resume", return_value=True):
            should_resume, reason = check_auto_resume("5511999999999")

        assert should_resume is True
        assert reason == "outside_business_hours"

    def test_returns_false_within_business_hours(self, reset_cache, mock_supabase):
        """Test that auto-resume is blocked within business hours."""
        mock_supabase["get"].return_value = {"agent_pause_state": {"paused": True}}

        with patch("src.services.agent_pause.should_auto_resume", return_value=False):
            should_resume, reason = check_auto_resume("5511999999999")

        assert should_resume is False
        assert reason == "within_business_hours"


class TestTryAutoResume:
    """Tests for try_auto_resume function."""

    def test_auto_resumes_outside_business_hours(self, reset_cache, mock_supabase):
        """Test that agent is auto-resumed outside business hours."""
        mock_supabase["get"].return_value = {"agent_pause_state": {"paused": True}}

        with patch("src.services.agent_pause.should_auto_resume", return_value=True), \
             patch("src.services.agent_pause.is_business_hours", return_value=False):
            result = try_auto_resume("5511999999999")

        assert result is True

    def test_does_not_resume_within_business_hours(self, reset_cache, mock_supabase):
        """Test that agent is not auto-resumed within business hours."""
        mock_supabase["get"].return_value = {"agent_pause_state": {"paused": True}}

        with patch("src.services.agent_pause.should_auto_resume", return_value=False):
            result = try_auto_resume("5511999999999")

        assert result is False


class TestIsResumeCommand:
    """Tests for is_resume_command function."""

    def test_recognizes_retomar_command(self):
        """Test that /retomar is recognized as resume command."""
        assert is_resume_command("/retomar") is True

    def test_recognizes_continuar_command(self):
        """Test that /continuar is recognized as resume command."""
        assert is_resume_command("/continuar") is True

    def test_case_insensitive(self):
        """Test that commands are case insensitive."""
        assert is_resume_command("/RETOMAR") is True
        assert is_resume_command("/Continuar") is True

    def test_with_extra_text(self):
        """Test that commands with extra text are recognized."""
        assert is_resume_command("/retomar agora") is True
        assert is_resume_command("/continuar a conversa") is True

    def test_rejects_non_commands(self):
        """Test that non-commands are rejected."""
        assert is_resume_command("ola") is False
        assert is_resume_command("retomar") is False  # Without slash
        assert is_resume_command("") is False
        assert is_resume_command(None) is False


class TestProcessSdrCommand:
    """Tests for process_sdr_command function."""

    def test_processes_retomar_when_paused(self, reset_cache, mock_supabase):
        """Test that /retomar resumes the agent when paused."""
        mock_supabase["get"].return_value = {"agent_pause_state": {"paused": True}}

        with patch("src.services.agent_pause.is_business_hours", return_value=True):
            was_command, response = process_sdr_command(
                "5511999999999", "/retomar", "SDR John"
            )

        assert was_command is True
        assert "retomado com sucesso" in response.lower()

    def test_handles_resume_when_not_paused(self, reset_cache, mock_supabase):
        """Test that /retomar handles case when not paused."""
        mock_supabase["get"].return_value = {}

        was_command, response = process_sdr_command(
            "5511999999999", "/retomar", "SDR John"
        )

        assert was_command is True
        assert "ativo" in response.lower()

    def test_returns_false_for_non_command(self, reset_cache):
        """Test that non-commands return False."""
        was_command, response = process_sdr_command(
            "5511999999999", "ola tudo bem", "SDR John"
        )

        assert was_command is False
        assert response == ""


class TestClearCache:
    """Tests for clear_cache function."""

    def test_clears_all_cache(self, reset_cache, mock_supabase):
        """Test that all cache is cleared."""
        # Populate cache
        mock_supabase["get"].return_value = {"agent_pause_state": {"paused": True}}
        is_agent_paused("5511999999999")
        is_agent_paused("5511888888888")

        clear_cache()

        # Cache should be empty
        from src.services.agent_pause import _pause_cache
        assert len(_pause_cache) == 0

    def test_clears_specific_phone(self, reset_cache, mock_supabase):
        """Test that specific phone cache is cleared."""
        mock_supabase["get"].return_value = {"agent_pause_state": {"paused": True}}
        is_agent_paused("5511999999999")
        is_agent_paused("5511888888888")

        clear_cache("5511999999999")

        from src.services.agent_pause import _pause_cache
        assert "5511999999999" not in _pause_cache
        assert "5511888888888" in _pause_cache


class TestLoadPauseStatesFromSupabase:
    """Tests for load_pause_states_from_supabase function."""

    def test_loads_paused_conversations(self, reset_cache):
        """Test that paused conversations are loaded."""
        mock_response = MagicMock()
        mock_response.data = [
            {
                "lead_phone": "5511999999999",
                "context_data": {"agent_pause_state": {"paused": True}}
            },
            {
                "lead_phone": "5511888888888",
                "context_data": {"agent_pause_state": {"paused": False}}
            },
        ]

        mock_client = MagicMock()
        mock_client.table.return_value.select.return_value.execute.return_value = mock_response

        with patch("src.services.agent_pause.get_supabase_client", return_value=mock_client):
            count = load_pause_states_from_supabase()

        assert count == 1  # Only one paused conversation

    def test_handles_no_supabase_client(self, reset_cache):
        """Test handling when Supabase is not available."""
        with patch("src.services.agent_pause.get_supabase_client", return_value=None):
            count = load_pause_states_from_supabase()

        assert count == 0


class TestGetPauseInfo:
    """Tests for get_pause_info function."""

    def test_returns_none_when_not_paused(self, reset_cache, mock_supabase):
        """Test that None is returned when not paused."""
        mock_supabase["get"].return_value = {}

        result = get_pause_info("5511999999999")

        assert result is None

    def test_returns_pause_info_when_paused(self, reset_cache, mock_supabase):
        """Test that pause info is returned when paused."""
        pause_state = {
            "paused": True,
            "reason": "sdr_intervention",
            "sender_name": "John"
        }
        mock_supabase["get"].return_value = {"agent_pause_state": pause_state}

        result = get_pause_info("5511999999999")

        assert result is not None
        assert result.get("paused") is True
        assert result.get("reason") == "sdr_intervention"


class TestResumeCommands:
    """Tests for RESUME_COMMANDS constant."""

    def test_contains_expected_commands(self):
        """Test that RESUME_COMMANDS contains expected commands."""
        assert "/retomar" in RESUME_COMMANDS
        assert "/continuar" in RESUME_COMMANDS
        assert len(RESUME_COMMANDS) == 2
