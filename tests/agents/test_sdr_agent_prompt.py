"""
Integration tests for SDR agent prompt loading.

Tests cover:
- System prompt loading on agent creation
- Prompt is applied to agent instructions
- Prompt reload functionality
- Cache behavior
"""

from unittest.mock import Mock, patch

import pytest

from src.agents.sdr_agent import (
    _load_system_prompt,
    create_sdr_agent,
    reload_system_prompt,
)
from src.services.prompt_loader import get_system_prompt_path


class TestSystemPromptLoading:
    """Tests for system prompt loading in SDR agent."""

    @pytest.fixture(autouse=True)
    def reset_prompt_cache(self):
        """Reset the global prompt cache before and after each test."""
        import src.agents.sdr_agent as agent_module
        original = agent_module._system_prompt
        agent_module._system_prompt = None
        yield
        agent_module._system_prompt = original

    def test_load_system_prompt_returns_string(self):
        """Test that _load_system_prompt returns a string."""
        prompt = _load_system_prompt()

        assert isinstance(prompt, str)
        assert len(prompt) > 0

    def test_load_system_prompt_caches_result(self):
        """Test that prompt is cached after first load."""
        import src.agents.sdr_agent as agent_module

        # First load
        prompt1 = _load_system_prompt()
        cached_value = agent_module._system_prompt

        # Second load should return cached value
        prompt2 = _load_system_prompt()

        assert prompt1 == prompt2
        assert agent_module._system_prompt == cached_value

    def test_load_system_prompt_force_reload(self):
        """Test that force_reload bypasses cache."""
        import src.agents.sdr_agent as agent_module

        # First load
        _load_system_prompt()
        original_cache = agent_module._system_prompt

        # Force reload
        with patch("src.agents.sdr_agent.load_system_prompt_from_xml") as mock_load:
            mock_load.return_value = "New prompt content"
            prompt = _load_system_prompt(force_reload=True)

        # Should have called the loader again
        mock_load.assert_called_once()
        assert prompt == "New prompt content"

    def test_reload_system_prompt_function(self):
        """Test reload_system_prompt function."""
        # First load
        original_prompt = _load_system_prompt()

        # Reload
        reloaded_prompt = reload_system_prompt()

        # Should have content (from actual XML)
        assert len(reloaded_prompt) > 0
        # Content should be same (file didn't change)
        assert original_prompt == reloaded_prompt

    def test_prompt_contains_expected_content(self):
        """Test that loaded prompt contains expected content from XML."""
        prompt = _load_system_prompt()

        # Check for key content
        assert "Seleto Industrial" in prompt
        assert "IDENTIDADE" in prompt or "agente" in prompt.lower()


class TestAgentCreation:
    """Tests for agent creation with system prompt."""

    @pytest.fixture(autouse=True)
    def reset_prompt_cache(self):
        """Reset the global prompt cache before each test."""
        import src.agents.sdr_agent as agent_module
        original = agent_module._system_prompt
        agent_module._system_prompt = None
        yield
        agent_module._system_prompt = original

    @patch("src.agents.sdr_agent.Agent")
    @patch("src.agents.sdr_agent.OpenAIChat")
    def test_agent_receives_system_prompt(self, mock_openai, mock_agent):
        """Test that agent is created with system prompt in instructions."""
        mock_openai.return_value = Mock()
        mock_agent.return_value = Mock()

        with patch.object(
            __import__("src.config.settings", fromlist=["settings"]).settings,
            "OPENAI_API_KEY",
            "test-key",
        ):
            create_sdr_agent()

        # Verify Agent was called with instructions
        call_kwargs = mock_agent.call_args.kwargs
        assert "instructions" in call_kwargs
        assert len(call_kwargs["instructions"]) > 0
        assert isinstance(call_kwargs["instructions"][0], str)

    @patch("src.agents.sdr_agent.Agent")
    @patch("src.agents.sdr_agent.OpenAIChat")
    def test_agent_prompt_is_not_empty(self, mock_openai, mock_agent):
        """Test that agent prompt is not empty."""
        mock_openai.return_value = Mock()
        mock_agent.return_value = Mock()

        with patch.object(
            __import__("src.config.settings", fromlist=["settings"]).settings,
            "OPENAI_API_KEY",
            "test-key",
        ):
            create_sdr_agent()

        # Get the instructions passed to Agent
        instructions = mock_agent.call_args.kwargs["instructions"]
        prompt = instructions[0]

        # Prompt should have substantial content
        assert len(prompt) > 100

    @patch("src.agents.sdr_agent.Agent")
    @patch("src.agents.sdr_agent.OpenAIChat")
    def test_agent_prompt_contains_behavioral_rules(self, mock_openai, mock_agent):
        """Test that agent prompt contains behavioral rules."""
        mock_openai.return_value = Mock()
        mock_agent.return_value = Mock()

        with patch.object(
            __import__("src.config.settings", fromlist=["settings"]).settings,
            "OPENAI_API_KEY",
            "test-key",
        ):
            create_sdr_agent()

        # Get the instructions
        instructions = mock_agent.call_args.kwargs["instructions"]
        prompt = instructions[0]

        # Should contain behavioral guidance
        assert "REGRAS" in prompt or "regras" in prompt.lower()


