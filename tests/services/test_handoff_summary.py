"""
Tests for handoff summary service.

This module tests the handoff summary functionality including:
- Summary generation with all fields
- Summary generation with missing fields
- Sending internal messages to Chatwoot
- Trigger on hot lead classification
- Duplicate prevention
- Error handling
"""

import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock, AsyncMock

from src.services.handoff_summary import (
    generate_handoff_summary,
    is_handoff_summary_sent,
    mark_handoff_summary_sent,
    send_handoff_summary,
    trigger_handoff_on_hot_lead,
    clear_handoff_summary_flag,
    _get_field_value,
    NOT_INFORMED,
    HANDOFF_SUMMARY_SENT_KEY,
)


# Fixtures for lead data
@pytest.fixture
def complete_lead_data():
    """Complete lead data with all fields filled."""
    return {
        "name": "Joao Silva",
        "company": "Frigorifico ABC",
        "city": "Sao Paulo",
        "uf": "SP",
        "product": "Formadora de Hamburguer FB300",
        "volume": "500 kg/dia",
        "urgency": "Alta - precisa para proximo mes",
        "knows_seleto": "Sim, ja comprou cortadora",
    }


@pytest.fixture
def partial_lead_data():
    """Partial lead data with some fields missing."""
    return {
        "name": "Maria Santos",
        "company": None,
        "city": "Curitiba",
        "uf": "PR",
        "product": "Moedor de Carne",
        "volume": None,
        "urgency": None,
        "knows_seleto": None,
    }


@pytest.fixture
def minimal_lead_data():
    """Minimal lead data (only required fields)."""
    return {
        "name": "Lead Teste",
        "product": "Equipamento industrial",
    }


@pytest.fixture
def orcamento_data():
    """Sample budget/quote data."""
    return {
        "resumo": "Lead interessado em formadora para producao de hamburgueres",
        "produto": "Formadora FB300",
        "segmento": "Frigorifico",
        "urgencia_compra": "Alta",
        "volume_diario": "500L",
    }


@pytest.fixture
def empresa_data():
    """Sample company data."""
    return {
        "nome": "Frigorifico ABC Ltda",
        "cidade": "Sao Paulo",
        "uf": "SP",
        "cnpj": "12345678000190",
    }


class TestGetFieldValue:
    """Tests for _get_field_value helper function."""

    def test_extracts_value_from_first_source(self):
        """Test that value is extracted from first source."""
        source1 = {"name": "John"}
        source2 = {"name": "Jane"}

        result = _get_field_value(source1, source2, keys=["name"])

        assert result == "John"

    def test_falls_back_to_second_source(self):
        """Test that value falls back to second source."""
        source1 = {}
        source2 = {"name": "Jane"}

        result = _get_field_value(source1, source2, keys=["name"])

        assert result == "Jane"

    def test_tries_multiple_keys(self):
        """Test that multiple keys are tried."""
        source = {"nome": "John"}

        result = _get_field_value(source, keys=["name", "nome"])

        assert result == "John"

    def test_returns_default_when_not_found(self):
        """Test that default is returned when value not found."""
        source = {}

        result = _get_field_value(source, keys=["name"])

        assert result == NOT_INFORMED

    def test_custom_default_value(self):
        """Test custom default value."""
        source = {}

        result = _get_field_value(source, keys=["name"], default="N/A")

        assert result == "N/A"

    def test_ignores_empty_strings(self):
        """Test that empty strings are treated as missing."""
        source1 = {"name": ""}
        source2 = {"name": "John"}

        result = _get_field_value(source1, source2, keys=["name"])

        assert result == "John"

    def test_ignores_whitespace_only(self):
        """Test that whitespace-only values are treated as missing."""
        source1 = {"name": "   "}
        source2 = {"name": "John"}

        result = _get_field_value(source1, source2, keys=["name"])

        assert result == "John"

    def test_handles_none_sources(self):
        """Test that None sources are handled."""
        result = _get_field_value(None, None, keys=["name"])

        assert result == NOT_INFORMED


