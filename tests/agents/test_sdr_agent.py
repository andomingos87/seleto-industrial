"""
Tests for SDR Agent - TECH-035: API Key Loading

Tests to ensure OPENAI_API_KEY is properly validated and passed to OpenAIChat.
"""

import os
from unittest.mock import patch

import pytest

import src.agents.sdr_agent as agent_module
from src.config.settings import Settings


class TestCreateSdrAgentApiKey:
    """Test cases for create_sdr_agent API key handling (TECH-035)."""

    def test_create_sdr_agent_with_api_key(self):
        """Test that agent is created successfully with API key configured."""
        # Create a mock settings with API key
        mock_settings = Settings(
            OPENAI_API_KEY="sk-test-key-12345",
            OPENAI_MODEL="gpt-4o",
        )

        # Patch settings and OpenAIChat
        with patch("src.agents.sdr_agent.settings", mock_settings):
            with patch("src.agents.sdr_agent.OpenAIChat") as mock_openai:
                with patch("src.agents.sdr_agent.Agent"):
                    with patch(
                        "src.agents.sdr_agent._load_system_prompt",
                        return_value="test prompt",
                    ):
                        # Reset module-level variable
                        agent_module._system_prompt = None

                        # Create agent
                        agent_module.create_sdr_agent()

                        # Verify OpenAIChat was called with api_key
                        mock_openai.assert_called_once()
                        call_kwargs = mock_openai.call_args[1]
                        assert "api_key" in call_kwargs
                        assert call_kwargs["api_key"] == "sk-test-key-12345"
                        assert call_kwargs["id"] == "gpt-4o"

    def test_create_sdr_agent_without_api_key_raises_error(self):
        """Test that agent creation fails with clear error when API key is missing."""
        # Create settings without API key
        mock_settings = Settings(
            OPENAI_API_KEY=None,
            OPENAI_MODEL="gpt-4o",
        )

        with patch("src.agents.sdr_agent.settings", mock_settings):
            # Reset module-level variable
            agent_module._system_prompt = None

            # Should raise ValueError with clear message
            with pytest.raises(ValueError, match="OPENAI_API_KEY not configured"):
                agent_module.create_sdr_agent()

    def test_create_sdr_agent_with_empty_api_key_raises_error(self):
        """Test that empty string API key is treated as not configured."""
        # Create settings with empty API key
        mock_settings = Settings(
            OPENAI_API_KEY="",
            OPENAI_MODEL="gpt-4o",
        )

        with patch("src.agents.sdr_agent.settings", mock_settings):
            # Reset module-level variable
            agent_module._system_prompt = None

            # Should raise ValueError with clear message
            with pytest.raises(ValueError, match="OPENAI_API_KEY not configured"):
                agent_module.create_sdr_agent()

    def test_api_key_is_passed_explicitly_not_from_environ(self, monkeypatch):
        """Test that api_key is passed explicitly to OpenAIChat, not relying on os.environ."""
        # Ensure OPENAI_API_KEY is NOT in os.environ
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        # Create settings with API key (simulating load from .env)
        mock_settings = Settings(
            OPENAI_API_KEY="sk-from-dotenv-file",
            OPENAI_MODEL="gpt-4o",
        )

        with patch("src.agents.sdr_agent.settings", mock_settings):
            with patch("src.agents.sdr_agent.OpenAIChat") as mock_openai:
                with patch("src.agents.sdr_agent.Agent"):
                    with patch(
                        "src.agents.sdr_agent._load_system_prompt",
                        return_value="test prompt",
                    ):
                        agent_module._system_prompt = None

                        # Verify os.environ does NOT have the key
                        assert "OPENAI_API_KEY" not in os.environ

                        # Create agent
                        agent_module.create_sdr_agent()

                        # Verify OpenAIChat was called with explicit api_key
                        call_kwargs = mock_openai.call_args[1]
                        assert call_kwargs["api_key"] == "sk-from-dotenv-file"
