"""
Tests for the Upsell Service - US-004.

This module tests:
- Detection of FBM100 interest
- FB300 suggestion generation
- Upsell suggestion tracking
- Prevention of repetitive suggestions
"""

import pytest

from src.services.upsell import (
    FBM100_KEYWORDS,
    PRODUCTION_CONTEXT_KEYWORDS,
    clear_upsell_history,
    detect_fbm100_interest,
    generate_fb300_suggestion,
    get_upsell_context_for_agent,
    get_upsell_suggestions,
    has_production_context,
    has_suggested_fb300,
    register_upsell_suggestion,
    should_suggest_upsell,
)


class TestDetectFBM100Interest:
    """Tests for FBM100 interest detection."""

    def test_detects_fbm100_exact_match(self):
        """Should detect exact 'FBM100' keyword."""
        assert detect_fbm100_interest("Quero saber mais sobre a FBM100") is True

    def test_detects_fbm100_with_space(self):
        """Should detect 'FBM 100' with space."""
        assert detect_fbm100_interest("Me fale sobre a FBM 100") is True

    def test_detects_fbm100_with_hyphen(self):
        """Should detect 'FBM-100' with hyphen."""
        assert detect_fbm100_interest("Quanto custa a FBM-100?") is True

    def test_detects_formadora_manual(self):
        """Should detect 'formadora manual' keyword."""
        assert detect_fbm100_interest("Preciso de uma formadora manual") is True

    def test_detects_formadora_hamburguer_manual(self):
        """Should detect 'formadora de hambúrguer manual'."""
        assert detect_fbm100_interest("Vocês tem formadora de hambúrguer manual?") is True

    def test_detects_hamburguer_manual(self):
        """Should detect 'hambúrguer manual'."""
        assert detect_fbm100_interest("Quero fazer hambúrguer manual") is True

    def test_detects_maquina_manual(self):
        """Should detect 'máquina manual'."""
        assert detect_fbm100_interest("Preciso de uma máquina manual para hambúrguer") is True

    def test_case_insensitive(self):
        """Should be case insensitive."""
        assert detect_fbm100_interest("FORMADORA MANUAL") is True
        assert detect_fbm100_interest("fbm100") is True
        assert detect_fbm100_interest("FbM100") is True

    def test_returns_false_for_no_match(self):
        """Should return False when no FBM100 keywords found."""
        assert detect_fbm100_interest("Quero uma formadora automática") is False
        assert detect_fbm100_interest("Me fale sobre a FB300") is False
        assert detect_fbm100_interest("Qual a melhor formadora?") is False

    def test_returns_false_for_empty_message(self):
        """Should return False for empty message."""
        assert detect_fbm100_interest("") is False
        assert detect_fbm100_interest(None) is False

    def test_all_keywords_are_detected(self):
        """Should detect all defined FBM100 keywords."""
        for keyword in FBM100_KEYWORDS:
            message = f"Eu gostaria de saber sobre {keyword}"
            assert detect_fbm100_interest(message) is True, f"Failed for keyword: {keyword}"


class TestHasProductionContext:
    """Tests for production context detection."""

    def test_detects_producao(self):
        """Should detect production-related keywords."""
        assert has_production_context("Qual a produção dessa máquina?") is True

    def test_detects_produtividade(self):
        """Should detect productivity keywords."""
        assert has_production_context("Qual a produtividade por hora?") is True

    def test_detects_quantidade(self):
        """Should detect quantity keywords."""
        assert has_production_context("Quantos hambúrgueres por dia?") is True

    def test_detects_aumentar_producao(self):
        """Should detect 'aumentar produção'."""
        assert has_production_context("Quero aumentar minha produção") is True

    def test_returns_false_for_no_context(self):
        """Should return False when no production context."""
        assert has_production_context("Qual o tamanho da máquina?") is False

    def test_all_keywords_are_detected(self):
        """Should detect all defined production keywords."""
        for keyword in PRODUCTION_CONTEXT_KEYWORDS:
            message = f"Pergunta sobre {keyword}"
            assert has_production_context(message) is True, f"Failed for keyword: {keyword}"


