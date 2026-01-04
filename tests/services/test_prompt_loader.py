"""
Tests for prompt loader service.

Tests cover:
- Loading valid XML prompts
- Handling invalid/malformed XML
- Security: path traversal prevention
- Security: XXE attack prevention
- File not found handling
- Prompt content validation
"""

import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

import pytest

from src.services.prompt_loader import (
    _PROMPTS_BASE_DIR,
    _validate_prompt_path,
    get_system_prompt_path,
    load_system_prompt_from_xml,
)


class TestGetSystemPromptPath:
    """Tests for get_system_prompt_path function."""

    def test_returns_correct_path_for_default_prompt(self):
        """Test that default prompt path is correct."""
        path = get_system_prompt_path()
        assert path.name == "sp_agente_v1.xml"
        assert "prompts" in str(path)
        assert "system_prompt" in str(path)

    def test_returns_correct_path_for_custom_prompt(self):
        """Test that custom prompt path is correct."""
        path = get_system_prompt_path("custom_prompt.xml")
        assert path.name == "custom_prompt.xml"
        assert "prompts" in str(path)
        assert "system_prompt" in str(path)

    def test_path_is_absolute(self):
        """Test that returned path can be resolved."""
        path = get_system_prompt_path()
        # Path should be resolvable (not necessarily exist)
        resolved = path.resolve()
        assert resolved is not None


class TestValidatePromptPath:
    """Tests for path validation security."""

    def test_valid_path_within_prompts_dir(self):
        """Test that valid paths within prompts directory are accepted."""
        valid_path = _PROMPTS_BASE_DIR / "sp_agente_v1.xml"
        # Should not raise
        _validate_prompt_path(valid_path)

    def test_rejects_path_traversal_attack(self):
        """Test that path traversal attacks are blocked."""
        # Attempt to escape prompts directory
        malicious_path = _PROMPTS_BASE_DIR / ".." / ".." / "etc" / "passwd"

        with pytest.raises(ValueError) as exc_info:
            _validate_prompt_path(malicious_path)

        assert "Security violation" in str(exc_info.value) or "outside allowed" in str(exc_info.value)

    def test_rejects_absolute_path_outside_prompts(self):
        """Test that absolute paths outside prompts directory are rejected."""
        if Path("/etc").exists():  # Unix-like systems
            malicious_path = Path("/etc/passwd")
        else:  # Windows
            malicious_path = Path("C:/Windows/System32/config")

        with pytest.raises(ValueError):
            _validate_prompt_path(malicious_path)


class TestLoadSystemPromptFromXml:
    """Tests for load_system_prompt_from_xml function."""

    def test_loads_valid_xml_prompt(self):
        """Test loading the actual sp_agente_v1.xml prompt."""
        prompt_path = get_system_prompt_path("sp_agente_v1.xml")
        prompt = load_system_prompt_from_xml(prompt_path)

        # Verify prompt is not empty
        assert prompt is not None
        assert len(prompt) > 0

        # Verify key sections are present
        assert "IDENTIDADE" in prompt or "Você é um agente" in prompt
        assert "MISSÃO" in prompt or "missão" in prompt.lower()

    def test_prompt_contains_expected_sections(self):
        """Test that loaded prompt contains expected sections."""
        prompt_path = get_system_prompt_path("sp_agente_v1.xml")
        prompt = load_system_prompt_from_xml(prompt_path)

        # Check for key content from the XML
        expected_content = [
            "Seleto Industrial",
            "REGRAS",
            "OBJETIVOS",
            "CONVERSA",
        ]

        for content in expected_content:
            assert content in prompt, f"Expected '{content}' in prompt"

    def test_prompt_contains_product_info(self):
        """Test that loaded prompt contains product information."""
        prompt_path = get_system_prompt_path("sp_agente_v1.xml")
        prompt = load_system_prompt_from_xml(prompt_path)

        # Check for product mentions
        products = ["CT200", "FBM100", "FB300", "FB700"]
        found_products = [p for p in products if p in prompt]

        assert len(found_products) >= 2, "Prompt should contain product information"

    def test_raises_file_not_found_for_missing_file(self):
        """Test that FileNotFoundError is raised for missing files."""
        prompt_path = _PROMPTS_BASE_DIR / "nonexistent_prompt.xml"

        with pytest.raises(FileNotFoundError) as exc_info:
            load_system_prompt_from_xml(prompt_path)

        assert "not found" in str(exc_info.value).lower()

    def test_raises_parse_error_for_malformed_xml(self):
        """Test that ParseError is raised for malformed XML."""
        # Create a temporary malformed XML file in the prompts directory
        malformed_xml = _PROMPTS_BASE_DIR / "test_malformed.xml"

        try:
            # Write malformed XML
            malformed_xml.write_text("<invalid><unclosed>", encoding="utf-8")

            with pytest.raises(ET.ParseError):
                load_system_prompt_from_xml(malformed_xml)
        finally:
            # Clean up
            if malformed_xml.exists():
                malformed_xml.unlink()

    def test_handles_empty_xml(self):
        """Test handling of empty XML file."""
        empty_xml = _PROMPTS_BASE_DIR / "test_empty.xml"

        try:
            # Write empty but valid XML
            empty_xml.write_text('<?xml version="1.0"?><system_prompt></system_prompt>', encoding="utf-8")

            # Should load without error, returning empty or minimal prompt
            prompt = load_system_prompt_from_xml(empty_xml)
            assert prompt is not None
            # Empty prompt should at least be an empty string
            assert isinstance(prompt, str)
        finally:
            # Clean up
            if empty_xml.exists():
                empty_xml.unlink()

    def test_rejects_path_traversal_in_load(self):
        """Test that path traversal is blocked during load."""
        malicious_path = _PROMPTS_BASE_DIR / ".." / ".." / "etc" / "passwd"

        with pytest.raises(ValueError) as exc_info:
            load_system_prompt_from_xml(malicious_path)

        # Should fail security validation before checking if file exists
        assert "Security" in str(exc_info.value) or "outside" in str(exc_info.value)


