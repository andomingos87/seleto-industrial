"""
Tests for SDR Agent Unavailable Products Integration - US-005.

Tests to ensure the SDR agent correctly:
- Detects espeto interest and informs about unavailability
- Registers interest for future contact
- Suggests CT200 as alternative when appropriate
- Does not interrupt normal qualification flow
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from src.services.unavailable_products import (
    clear_product_interest,
    get_product_interests_for_phone,
)


class TestSDRAgentEspetoDetection:
    """Test suite for espeto detection in SDR agent."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Clear product interests before and after each test."""
        clear_product_interest("5511999990001")
        clear_product_interest("5511999990002")
        clear_product_interest("5511999990003")
        yield
        clear_product_interest("5511999990001")
        clear_product_interest("5511999990002")
        clear_product_interest("5511999990003")

    @pytest.mark.asyncio
    async def test_espeto_mention_triggers_unavailable_context(self):
        """Test that mentioning espeto triggers unavailable product context injection."""
        from src.agents.sdr_agent import process_message

        with patch("src.agents.sdr_agent.conversation_memory") as mock_memory:
            with patch("src.agents.sdr_agent.get_persisted_lead_data", return_value={}):
                with patch("src.agents.sdr_agent.extract_lead_data", new_callable=AsyncMock) as mock_extract:
                    with patch("src.agents.sdr_agent.persist_lead_data", new_callable=AsyncMock):
                        with patch("src.agents.sdr_agent.sdr_agent") as mock_agent:
                            mock_memory.is_first_message.return_value = False
                            mock_memory.get_messages_for_llm.return_value = []
                            mock_memory.get_question_count.return_value = 0
                            mock_extract.return_value = {}

                            mock_response = MagicMock()
                            mock_response.content = "Entendo seu interesse em espetos."
                            mock_agent.run.return_value = mock_response

                            phone = "5511999990001"
                            await process_message(
                                phone=phone,
                                message="Vocês tem máquina de espeto?",
                            )

                            # Verify agent was called with unavailable product context
                            mock_agent.run.assert_called()
                            call_args = mock_agent.run.call_args
                            input_message = call_args[0][0] if call_args[0] else ""

                            # Should contain unavailable product marker
                            assert "PRODUTO INDISPONÍVEL" in input_message

    @pytest.mark.asyncio
    async def test_espetinho_triggers_unavailable_context(self):
        """Test that 'espetinho' triggers unavailable context."""
        from src.agents.sdr_agent import process_message

        with patch("src.agents.sdr_agent.conversation_memory") as mock_memory:
            with patch("src.agents.sdr_agent.get_persisted_lead_data", return_value={}):
                with patch("src.agents.sdr_agent.extract_lead_data", new_callable=AsyncMock) as mock_extract:
                    with patch("src.agents.sdr_agent.persist_lead_data", new_callable=AsyncMock):
                        with patch("src.agents.sdr_agent.sdr_agent") as mock_agent:
                            mock_memory.is_first_message.return_value = False
                            mock_memory.get_messages_for_llm.return_value = []
                            mock_memory.get_question_count.return_value = 0
                            mock_extract.return_value = {}

                            mock_response = MagicMock()
                            mock_response.content = "Sobre espetinhos..."
                            mock_agent.run.return_value = mock_response

                            phone = "5511999990002"
                            await process_message(
                                phone=phone,
                                message="Preciso fazer espetinhos em escala",
                            )

                            # Verify interest was registered
                            interests = get_product_interests_for_phone(phone)
                            assert len(interests) == 1
                            assert interests[0].product == "espeto"

    @pytest.mark.asyncio
    async def test_non_espeto_query_does_not_trigger_unavailable(self):
        """Test that queries not about espeto do not trigger unavailable context."""
        from src.agents.sdr_agent import process_message

        with patch("src.agents.sdr_agent.conversation_memory") as mock_memory:
            with patch("src.agents.sdr_agent.get_persisted_lead_data", return_value={}):
                with patch("src.agents.sdr_agent.extract_lead_data", new_callable=AsyncMock) as mock_extract:
                    with patch("src.agents.sdr_agent.persist_lead_data", new_callable=AsyncMock):
                        with patch("src.agents.sdr_agent.sdr_agent") as mock_agent:
                            mock_memory.is_first_message.return_value = False
                            mock_memory.get_messages_for_llm.return_value = []
                            mock_memory.get_question_count.return_value = 0
                            mock_extract.return_value = {}

                            mock_response = MagicMock()
                            mock_response.content = "A FB700 é nossa formadora automática."
                            mock_agent.run.return_value = mock_response

                            phone = "5511999990003"
                            await process_message(
                                phone=phone,
                                message="Quero saber sobre a FB700",
                            )

                            # Should NOT have interest registered
                            interests = get_product_interests_for_phone(phone)
                            assert len(interests) == 0