class TestGenerateHandoffSummary:
    """Tests for generate_handoff_summary function."""

    def test_generates_summary_with_all_fields(self, complete_lead_data, orcamento_data):
        """Test summary generation with all fields populated."""
        summary = generate_handoff_summary(
            lead_data=complete_lead_data,
            orcamento_data=orcamento_data,
            canal="WhatsApp",
        )

        assert "Novo Lead Quente - via WhatsApp" in summary
        assert "Nome: Joao Silva" in summary
        assert "Empresa: Frigorifico ABC" in summary
        assert "Localizacao: Sao Paulo/SP" in summary
        assert "Produto de Interesse: Formadora de Hamburguer FB300" in summary
        assert "Capacidade / Volume: 500 kg/dia" in summary
        assert "Urgencia: Alta - precisa para proximo mes" in summary
        assert "Ja conhece a Seleto Industrial?: Sim, ja comprou cortadora" in summary
        assert "Observacoes adicionais: Lead interessado" in summary

    def test_fills_missing_fields_with_nao_informado(self, partial_lead_data):
        """Test summary generation with missing fields shows 'Nao informado'."""
        summary = generate_handoff_summary(lead_data=partial_lead_data)

        assert "Nome: Maria Santos" in summary
        assert f"Empresa: {NOT_INFORMED}" in summary
        assert "Localizacao: Curitiba/PR" in summary
        assert "Produto de Interesse: Moedor de Carne" in summary
        assert f"Capacidade / Volume: {NOT_INFORMED}" in summary
        assert f"Urgencia: {NOT_INFORMED}" in summary
        assert f"Ja conhece a Seleto Industrial?: {NOT_INFORMED}" in summary

    def test_generates_summary_with_no_data(self):
        """Test summary generation with no data."""
        summary = generate_handoff_summary()

        assert "Novo Lead Quente - via WhatsApp" in summary
        assert f"Nome: {NOT_INFORMED}" in summary
        assert f"Empresa: {NOT_INFORMED}" in summary

    def test_uses_empresa_data_as_fallback(self, empresa_data):
        """Test that empresa_data is used as fallback for company info."""
        summary = generate_handoff_summary(empresa_data=empresa_data)

        assert "Empresa: Frigorifico ABC Ltda" in summary
        assert "Localizacao: Sao Paulo/SP" in summary

    def test_uses_orcamento_data_for_product_info(self, orcamento_data):
        """Test that orcamento_data is used for product info."""
        summary = generate_handoff_summary(orcamento_data=orcamento_data)

        assert "Produto de Interesse: Formadora FB300" in summary
        assert "Capacidade / Volume: 500L" in summary
        assert "Urgencia: Alta" in summary

    def test_uses_conversation_summary_as_observations(self):
        """Test that conversation_summary is used for observations."""
        summary = generate_handoff_summary(
            conversation_summary="Lead muito interessado no produto"
        )

        assert "Observacoes adicionais: Lead muito interessado" in summary

    def test_custom_canal(self):
        """Test summary with custom channel."""
        summary = generate_handoff_summary(canal="Telefone")

        assert "Novo Lead Quente - via Telefone" in summary

    def test_location_with_only_city(self):
        """Test location formatting with only city."""
        lead_data = {"city": "Campinas"}

        summary = generate_handoff_summary(lead_data=lead_data)

        assert "Localizacao: Campinas" in summary

    def test_location_with_only_uf(self):
        """Test location formatting with only UF."""
        lead_data = {"uf": "MG"}

        summary = generate_handoff_summary(lead_data=lead_data)

        assert "Localizacao: MG" in summary

    def test_handles_minimal_data(self, minimal_lead_data):
        """Test that summary is generated even with minimal data."""
        summary = generate_handoff_summary(lead_data=minimal_lead_data)

        assert "Nome: Lead Teste" in summary
        assert "Produto de Interesse: Equipamento industrial" in summary


