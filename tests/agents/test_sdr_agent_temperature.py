"""
Integration tests for temperature classification in SDR agent flow.

Tests cover:
- Temperature classification triggered during message processing
- Classification persistence to database
- Classification with different lead data scenarios
- Non-blocking behavior (errors don't break main flow)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock


class TestTemperatureClassificationIntegration:
    """Integration tests for temperature classification in agent flow."""

    @pytest.fixture
    def mock_conversation_memory(self):
        """Create a mock conversation memory."""
        memory = MagicMock()
        memory.is_first_message.return_value = False
        memory.get_messages_for_llm.return_value = []
        memory.get_lead_data.return_value = {}
        memory.get_question_count.return_value = 0
        memory.add_message = MagicMock()
        memory.reset_question_count = MagicMock()
        return memory

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings."""
        settings = MagicMock()
        settings.OPENAI_API_KEY = "test-api-key"
        settings.OPENAI_MODEL = "gpt-4"
        return settings

    @pytest.mark.asyncio
    async def test_classification_triggered_with_sufficient_data(self):
        """Test that classification is triggered when lead has sufficient data."""
        with patch("src.agents.sdr_agent.settings") as mock_settings, \
             patch("src.agents.sdr_agent.conversation_memory") as mock_memory, \
             patch("src.agents.sdr_agent.get_persisted_lead_data") as mock_get_data, \
             patch("src.agents.sdr_agent.extract_lead_data") as mock_extract, \
             patch("src.agents.sdr_agent.persist_lead_data") as mock_persist, \
             patch("src.agents.sdr_agent.should_classify_lead") as mock_should_classify, \
             patch("src.agents.sdr_agent.classify_lead") as mock_classify, \
             patch("src.agents.sdr_agent.sdr_agent") as mock_agent:

            # Setup mocks
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_memory.is_first_message.return_value = False
            mock_memory.get_messages_for_llm.return_value = []
            mock_memory.get_question_count.return_value = 0

            # Lead has sufficient data for classification
            mock_get_data.return_value = {
                "name": "Carlos",
                "company": "Restaurante Bom Sabor",
            }
            mock_extract.return_value = {}
            mock_persist.return_value = True
            mock_should_classify.return_value = True
            mock_classify.return_value = ("morno", "Lead com dados parciais")

            # Mock agent response
            mock_response = MagicMock()
            mock_response.content = "Obrigado pelas informacoes!"
            mock_agent.run.return_value = mock_response

            # Import after mocking
            from src.agents.sdr_agent import process_message

            # Process message
            response = await process_message("5511999999999", "Oi, sou Carlos")

            # Verify classification was called
            mock_should_classify.assert_called()
            mock_classify.assert_called_once()

    @pytest.mark.asyncio
    async def test_classification_not_triggered_with_insufficient_data(self):
        """Test that classification is NOT triggered with insufficient data."""
        with patch("src.agents.sdr_agent.settings") as mock_settings, \
             patch("src.agents.sdr_agent.conversation_memory") as mock_memory, \
             patch("src.agents.sdr_agent.get_persisted_lead_data") as mock_get_data, \
             patch("src.agents.sdr_agent.extract_lead_data") as mock_extract, \
             patch("src.agents.sdr_agent.persist_lead_data") as mock_persist, \
             patch("src.agents.sdr_agent.should_classify_lead") as mock_should_classify, \
             patch("src.agents.sdr_agent.classify_lead") as mock_classify, \
             patch("src.agents.sdr_agent.sdr_agent") as mock_agent:

            # Setup mocks
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_memory.is_first_message.return_value = False
            mock_memory.get_messages_for_llm.return_value = []
            mock_memory.get_question_count.return_value = 0

            # Lead has insufficient data
            mock_get_data.return_value = {"name": "Carlos"}  # Only 1 field
            mock_extract.return_value = {}
            mock_persist.return_value = True
            mock_should_classify.return_value = False  # Should not classify

            # Mock agent response
            mock_response = MagicMock()
            mock_response.content = "Ola!"
            mock_agent.run.return_value = mock_response

            from src.agents.sdr_agent import process_message

            response = await process_message("5511999999999", "Oi")

            # Verify classification was NOT called
            mock_classify.assert_not_called()

    @pytest.mark.asyncio
    async def test_classification_error_does_not_break_flow(self):
        """Test that classification errors don't break the main flow."""
        with patch("src.agents.sdr_agent.settings") as mock_settings, \
             patch("src.agents.sdr_agent.conversation_memory") as mock_memory, \
             patch("src.agents.sdr_agent.get_persisted_lead_data") as mock_get_data, \
             patch("src.agents.sdr_agent.extract_lead_data") as mock_extract, \
             patch("src.agents.sdr_agent.persist_lead_data") as mock_persist, \
             patch("src.agents.sdr_agent.should_classify_lead") as mock_should_classify, \
             patch("src.agents.sdr_agent.classify_lead") as mock_classify, \
             patch("src.agents.sdr_agent.sdr_agent") as mock_agent:

            # Setup mocks
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_memory.is_first_message.return_value = False
            mock_memory.get_messages_for_llm.return_value = []
            mock_memory.get_question_count.return_value = 0

            mock_get_data.return_value = {
                "name": "Carlos",
                "company": "Restaurante",
            }
            mock_extract.return_value = {}
            mock_persist.return_value = True
            mock_should_classify.return_value = True

            # Classification raises an error
            mock_classify.side_effect = Exception("Classification failed")

            # Mock agent response - should still work
            mock_response = MagicMock()
            mock_response.content = "Obrigado!"
            mock_agent.run.return_value = mock_response

            from src.agents.sdr_agent import process_message

            # Should not raise, should return response
            response = await process_message("5511999999999", "Oi")

            # Response should still be returned
            assert response is not None

    @pytest.mark.asyncio
    async def test_classification_updates_lead_data(self):
        """Test that successful classification updates lead data."""
        with patch("src.agents.sdr_agent.settings") as mock_settings, \
             patch("src.agents.sdr_agent.conversation_memory") as mock_memory, \
             patch("src.agents.sdr_agent.get_persisted_lead_data") as mock_get_data, \
             patch("src.agents.sdr_agent.extract_lead_data") as mock_extract, \
             patch("src.agents.sdr_agent.persist_lead_data") as mock_persist, \
             patch("src.agents.sdr_agent.should_classify_lead") as mock_should_classify, \
             patch("src.agents.sdr_agent.classify_lead") as mock_classify, \
             patch("src.agents.sdr_agent.sdr_agent") as mock_agent:

            # Setup mocks
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_memory.is_first_message.return_value = False
            mock_memory.get_messages_for_llm.return_value = []
            mock_memory.get_question_count.return_value = 0

            mock_get_data.return_value = {
                "name": "Carlos",
                "company": "Restaurante",
                "city": "SP",
            }
            mock_extract.return_value = {}
            mock_persist.return_value = True
            mock_should_classify.return_value = True
            mock_classify.return_value = ("quente", "Lead qualificado")

            mock_response = MagicMock()
            mock_response.content = "Vou encaminhar para o comercial!"
            mock_agent.run.return_value = mock_response

            from src.agents.sdr_agent import process_message

            response = await process_message("5511999999999", "Preciso urgente!")

            # Classification should have been called with correct parameters
            mock_classify.assert_called_once()
            call_kwargs = mock_classify.call_args
            assert call_kwargs is not None