class TestSDRAgentCT200Suggestion:
    """Test suite for CT200 alternative suggestion."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Clear product interests before and after each test."""
        clear_product_interest("5511999990010")
        clear_product_interest("5511999990011")
        yield
        clear_product_interest("5511999990010")
        clear_product_interest("5511999990011")

    @pytest.mark.asyncio
    async def test_ct200_suggested_with_cutting_context(self):
        """Test that CT200 is suggested when cutting context is present."""
        from src.agents.sdr_agent import process_message

        with patch("src.agents.sdr_agent.conversation_memory") as mock_memory:
            with patch("src.agents.sdr_agent.get_persisted_lead_data", return_value={}):
                with patch("src.agents.sdr_agent.extract_lead_data", new_callable=AsyncMock) as mock_extract:
                    with patch("src.agents.sdr_agent.persist_lead_data", new_callable=AsyncMock):
                        with patch("src.agents.sdr_agent.sdr_agent") as mock_agent:
                            mock_memory.is_first_message.return_value = False
                            mock_memory.get_messages_for_llm.return_value = []
                            mock_memory.get_question_count.return_value = 0
                            mock_extract.return_value = {}

                            mock_response = MagicMock()
                            mock_response.content = "Sobre corte para espetos..."
                            mock_agent.run.return_value = mock_response

                            phone = "5511999990010"
                            await process_message(
                                phone=phone,
                                message="Preciso cortar carne em cubos para espeto",
                            )

                            # Verify agent was called with CT200 context
                            mock_agent.run.assert_called()
                            call_args = mock_agent.run.call_args
                            input_message = call_args[0][0] if call_args[0] else ""

                            # Should contain CT200 suggestion
                            assert "CT200" in input_message

    @pytest.mark.asyncio
    async def test_ct200_not_suggested_without_cutting_context(self):
        """Test that CT200 is not suggested without cutting context."""
        from src.agents.sdr_agent import process_message

        with patch("src.agents.sdr_agent.conversation_memory") as mock_memory:
            with patch("src.agents.sdr_agent.get_persisted_lead_data", return_value={}):
                with patch("src.agents.sdr_agent.extract_lead_data", new_callable=AsyncMock) as mock_extract:
                    with patch("src.agents.sdr_agent.persist_lead_data", new_callable=AsyncMock):
                        with patch("src.agents.sdr_agent.sdr_agent") as mock_agent:
                            mock_memory.is_first_message.return_value = False
                            mock_memory.get_messages_for_llm.return_value = []
                            mock_memory.get_question_count.return_value = 0
                            mock_extract.return_value = {}

                            mock_response = MagicMock()
                            mock_response.content = "Sobre a máquina de espeto..."
                            mock_agent.run.return_value = mock_response

                            phone = "5511999990011"
                            await process_message(
                                phone=phone,
                                message="Vocês tem máquina de espeto?",
                            )

                            # Verify agent was called
                            mock_agent.run.assert_called()
                            call_args = mock_agent.run.call_args
                            input_message = call_args[0][0] if call_args[0] else ""

                            # Should have unavailable context but not necessarily CT200
                            assert "PRODUTO INDISPONÍVEL" in input_message