class TestIsHandoffSummarySent:
    """Tests for is_handoff_summary_sent function."""

    @pytest.fixture
    def mock_supabase(self):
        """Mock Supabase context functions."""
        with patch("src.services.handoff_summary.get_context_from_supabase") as mock_get:
            mock_get.return_value = {}
            yield mock_get

    def test_returns_false_when_not_sent(self, mock_supabase):
        """Test that False is returned when summary not sent."""
        mock_supabase.return_value = {}

        result = is_handoff_summary_sent("5511999999999")

        assert result is False

    def test_returns_true_when_sent(self, mock_supabase):
        """Test that True is returned when summary was sent."""
        mock_supabase.return_value = {
            HANDOFF_SUMMARY_SENT_KEY: {"sent": True}
        }

        result = is_handoff_summary_sent("5511999999999")

        assert result is True

    def test_returns_false_when_sent_is_false(self, mock_supabase):
        """Test that False is returned when sent flag is False."""
        mock_supabase.return_value = {
            HANDOFF_SUMMARY_SENT_KEY: {"sent": False}
        }

        result = is_handoff_summary_sent("5511999999999")

        assert result is False

    def test_handles_invalid_phone(self, mock_supabase):
        """Test that invalid phone returns False."""
        result = is_handoff_summary_sent("")

        assert result is False
        mock_supabase.assert_not_called()

    def test_normalizes_phone(self, mock_supabase):
        """Test that phone is normalized before lookup."""
        mock_supabase.return_value = {}

        is_handoff_summary_sent("+55 (11) 99999-9999")

        mock_supabase.assert_called_once_with("5511999999999")


class TestMarkHandoffSummarySent:
    """Tests for mark_handoff_summary_sent function."""

    @pytest.fixture
    def mock_supabase(self):
        """Mock Supabase context functions."""
        with patch("src.services.handoff_summary.get_context_from_supabase") as mock_get, \
             patch("src.services.handoff_summary.save_context_to_supabase") as mock_save:
            mock_get.return_value = {}
            mock_save.return_value = True
            yield {"get": mock_get, "save": mock_save}

    def test_marks_summary_as_sent(self, mock_supabase):
        """Test that summary is marked as sent."""
        result = mark_handoff_summary_sent("5511999999999")

        assert result is True
        mock_supabase["save"].assert_called_once()

        # Check the saved context
        saved_context = mock_supabase["save"].call_args[0][1]
        assert saved_context[HANDOFF_SUMMARY_SENT_KEY]["sent"] is True
        assert "sent_at" in saved_context[HANDOFF_SUMMARY_SENT_KEY]
        assert saved_context[HANDOFF_SUMMARY_SENT_KEY]["temperature"] == "quente"

    def test_handles_save_failure(self, mock_supabase):
        """Test handling of save failure."""
        mock_supabase["save"].return_value = False

        result = mark_handoff_summary_sent("5511999999999")

        assert result is False

    def test_handles_invalid_phone(self, mock_supabase):
        """Test that invalid phone returns False."""
        result = mark_handoff_summary_sent("")

        assert result is False
        mock_supabase["save"].assert_not_called()