class TestPromptReloadAfterRestart:
    """Tests to verify prompt reloads correctly after simulated restart."""

    @pytest.fixture(autouse=True)
    def reset_prompt_cache(self):
        """Reset the global prompt cache before each test."""
        import src.agents.sdr_agent as agent_module
        original = agent_module._system_prompt
        agent_module._system_prompt = None
        yield
        agent_module._system_prompt = original

    def test_prompt_loads_fresh_after_cache_cleared(self):
        """Test that prompt loads fresh when cache is cleared (simulating restart)."""
        import src.agents.sdr_agent as agent_module

        # Simulate initial load
        prompt1 = _load_system_prompt()
        assert agent_module._system_prompt is not None

        # Simulate restart by clearing cache
        agent_module._system_prompt = None

        # Load again - should load fresh
        with patch("src.agents.sdr_agent.load_system_prompt_from_xml") as mock_load:
            mock_load.return_value = "Fresh prompt after restart"
            prompt2 = _load_system_prompt()

        # Should have called loader
        mock_load.assert_called_once()
        assert prompt2 == "Fresh prompt after restart"

    def test_multiple_agents_use_same_cached_prompt(self):
        """Test that multiple agent instances use the same cached prompt."""
        import src.agents.sdr_agent as agent_module

        with patch("src.agents.sdr_agent.Agent") as mock_agent, \
             patch("src.agents.sdr_agent.OpenAIChat") as mock_openai:
            mock_openai.return_value = Mock()
            mock_agent.return_value = Mock()

            with patch.object(
                __import__("src.config.settings", fromlist=["settings"]).settings,
                "OPENAI_API_KEY",
                "test-key",
            ):
                # Create first agent
                create_sdr_agent()
                first_prompt = mock_agent.call_args.kwargs["instructions"][0]

                # Create second agent
                create_sdr_agent()
                second_prompt = mock_agent.call_args.kwargs["instructions"][0]

        # Both agents should have the same prompt
        assert first_prompt == second_prompt


class TestPromptLoadingErrors:
    """Tests for error handling in prompt loading."""

    @pytest.fixture(autouse=True)
    def reset_prompt_cache(self):
        """Reset the global prompt cache before each test."""
        import src.agents.sdr_agent as agent_module
        original = agent_module._system_prompt
        agent_module._system_prompt = None
        yield
        agent_module._system_prompt = original

    def test_raises_error_for_missing_xml(self):
        """Test that missing XML file raises FileNotFoundError."""
        with patch("src.agents.sdr_agent.get_system_prompt_path") as mock_path:
            # Point to non-existent file
            from src.services.prompt_loader import _PROMPTS_BASE_DIR
            mock_path.return_value = _PROMPTS_BASE_DIR / "nonexistent.xml"

            with pytest.raises(FileNotFoundError):
                _load_system_prompt()

    def test_raises_error_for_malformed_xml(self):
        """Test that malformed XML raises ParseError."""
        import xml.etree.ElementTree as ET
        from src.services.prompt_loader import _PROMPTS_BASE_DIR

        malformed_file = _PROMPTS_BASE_DIR / "test_malformed_agent.xml"

        try:
            # Create malformed XML
            malformed_file.write_text("<broken><unclosed>", encoding="utf-8")

            with patch("src.agents.sdr_agent.get_system_prompt_path") as mock_path:
                mock_path.return_value = malformed_file

                with pytest.raises(ET.ParseError):
                    _load_system_prompt()
        finally:
            if malformed_file.exists():
                malformed_file.unlink()


class TestPromptFileIntegrity:
    """Tests to verify the prompt file exists and is valid."""

    def test_default_prompt_file_exists(self):
        """Test that the default prompt file exists."""
        prompt_path = get_system_prompt_path("sp_agente_v1.xml")
        assert prompt_path.exists(), f"Prompt file not found: {prompt_path}"

    def test_default_prompt_file_is_valid_xml(self):
        """Test that the default prompt file is valid XML."""
        import xml.etree.ElementTree as ET

        prompt_path = get_system_prompt_path("sp_agente_v1.xml")

        # Should parse without error
        tree = ET.parse(prompt_path)
        root = tree.getroot()

        # Should have root element
        assert root is not None
        assert root.tag == "system_prompt"

    def test_default_prompt_has_required_sections(self):
        """Test that default prompt has required XML sections."""
        import xml.etree.ElementTree as ET

        prompt_path = get_system_prompt_path("sp_agente_v1.xml")
        tree = ET.parse(prompt_path)
        root = tree.getroot()

        # Check for required sections
        required_sections = ["role", "rules", "objectives"]
        for section in required_sections:
            element = root.find(section)
            assert element is not None, f"Missing required section: {section}"