class TestGenerateFB300Suggestion:
    """Tests for FB300 suggestion generation."""

    def test_generates_non_empty_suggestion(self):
        """Should generate a non-empty suggestion."""
        suggestion = generate_fb300_suggestion()
        assert suggestion is not None
        assert len(suggestion) > 0

    def test_suggestion_contains_fb300(self):
        """Suggestion should mention FB300."""
        suggestion = generate_fb300_suggestion()
        assert "FB300" in suggestion

    def test_suggestion_contains_fbm100(self):
        """Suggestion should mention FBM100 for comparison."""
        suggestion = generate_fb300_suggestion()
        assert "FBM100" in suggestion

    def test_suggestion_is_consultive(self):
        """Suggestion should have consultive tone markers."""
        suggestion = generate_fb300_suggestion()
        # Check for consultive tone markers
        assert "consultivo" in suggestion.lower() or "consultiva" in suggestion.lower()
        assert "pressão" in suggestion.lower() or "pressione" in suggestion.lower()

    def test_suggestion_contains_productivity_comparison(self):
        """Suggestion should contain productivity comparison."""
        suggestion = generate_fb300_suggestion()
        # Check for productivity numbers
        assert "300-350" in suggestion or "300 a 350" in suggestion
        assert "500-600" in suggestion or "500 a 600" in suggestion

    def test_suggestion_contains_example(self):
        """Suggestion should contain an example approach."""
        suggestion = generate_fb300_suggestion()
        assert "EXEMPLO" in suggestion or "exemplo" in suggestion


class TestUpsellSuggestionTracking:
    """Tests for upsell suggestion tracking."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Clear upsell history before and after each test."""
        clear_upsell_history("5511999998888")
        clear_upsell_history("5511999997777")
        yield
        clear_upsell_history("5511999998888")
        clear_upsell_history("5511999997777")

    def test_register_upsell_suggestion(self):
        """Should register an upsell suggestion."""
        phone = "5511999998888"
        register_upsell_suggestion(
            phone=phone,
            from_product="FBM100",
            to_product="FB300",
            message_trigger="Quero a FBM100",
        )

        suggestions = get_upsell_suggestions(phone)
        assert len(suggestions) == 1
        assert suggestions[0].from_product == "FBM100"
        assert suggestions[0].to_product == "FB300"
        assert suggestions[0].phone == phone

    def test_has_suggested_fb300_returns_true_after_suggestion(self):
        """Should return True after FB300 has been suggested."""
        phone = "5511999998888"
        assert has_suggested_fb300(phone) is False

        register_upsell_suggestion(
            phone=phone,
            from_product="FBM100",
            to_product="FB300",
            message_trigger="test",
        )

        assert has_suggested_fb300(phone) is True

    def test_has_suggested_fb300_returns_false_for_other_products(self):
        """Should return False if only other products were suggested."""
        phone = "5511999998888"
        register_upsell_suggestion(
            phone=phone,
            from_product="FB300",
            to_product="FB700",
            message_trigger="test",
        )

        assert has_suggested_fb300(phone) is False

    def test_clear_upsell_history(self):
        """Should clear upsell history for a phone."""
        phone = "5511999998888"
        register_upsell_suggestion(
            phone=phone,
            from_product="FBM100",
            to_product="FB300",
            message_trigger="test",
        )

        assert len(get_upsell_suggestions(phone)) == 1

        clear_upsell_history(phone)

        assert len(get_upsell_suggestions(phone)) == 0

    def test_multiple_suggestions_for_same_phone(self):
        """Should track multiple suggestions for the same phone."""
        phone = "5511999998888"
        register_upsell_suggestion(
            phone=phone,
            from_product="FBM100",
            to_product="FB300",
            message_trigger="test1",
        )
        register_upsell_suggestion(
            phone=phone,
            from_product="FB300",
            to_product="FB700",
            message_trigger="test2",
        )

        suggestions = get_upsell_suggestions(phone)
        assert len(suggestions) == 2

    def test_suggestions_are_isolated_by_phone(self):
        """Suggestions should be isolated by phone number."""
        phone1 = "5511999998888"
        phone2 = "5511999997777"

        register_upsell_suggestion(
            phone=phone1,
            from_product="FBM100",
            to_product="FB300",
            message_trigger="test",
        )

        assert len(get_upsell_suggestions(phone1)) == 1
        assert len(get_upsell_suggestions(phone2)) == 0