class TestSendHandoffSummary:
    """Tests for send_handoff_summary function."""

    @pytest.fixture
    def mock_dependencies(self):
        """Mock all dependencies for send_handoff_summary."""
        with patch("src.services.handoff_summary.is_handoff_summary_sent") as mock_is_sent, \
             patch("src.services.handoff_summary.mark_handoff_summary_sent") as mock_mark, \
             patch("src.services.handoff_summary.send_internal_message_to_chatwoot", new_callable=AsyncMock) as mock_send, \
             patch("src.services.handoff_summary.normalize_phone") as mock_normalize:
            mock_is_sent.return_value = False
            mock_mark.return_value = True
            mock_send.return_value = True
            mock_normalize.side_effect = lambda x: x.replace("+", "").replace(" ", "").replace("-", "").replace("(", "").replace(")", "") if x else None
            yield {
                "is_sent": mock_is_sent,
                "mark": mock_mark,
                "send": mock_send,
                "normalize": mock_normalize,
            }

    @pytest.mark.asyncio
    async def test_sends_summary_successfully(self, mock_dependencies):
        """Test that summary is sent successfully."""
        result = await send_handoff_summary(
            phone="5511999999999",
            lead_data={"name": "John"},
        )

        assert result is True
        mock_dependencies["send"].assert_called_once()
        mock_dependencies["mark"].assert_called_once()

    @pytest.mark.asyncio
    async def test_skips_if_already_sent(self, mock_dependencies):
        """Test that summary is skipped if already sent."""
        mock_dependencies["is_sent"].return_value = True

        result = await send_handoff_summary(phone="5511999999999")

        assert result is False
        mock_dependencies["send"].assert_not_called()

    @pytest.mark.asyncio
    async def test_sends_with_force_flag(self, mock_dependencies):
        """Test that force flag bypasses duplicate check."""
        mock_dependencies["is_sent"].return_value = True

        result = await send_handoff_summary(
            phone="5511999999999",
            force=True,
        )

        assert result is True
        mock_dependencies["send"].assert_called_once()

    @pytest.mark.asyncio
    async def test_handles_invalid_phone(self, mock_dependencies):
        """Test handling of invalid phone."""
        # Clear side_effect and set return_value to None for invalid phone
        mock_dependencies["normalize"].side_effect = None
        mock_dependencies["normalize"].return_value = None

        result = await send_handoff_summary(phone="invalid")

        assert result is False
        mock_dependencies["send"].assert_not_called()

    @pytest.mark.asyncio
    async def test_handles_chatwoot_failure(self, mock_dependencies):
        """Test handling of Chatwoot send failure."""
        mock_dependencies["send"].return_value = False

        result = await send_handoff_summary(phone="5511999999999")

        assert result is False
        mock_dependencies["mark"].assert_not_called()

    @pytest.mark.asyncio
    async def test_handles_chatwoot_exception(self, mock_dependencies):
        """Test handling of Chatwoot exception."""
        mock_dependencies["send"].side_effect = Exception("Connection error")

        result = await send_handoff_summary(phone="5511999999999")

        assert result is False

    @pytest.mark.asyncio
    async def test_sends_as_internal_message(self, mock_dependencies):
        """Test that summary is sent as internal message."""
        await send_handoff_summary(phone="5511999999999")

        call_kwargs = mock_dependencies["send"].call_args[1]
        assert "content" in call_kwargs
        assert call_kwargs["sender_name"] == "Sistema - Lead Quente"


class TestTriggerHandoffOnHotLead:
    """Tests for trigger_handoff_on_hot_lead function."""

    @pytest.fixture
    def mock_send_handoff(self):
        """Mock send_handoff_summary function."""
        with patch("src.services.handoff_summary.send_handoff_summary", new_callable=AsyncMock) as mock:
            mock.return_value = True
            yield mock

    @pytest.mark.asyncio
    async def test_triggers_for_hot_lead(self, mock_send_handoff):
        """Test that handoff is triggered for hot lead."""
        result = await trigger_handoff_on_hot_lead(
            phone="5511999999999",
            lead_data={"name": "John"},
            temperature="quente",
        )

        assert result is True
        mock_send_handoff.assert_called_once()

    @pytest.mark.asyncio
    async def test_does_not_trigger_for_warm_lead(self, mock_send_handoff):
        """Test that handoff is not triggered for warm lead."""
        result = await trigger_handoff_on_hot_lead(
            phone="5511999999999",
            temperature="morno",
        )

        assert result is False
        mock_send_handoff.assert_not_called()

    @pytest.mark.asyncio
    async def test_does_not_trigger_for_cold_lead(self, mock_send_handoff):
        """Test that handoff is not triggered for cold lead."""
        result = await trigger_handoff_on_hot_lead(
            phone="5511999999999",
            temperature="frio",
        )

        assert result is False
        mock_send_handoff.assert_not_called()

    @pytest.mark.asyncio
    async def test_case_insensitive_temperature(self, mock_send_handoff):
        """Test that temperature comparison is case insensitive."""
        result = await trigger_handoff_on_hot_lead(
            phone="5511999999999",
            temperature="QUENTE",
        )

        assert result is True
        mock_send_handoff.assert_called_once()

    @pytest.mark.asyncio
    async def test_passes_justification_as_summary(self, mock_send_handoff):
        """Test that justification is passed as conversation summary."""
        await trigger_handoff_on_hot_lead(
            phone="5511999999999",
            temperature="quente",
            justification="Cliente com urgencia alta",
        )

        call_kwargs = mock_send_handoff.call_args[1]
        assert call_kwargs["conversation_summary"] == "Cliente com urgencia alta"