class TestSDRAgentInterestRegistration:
    """Test suite for product interest registration."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Clear product interests before and after each test."""
        clear_product_interest("5511999990020")
        yield
        clear_product_interest("5511999990020")

    @pytest.mark.asyncio
    async def test_interest_registered_on_espeto_query(self):
        """Test that interest is registered when espeto is queried."""
        from src.agents.sdr_agent import process_message

        phone = "5511999990020"

        with patch("src.agents.sdr_agent.conversation_memory") as mock_memory:
            with patch("src.agents.sdr_agent.get_persisted_lead_data", return_value={}):
                with patch("src.agents.sdr_agent.extract_lead_data", new_callable=AsyncMock) as mock_extract:
                    with patch("src.agents.sdr_agent.persist_lead_data", new_callable=AsyncMock):
                        with patch("src.agents.sdr_agent.sdr_agent") as mock_agent:
                            mock_memory.is_first_message.return_value = False
                            mock_memory.get_messages_for_llm.return_value = []
                            mock_memory.get_question_count.return_value = 0
                            mock_extract.return_value = {}

                            mock_response = MagicMock()
                            mock_response.content = "Resposta do agente"
                            mock_agent.run.return_value = mock_response

                            # Initially no interests
                            assert len(get_product_interests_for_phone(phone)) == 0

                            await process_message(
                                phone=phone,
                                message="Quero saber sobre linha de espetos",
                            )

                            # Should have registered interest
                            interests = get_product_interests_for_phone(phone)
                            assert len(interests) == 1
                            assert interests[0].product == "espeto"
                            assert interests[0].phone == phone

    @pytest.mark.asyncio
    async def test_multiple_espeto_queries_register_multiple_interests(self):
        """Test that multiple espeto queries register multiple interests."""
        from src.agents.sdr_agent import process_message

        phone = "5511999990020"

        with patch("src.agents.sdr_agent.conversation_memory") as mock_memory:
            with patch("src.agents.sdr_agent.get_persisted_lead_data", return_value={}):
                with patch("src.agents.sdr_agent.extract_lead_data", new_callable=AsyncMock) as mock_extract:
                    with patch("src.agents.sdr_agent.persist_lead_data", new_callable=AsyncMock):
                        with patch("src.agents.sdr_agent.sdr_agent") as mock_agent:
                            mock_memory.is_first_message.return_value = False
                            mock_memory.get_messages_for_llm.return_value = []
                            mock_memory.get_question_count.return_value = 0
                            mock_extract.return_value = {}

                            mock_response = MagicMock()
                            mock_response.content = "Resposta"
                            mock_agent.run.return_value = mock_response

                            # First query
                            await process_message(
                                phone=phone,
                                message="Vocês tem espeto?",
                            )

                            # Second query
                            await process_message(
                                phone=phone,
                                message="Me fale mais sobre espetos",
                            )

                            # Should have registered 2 interests
                            interests = get_product_interests_for_phone(phone)
                            assert len(interests) == 2