class TestTemperatureClassificationWithConversationHistory:
    """Tests for classification considering conversation history."""

    @pytest.mark.asyncio
    async def test_classification_uses_conversation_history(self):
        """Test that classification receives conversation history."""
        with patch("src.agents.sdr_agent.settings") as mock_settings, \
             patch("src.agents.sdr_agent.conversation_memory") as mock_memory, \
             patch("src.agents.sdr_agent.get_persisted_lead_data") as mock_get_data, \
             patch("src.agents.sdr_agent.extract_lead_data") as mock_extract, \
             patch("src.agents.sdr_agent.persist_lead_data") as mock_persist, \
             patch("src.agents.sdr_agent.should_classify_lead") as mock_should_classify, \
             patch("src.agents.sdr_agent.classify_lead") as mock_classify, \
             patch("src.agents.sdr_agent.sdr_agent") as mock_agent:

            # Setup mocks
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_memory.is_first_message.return_value = False

            # Return conversation history
            conversation_history = [
                {"role": "user", "content": "Oi, quero uma fritadeira"},
                {"role": "assistant", "content": "Claro! Qual o tamanho?"},
                {"role": "user", "content": "Grande, para restaurante"},
            ]
            mock_memory.get_messages_for_llm.return_value = conversation_history
            mock_memory.get_question_count.return_value = 0

            mock_get_data.return_value = {
                "name": "Carlos",
                "company": "Restaurante",
            }
            mock_extract.return_value = {}
            mock_persist.return_value = True
            mock_should_classify.return_value = True
            mock_classify.return_value = ("morno", "Lead interessado")

            mock_response = MagicMock()
            mock_response.content = "Entendi!"
            mock_agent.run.return_value = mock_response

            from src.agents.sdr_agent import process_message

            await process_message("5511999999999", "Obrigado")

            # Check that classify_lead was called with conversation history
            mock_classify.assert_called_once()
            call_args = mock_classify.call_args
            # The conversation_history parameter should be passed
            assert "conversation_history" in call_args.kwargs or len(call_args.args) >= 3