class TestShouldSuggestUpsell:
    """Tests for the main upsell decision logic."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Clear upsell history before and after each test."""
        clear_upsell_history("5511999998888")
        yield
        clear_upsell_history("5511999998888")

    def test_should_suggest_when_fbm100_detected(self):
        """Should suggest upsell when FBM100 interest is detected."""
        phone = "5511999998888"
        message = "Me fale sobre a FBM100"

        assert should_suggest_upsell(phone, message) is True

    def test_should_not_suggest_when_no_fbm100_interest(self):
        """Should not suggest when no FBM100 interest detected."""
        phone = "5511999998888"
        message = "Quero saber sobre a FB700"

        assert should_suggest_upsell(phone, message) is False

    def test_should_not_suggest_twice(self):
        """Should not suggest FB300 twice to the same lead."""
        phone = "5511999998888"
        message = "Me fale sobre a FBM100"

        # First suggestion should be allowed
        assert should_suggest_upsell(phone, message) is True

        # Register the suggestion
        register_upsell_suggestion(
            phone=phone,
            from_product="FBM100",
            to_product="FB300",
            message_trigger=message,
        )

        # Second suggestion should be blocked
        assert should_suggest_upsell(phone, "Mais informações sobre a formadora manual") is False


class TestGetUpsellContextForAgent:
    """Tests for the main agent context function."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Clear upsell history before and after each test."""
        clear_upsell_history("5511999998888")
        yield
        clear_upsell_history("5511999998888")

    def test_returns_context_when_upsell_should_be_suggested(self):
        """Should return context when upsell should be suggested."""
        phone = "5511999998888"
        message = "Quero a FBM100"

        context = get_upsell_context_for_agent(phone, message)

        assert context is not None
        assert "FB300" in context
        assert "FBM100" in context

    def test_returns_none_when_no_upsell(self):
        """Should return None when no upsell should be made."""
        phone = "5511999998888"
        message = "Quero saber sobre cortadoras"

        context = get_upsell_context_for_agent(phone, message)

        assert context is None

    def test_registers_suggestion_when_context_returned(self):
        """Should register the suggestion when context is returned."""
        phone = "5511999998888"
        message = "Preciso de uma formadora manual"

        # Initially no suggestions
        assert len(get_upsell_suggestions(phone)) == 0

        # Get context (which should register suggestion)
        context = get_upsell_context_for_agent(phone, message)

        # Now should have one suggestion
        assert context is not None
        assert len(get_upsell_suggestions(phone)) == 1
        assert has_suggested_fb300(phone) is True

    def test_returns_none_after_first_suggestion(self):
        """Should return None after first suggestion is made."""
        phone = "5511999998888"

        # First call should return context
        context1 = get_upsell_context_for_agent(phone, "Me fale da FBM100")
        assert context1 is not None

        # Second call should return None
        context2 = get_upsell_context_for_agent(phone, "Me fale mais da formadora manual")
        assert context2 is None


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Clear upsell history before and after each test."""
        clear_upsell_history("5511999998888")
        yield
        clear_upsell_history("5511999998888")

    def test_handles_message_with_special_characters(self):
        """Should handle messages with special characters."""
        message = "Quero a FBM100!!! É boa? @#$%"
        assert detect_fbm100_interest(message) is True

    def test_handles_long_message(self):
        """Should handle very long messages."""
        message = "Eu gostaria de saber mais " * 100 + "sobre a FBM100"
        assert detect_fbm100_interest(message) is True

    def test_handles_unicode_characters(self):
        """Should handle unicode characters."""
        message = "Quero a formadora manual 🍔 FBM100"
        assert detect_fbm100_interest(message) is True

    def test_truncates_long_trigger_message(self):
        """Should truncate very long trigger messages."""
        phone = "5511999998888"
        long_message = "FBM100 " * 100

        register_upsell_suggestion(
            phone=phone,
            from_product="FBM100",
            to_product="FB300",
            message_trigger=long_message,
        )

        suggestions = get_upsell_suggestions(phone)
        assert len(suggestions[0].message_trigger) <= 200