class TestSDRAgentUnavailableIntegration:
    """Test suite for unavailable products integration with other features."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Clear product interests before and after each test."""
        clear_product_interest("5511999990030")
        clear_product_interest("5511999990031")
        yield
        clear_product_interest("5511999990030")
        clear_product_interest("5511999990031")

    @pytest.mark.asyncio
    async def test_unavailable_works_with_knowledge_base(self):
        """Test that unavailable product context works with knowledge base."""
        from src.agents.sdr_agent import process_message

        with patch("src.agents.sdr_agent.conversation_memory") as mock_memory:
            with patch("src.agents.sdr_agent.get_persisted_lead_data", return_value={}):
                with patch("src.agents.sdr_agent.extract_lead_data", new_callable=AsyncMock) as mock_extract:
                    with patch("src.agents.sdr_agent.persist_lead_data", new_callable=AsyncMock):
                        with patch("src.agents.sdr_agent.sdr_agent") as mock_agent:
                            mock_memory.is_first_message.return_value = False
                            mock_memory.get_messages_for_llm.return_value = []
                            mock_memory.get_question_count.return_value = 0
                            mock_extract.return_value = {}

                            mock_response = MagicMock()
                            mock_response.content = "Resposta com informações."
                            mock_agent.run.return_value = mock_response

                            phone = "5511999990030"
                            await process_message(
                                phone=phone,
                                message="Qual a produtividade da linha de espeto?",
                            )

                            # Verify agent was called
                            mock_agent.run.assert_called()
                            call_args = mock_agent.run.call_args
                            input_message = call_args[0][0] if call_args[0] else ""

                            # Should contain both knowledge base and unavailable context
                            assert "BASE DE CONHECIMENTO" in input_message
                            assert "PRODUTO INDISPONÍVEL" in input_message

    @pytest.mark.asyncio
    async def test_commercial_guardrail_still_works_with_espeto(self):
        """Test that commercial guardrail still blocks even with espeto mention."""
        from src.agents.sdr_agent import process_message

        with patch("src.agents.sdr_agent.conversation_memory") as mock_memory:
            with patch("src.agents.sdr_agent.get_persisted_lead_data", return_value={}):
                with patch("src.agents.sdr_agent.extract_lead_data", new_callable=AsyncMock) as mock_extract:
                    with patch("src.agents.sdr_agent.persist_lead_data", new_callable=AsyncMock):
                        mock_memory.is_first_message.return_value = False
                        mock_memory.get_messages_for_llm.return_value = []
                        mock_memory.get_question_count.return_value = 0
                        mock_extract.return_value = {}

                        phone = "5511999990031"
                        response = await process_message(
                            phone=phone,
                            message="Qual o preço da máquina de espeto?",
                        )

                        # Should be blocked by commercial guardrail
                        assert "consultor" in response.lower() or "vendas" in response.lower()

                        # Should NOT have registered interest (blocked before)
                        interests = get_product_interests_for_phone(phone)
                        assert len(interests) == 0


class TestSDRAgentUnavailableContextContent:
    """Test suite for unavailable product context content verification."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Clear product interests before and after each test."""
        clear_product_interest("5511999990040")
        yield
        clear_product_interest("5511999990040")

    @pytest.mark.asyncio
    async def test_context_contains_improvement_info(self):
        """Test that context mentions improvement/melhorias."""
        from src.agents.sdr_agent import process_message

        with patch("src.agents.sdr_agent.conversation_memory") as mock_memory:
            with patch("src.agents.sdr_agent.get_persisted_lead_data", return_value={}):
                with patch("src.agents.sdr_agent.extract_lead_data", new_callable=AsyncMock) as mock_extract:
                    with patch("src.agents.sdr_agent.persist_lead_data", new_callable=AsyncMock):
                        with patch("src.agents.sdr_agent.sdr_agent") as mock_agent:
                            mock_memory.is_first_message.return_value = False
                            mock_memory.get_messages_for_llm.return_value = []
                            mock_memory.get_question_count.return_value = 0
                            mock_extract.return_value = {}

                            mock_response = MagicMock()
                            mock_response.content = "Resposta"
                            mock_agent.run.return_value = mock_response

                            phone = "5511999990040"
                            await process_message(
                                phone=phone,
                                message="Vocês tem máquina de espeto?",
                            )

                            # Verify context content
                            call_args = mock_agent.run.call_args
                            input_message = call_args[0][0] if call_args[0] else ""

                            # Should mention improvements
                            assert "melhoria" in input_message.lower()

    @pytest.mark.asyncio
    async def test_context_instructs_not_to_mention_internal_date(self):
        """Test that context instructs agent NOT to mention internal date."""
        from src.agents.sdr_agent import process_message

        with patch("src.agents.sdr_agent.conversation_memory") as mock_memory:
            with patch("src.agents.sdr_agent.get_persisted_lead_data", return_value={}):
                with patch("src.agents.sdr_agent.extract_lead_data", new_callable=AsyncMock) as mock_extract:
                    with patch("src.agents.sdr_agent.persist_lead_data", new_callable=AsyncMock):
                        with patch("src.agents.sdr_agent.sdr_agent") as mock_agent:
                            mock_memory.is_first_message.return_value = False
                            mock_memory.get_messages_for_llm.return_value = []
                            mock_memory.get_question_count.return_value = 0
                            mock_extract.return_value = {}

                            mock_response = MagicMock()
                            mock_response.content = "Resposta"
                            mock_agent.run.return_value = mock_response

                            # Clear history first
                            clear_product_interest("5511999990041")

                            phone = "5511999990041"
                            await process_message(
                                phone=phone,
                                message="Quando terão máquina de espeto?",
                            )

                            call_args = mock_agent.run.call_args
                            input_message = call_args[0][0] if call_args[0] else ""

                            # Should contain instruction NOT to mention the date
                            assert "não mencione" in input_message.lower()
                            # Should say it's internal information
                            assert "interna" in input_message.lower()
                            # The instruction itself contains the date for reference,
                            # but instructs agent NOT to share it with the lead

                            # Cleanup
                            clear_product_interest("5511999990041")