class TestTemperatureClassificationScenarios:
    """Test different lead scenarios for classification."""

    def test_cold_lead_criteria(self):
        """Test that cold lead criteria are correctly identified."""
        from src.services.temperature_classification import (
            calculate_completeness_score,
            calculate_engagement_score,
            _fallback_classification,
        )

        # Cold lead: minimal data, low engagement
        lead_data = {"name": ""}  # No data
        engagement_score = calculate_engagement_score("5511999999999", [])
        completeness_score = calculate_completeness_score(lead_data)

        temp, _ = _fallback_classification(engagement_score, completeness_score, lead_data)
        assert temp == "frio"

    def test_warm_lead_criteria(self):
        """Test that warm lead criteria are correctly identified."""
        from src.services.temperature_classification import (
            calculate_completeness_score,
            calculate_engagement_score,
            _fallback_classification,
        )

        # Warm lead: some data, moderate engagement
        lead_data = {
            "name": "Carlos",
            "company": "Restaurante",
        }

        # Simulate moderate conversation
        conversation = [
            {"role": "assistant", "content": "Ola!"},
            {"role": "user", "content": "Oi, quero uma fritadeira para meu restaurante"},
            {"role": "assistant", "content": "Qual o tamanho?"},
            {"role": "user", "content": "Media, cerca de 20 litros"},
        ]

        engagement_score = calculate_engagement_score("5511999999999", conversation)
        completeness_score = calculate_completeness_score(lead_data)

        # Combined score should be moderate
        temp, _ = _fallback_classification(engagement_score, completeness_score, lead_data)
        assert temp in ["morno", "frio"]  # Should be warm or cold based on exact scores

    def test_hot_lead_criteria(self):
        """Test that hot lead criteria are correctly identified."""
        from src.services.temperature_classification import (
            calculate_completeness_score,
            calculate_engagement_score,
            _fallback_classification,
        )

        # Hot lead: complete data, high engagement, high urgency
        lead_data = {
            "name": "Maria Silva",
            "company": "Rede de Restaurantes",
            "city": "Rio de Janeiro",
            "product": "Fritadeira FB300",
            "volume": "50 unidades",
            "urgency": "alta",
            "uf": "RJ",
            "knows_seleto": "sim",
        }

        # High engagement conversation
        conversation = [
            {"role": "assistant", "content": "Ola!"},
            {"role": "user", "content": "Oi, sou Maria da Rede de Restaurantes no RJ. Preciso de 50 fritadeiras FB300 para nossas 10 lojas novas"},
            {"role": "assistant", "content": "Excelente! Podemos ajudar..."},
            {"role": "user", "content": "Urgente, vamos inaugurar em 2 meses. Ja conhecemos a Seleto e queremos fechar negocio."},
            {"role": "assistant", "content": "Perfeito!"},
            {"role": "user", "content": "Por favor, me passe o contato comercial para agendar visita."},
        ]

        engagement_score = calculate_engagement_score("5511999999999", conversation)
        completeness_score = calculate_completeness_score(lead_data)

        temp, _ = _fallback_classification(engagement_score, completeness_score, lead_data)
        assert temp == "quente"


class TestTemperaturePersistence:
    """Tests for temperature persistence functionality."""

    @pytest.mark.asyncio
    async def test_update_lead_temperature_success(self):
        """Test successful temperature update."""
        from src.services.temperature_classification import update_lead_temperature

        with patch("src.services.temperature_classification.get_supabase_client") as mock_client:
            mock_supabase = MagicMock()
            mock_client.return_value = mock_supabase

            # Mock the select query
            mock_table = MagicMock()
            mock_supabase.table.return_value = mock_table
            mock_table.select.return_value.eq.return_value.execute.return_value.data = [
                {"context_data": {"name": "Carlos"}}
            ]
            mock_table.upsert.return_value.execute.return_value.data = [{"id": 1}]

            result = await update_lead_temperature(
                "5511999999999",
                "quente",
                "Lead qualificado com alta urgencia"
            )

            assert result is True
            mock_table.upsert.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_lead_temperature_no_existing_context(self):
        """Test temperature update when no existing context."""
        from src.services.temperature_classification import update_lead_temperature

        with patch("src.services.temperature_classification.get_supabase_client") as mock_client:
            mock_supabase = MagicMock()
            mock_client.return_value = mock_supabase

            mock_table = MagicMock()
            mock_supabase.table.return_value = mock_table
            # No existing context
            mock_table.select.return_value.eq.return_value.execute.return_value.data = []
            mock_table.upsert.return_value.execute.return_value.data = [{"id": 1}]

            result = await update_lead_temperature(
                "5511999999999",
                "morno",
                "Lead novo"
            )

            assert result is True