class TestClearHandoffSummaryFlag:
    """Tests for clear_handoff_summary_flag function."""

    @pytest.fixture
    def mock_supabase(self):
        """Mock Supabase context functions."""
        with patch("src.services.handoff_summary.get_context_from_supabase") as mock_get, \
             patch("src.services.handoff_summary.save_context_to_supabase") as mock_save:
            mock_get.return_value = {
                HANDOFF_SUMMARY_SENT_KEY: {"sent": True}
            }
            mock_save.return_value = True
            yield {"get": mock_get, "save": mock_save}

    def test_clears_flag_successfully(self, mock_supabase):
        """Test that flag is cleared successfully."""
        result = clear_handoff_summary_flag("5511999999999")

        assert result is True
        mock_supabase["save"].assert_called_once()

        saved_context = mock_supabase["save"].call_args[0][1]
        assert saved_context[HANDOFF_SUMMARY_SENT_KEY]["sent"] is False

    def test_returns_true_when_flag_not_present(self, mock_supabase):
        """Test that True is returned when flag not present."""
        mock_supabase["get"].return_value = {}

        result = clear_handoff_summary_flag("5511999999999")

        assert result is True
        mock_supabase["save"].assert_not_called()

    def test_handles_invalid_phone(self, mock_supabase):
        """Test that invalid phone returns False."""
        result = clear_handoff_summary_flag("")

        assert result is False


class TestDuplicatePrevention:
    """Integration tests for duplicate prevention."""

    @pytest.fixture
    def mock_all_dependencies(self):
        """Mock all dependencies for full flow testing."""
        with patch("src.services.handoff_summary.get_context_from_supabase") as mock_get, \
             patch("src.services.handoff_summary.save_context_to_supabase") as mock_save, \
             patch("src.services.handoff_summary.send_internal_message_to_chatwoot", new_callable=AsyncMock) as mock_send:
            mock_get.return_value = {}
            mock_save.return_value = True
            mock_send.return_value = True
            yield {"get": mock_get, "save": mock_save, "send": mock_send}

    @pytest.mark.asyncio
    async def test_does_not_send_duplicate(self, mock_all_dependencies):
        """Test that duplicate summary is not sent."""
        # First call - should send
        mock_all_dependencies["get"].return_value = {}
        result1 = await send_handoff_summary(phone="5511999999999")

        # Second call - should skip
        mock_all_dependencies["get"].return_value = {
            HANDOFF_SUMMARY_SENT_KEY: {"sent": True}
        }
        result2 = await send_handoff_summary(phone="5511999999999")

        assert result1 is True
        assert result2 is False
        assert mock_all_dependencies["send"].call_count == 1


class TestErrorHandling:
    """Tests for error handling in handoff summary service."""

    @pytest.mark.asyncio
    async def test_error_does_not_propagate(self):
        """Test that errors in handoff do not propagate to caller."""
        with patch("src.services.handoff_summary.send_internal_message_to_chatwoot", new_callable=AsyncMock) as mock_send, \
             patch("src.services.handoff_summary.is_handoff_summary_sent", return_value=False), \
             patch("src.services.handoff_summary.normalize_phone", return_value="5511999999999"):
            mock_send.side_effect = Exception("Network error")

            # Should return False but not raise
            result = await send_handoff_summary(phone="5511999999999")

            assert result is False

    def test_generate_summary_handles_none_values(self):
        """Test that generate_summary handles None values gracefully."""
        # Should not raise
        summary = generate_handoff_summary(
            lead_data=None,
            orcamento_data=None,
            empresa_data=None,
        )

        assert "Novo Lead Quente" in summary
        assert NOT_INFORMED in summary