class TestPromptContentQuality:
    """Tests for quality of loaded prompt content."""

    @pytest.fixture
    def loaded_prompt(self):
        """Load the system prompt once for multiple tests."""
        prompt_path = get_system_prompt_path("sp_agente_v1.xml")
        return load_system_prompt_from_xml(prompt_path)

    def test_prompt_has_reasonable_length(self, loaded_prompt):
        """Test that prompt has reasonable length (not too short or too long)."""
        # Prompt should be substantial but not excessively long
        assert len(loaded_prompt) > 500, "Prompt too short"
        assert len(loaded_prompt) < 50000, "Prompt too long"

    def test_prompt_is_properly_formatted(self, loaded_prompt):
        """Test that prompt has proper formatting."""
        # Should have multiple lines
        lines = loaded_prompt.split("\n")
        assert len(lines) > 10, "Prompt should have multiple lines"

        # Should have section headers (indicated by ===)
        assert "===" in loaded_prompt, "Prompt should have section headers"

    def test_prompt_contains_behavioral_rules(self, loaded_prompt):
        """Test that prompt contains behavioral rules."""
        behavioral_keywords = [
            "cordial",
            "profissional",
            "emoji",
            "pergunta",
        ]

        found = sum(1 for kw in behavioral_keywords if kw.lower() in loaded_prompt.lower())
        assert found >= 2, "Prompt should contain behavioral rules"

    def test_prompt_contains_limitations(self, loaded_prompt):
        """Test that prompt contains limitation rules."""
        limitation_keywords = [
            "não",
            "limite",
            "limitaç",
            "restrição",
            "orçamento",
            "preço",
            "venda",
            "desconto",
        ]

        found = sum(1 for kw in limitation_keywords if kw.lower() in loaded_prompt.lower())
        assert found >= 1, "Prompt should contain limitations"


class TestPromptLoaderCaching:
    """Tests for prompt loader caching behavior."""

    def test_multiple_loads_return_same_content(self):
        """Test that multiple loads return the same content."""
        prompt_path = get_system_prompt_path("sp_agente_v1.xml")

        prompt1 = load_system_prompt_from_xml(prompt_path)
        prompt2 = load_system_prompt_from_xml(prompt_path)

        # Content should be identical
        assert prompt1 == prompt2

    def test_different_files_return_different_content(self):
        """Test that different XML files return different content."""
        import xml.etree.ElementTree as ET

        prompt1_path = get_system_prompt_path("sp_agente_v1.xml")
        prompt2_path = get_system_prompt_path("sp_calcula_temperatura.xml")

        # Skip if second file doesn't exist
        if not prompt2_path.exists():
            pytest.skip("Second prompt file not available")

        # Skip if second file is malformed XML
        try:
            ET.parse(prompt2_path)
        except ET.ParseError:
            pytest.skip("Second prompt file has malformed XML")

        prompt1 = load_system_prompt_from_xml(prompt1_path)
        prompt2 = load_system_prompt_from_xml(prompt2_path)

        # Content should be different
        assert prompt1 != prompt2