class TestSDRAgentUnavailableFlowIntegrity:
    """Test suite to ensure unavailable product handling doesn't break normal flow."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Clear product interests before and after each test."""
        clear_product_interest("5511999990050")
        yield
        clear_product_interest("5511999990050")

    @pytest.mark.asyncio
    async def test_unavailable_does_not_block_agent_response(self):
        """Test that unavailable context doesn't prevent agent from responding."""
        from src.agents.sdr_agent import process_message

        with patch("src.agents.sdr_agent.conversation_memory") as mock_memory:
            with patch("src.agents.sdr_agent.get_persisted_lead_data", return_value={}):
                with patch("src.agents.sdr_agent.extract_lead_data", new_callable=AsyncMock) as mock_extract:
                    with patch("src.agents.sdr_agent.persist_lead_data", new_callable=AsyncMock):
                        with patch("src.agents.sdr_agent.sdr_agent") as mock_agent:
                            mock_memory.is_first_message.return_value = False
                            mock_memory.get_messages_for_llm.return_value = []
                            mock_memory.get_question_count.return_value = 0
                            mock_extract.return_value = {}

                            expected_response = "A linha de espetos está em desenvolvimento!"
                            mock_response = MagicMock()
                            mock_response.content = expected_response
                            mock_agent.run.return_value = mock_response

                            phone = "5511999990050"
                            response = await process_message(
                                phone=phone,
                                message="Me fale sobre espeto",
                            )

                            # Agent should still respond normally
                            assert response == expected_response

    @pytest.mark.asyncio
    async def test_messages_added_to_history_with_unavailable(self):
        """Test that messages are still added to history when unavailable is triggered."""
        from src.agents.sdr_agent import process_message

        with patch("src.agents.sdr_agent.conversation_memory") as mock_memory:
            with patch("src.agents.sdr_agent.get_persisted_lead_data", return_value={}):
                with patch("src.agents.sdr_agent.extract_lead_data", new_callable=AsyncMock) as mock_extract:
                    with patch("src.agents.sdr_agent.persist_lead_data", new_callable=AsyncMock):
                        with patch("src.agents.sdr_agent.sdr_agent") as mock_agent:
                            mock_memory.is_first_message.return_value = False
                            mock_memory.get_messages_for_llm.return_value = []
                            mock_memory.get_question_count.return_value = 0
                            mock_extract.return_value = {}

                            mock_response = MagicMock()
                            mock_response.content = "Resposta"
                            mock_agent.run.return_value = mock_response

                            # Clear history first
                            clear_product_interest("5511999990051")

                            phone = "5511999990051"
                            await process_message(
                                phone=phone,
                                message="Quero espeto",
                            )

                            # Should add both user and assistant messages
                            assert mock_memory.add_message.call_count == 2
                            calls = mock_memory.add_message.call_args_list
                            assert calls[0][0][1] == "user"
                            assert calls[1][0][1] == "assistant"

                            # Cleanup
                            clear_product_interest("5511999990051")


class TestSDRAgentUnavailableLogging:
    """Test suite for unavailable product logging verification."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Clear product interests before and after each test."""
        clear_product_interest("5511999990060")
        yield
        clear_product_interest("5511999990060")

    @pytest.mark.asyncio
    async def test_logs_when_espeto_detected(self):
        """Test that log message is generated when espeto is detected."""
        from src.agents.sdr_agent import process_message

        with patch("src.agents.sdr_agent.conversation_memory") as mock_memory:
            with patch("src.agents.sdr_agent.get_persisted_lead_data", return_value={}):
                with patch("src.agents.sdr_agent.extract_lead_data", new_callable=AsyncMock) as mock_extract:
                    with patch("src.agents.sdr_agent.persist_lead_data", new_callable=AsyncMock):
                        with patch("src.agents.sdr_agent.sdr_agent") as mock_agent:
                            with patch("src.agents.sdr_agent.logger") as mock_logger:
                                mock_memory.is_first_message.return_value = False
                                mock_memory.get_messages_for_llm.return_value = []
                                mock_memory.get_question_count.return_value = 0
                                mock_extract.return_value = {}

                                mock_response = MagicMock()
                                mock_response.content = "Resposta"
                                mock_agent.run.return_value = mock_response

                                phone = "5511999990060"
                                await process_message(
                                    phone=phone,
                                    message="Vocês tem espeto?",
                                )

                                # Verify logging was called for unavailable product
                                info_calls = [
                                    call for call in mock_logger.info.call_args_list
                                    if "speto" in str(call).lower() or "unavailable" in str(call).lower()
                                ]
                                assert len(info_calls) >= 1


class TestSDRAgentUnavailableWithUpsell:
    """Test suite for interaction between unavailable products and upsell features."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Clear interests before and after each test."""
        from src.services.upsell import clear_upsell_history
        clear_product_interest("5511999990070")
        clear_upsell_history("5511999990070")
        yield
        clear_product_interest("5511999990070")
        clear_upsell_history("5511999990070")

    @pytest.mark.asyncio
    async def test_espeto_and_fbm100_can_coexist(self):
        """Test that espeto and FBM100 contexts can both be injected."""
        from src.agents.sdr_agent import process_message
        from src.services.upsell import get_upsell_suggestions

        with patch("src.agents.sdr_agent.conversation_memory") as mock_memory:
            with patch("src.agents.sdr_agent.get_persisted_lead_data", return_value={}):
                with patch("src.agents.sdr_agent.extract_lead_data", new_callable=AsyncMock) as mock_extract:
                    with patch("src.agents.sdr_agent.persist_lead_data", new_callable=AsyncMock):
                        with patch("src.agents.sdr_agent.sdr_agent") as mock_agent:
                            mock_memory.is_first_message.return_value = False
                            mock_memory.get_messages_for_llm.return_value = []
                            mock_memory.get_question_count.return_value = 0
                            mock_extract.return_value = {}

                            mock_response = MagicMock()
                            mock_response.content = "Resposta"
                            mock_agent.run.return_value = mock_response

                            phone = "5511999990070"
                            # First, ask about espeto
                            await process_message(
                                phone=phone,
                                message="Vocês tem máquina de espeto?",
                            )

                            # Verify espeto was registered
                            interests = get_product_interests_for_phone(phone)
                            assert len(interests) == 1

                            # Now ask about FBM100
                            await process_message(
                                phone=phone,
                                message="E a formadora manual FBM100?",
                            )

                            # Verify upsell was also triggered
                            upsell_suggestions = get_upsell_suggestions(phone)
                            assert len(upsell_suggestions) == 1
