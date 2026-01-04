"""
Tests for SDR Agent Upsell Integration - US-004.

Tests to ensure the SDR agent correctly:
- Detects FBM100 interest and suggests FB300
- Uses consultive tone in suggestions
- Does not repeat upsell suggestions
- Does not interrupt normal qualification flow
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from src.services.upsell import clear_upsell_history, get_upsell_suggestions, has_suggested_fb300


class TestSDRAgentUpsellDetection:
    """Test suite for upsell detection in SDR agent."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Clear upsell history before and after each test."""
        clear_upsell_history("5511999990001")
        clear_upsell_history("5511999990002")
        clear_upsell_history("5511999990003")
        yield
        clear_upsell_history("5511999990001")
        clear_upsell_history("5511999990002")
        clear_upsell_history("5511999990003")

    @pytest.mark.asyncio
    async def test_fbm100_mention_triggers_upsell_context(self):
        """Test that mentioning FBM100 triggers upsell context injection."""
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
                            mock_response.content = "A FBM100 é uma ótima opção!"
                            mock_agent.run.return_value = mock_response

                            phone = "5511999990001"
                            await process_message(
                                phone=phone,
                                message="Me fale sobre a FBM100",
                            )

                            # Verify agent was called with upsell context
                            mock_agent.run.assert_called()
                            call_args = mock_agent.run.call_args
                            input_message = call_args[0][0] if call_args[0] else ""

                            # Should contain upsell marker
                            assert "SUGESTÃO DE UPSELL" in input_message or "FB300" in input_message

    @pytest.mark.asyncio
    async def test_formadora_manual_triggers_upsell_context(self):
        """Test that 'formadora manual' triggers upsell context."""
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
                            mock_response.content = "Temos opções manuais e semi-automáticas."
                            mock_agent.run.return_value = mock_response

                            phone = "5511999990002"
                            await process_message(
                                phone=phone,
                                message="Preciso de uma formadora manual de hambúrguer",
                            )

                            # Verify upsell was registered
                            assert has_suggested_fb300(phone) is True

    @pytest.mark.asyncio
    async def test_non_fbm100_query_does_not_trigger_upsell(self):
        """Test that queries not about FBM100 do not trigger upsell."""
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

                            # Should NOT have upsell registered
                            assert has_suggested_fb300(phone) is False


class TestSDRAgentUpsellRepetition:
    """Test suite for upsell repetition prevention."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Clear upsell history before and after each test."""
        clear_upsell_history("5511999990010")
        yield
        clear_upsell_history("5511999990010")

    @pytest.mark.asyncio
    async def test_upsell_not_suggested_twice(self):
        """Test that FB300 is not suggested twice to the same lead."""
        from src.agents.sdr_agent import process_message

        phone = "5511999990010"

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

                            # First message about FBM100
                            await process_message(
                                phone=phone,
                                message="Me fale sobre a FBM100",
                            )

                            # Should have registered upsell
                            suggestions = get_upsell_suggestions(phone)
                            assert len(suggestions) == 1

                            # Second message about FBM100
                            await process_message(
                                phone=phone,
                                message="Mais detalhes da formadora manual",
                            )

                            # Should still have only one suggestion
                            suggestions = get_upsell_suggestions(phone)
                            assert len(suggestions) == 1


class TestSDRAgentUpsellIntegration:
    """Test suite for upsell integration with other features."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Clear upsell history before and after each test."""
        clear_upsell_history("5511999990020")
        clear_upsell_history("5511999990021")
        yield
        clear_upsell_history("5511999990020")
        clear_upsell_history("5511999990021")

    @pytest.mark.asyncio
    async def test_upsell_works_with_knowledge_base(self):
        """Test that upsell works alongside knowledge base injection."""
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

                            phone = "5511999990020"
                            await process_message(
                                phone=phone,
                                message="Qual a produtividade da FBM100?",
                            )

                            # Verify agent was called
                            mock_agent.run.assert_called()
                            call_args = mock_agent.run.call_args
                            input_message = call_args[0][0] if call_args[0] else ""

                            # Should contain both knowledge base and upsell context
                            assert "BASE DE CONHECIMENTO" in input_message
                            assert "FB300" in input_message or "UPSELL" in input_message

    @pytest.mark.asyncio
    async def test_commercial_guardrail_still_works_with_fbm100(self):
        """Test that commercial guardrail still blocks even with FBM100 mention."""
        from src.agents.sdr_agent import process_message

        with patch("src.agents.sdr_agent.conversation_memory") as mock_memory:
            with patch("src.agents.sdr_agent.get_persisted_lead_data", return_value={}):
                with patch("src.agents.sdr_agent.extract_lead_data", new_callable=AsyncMock) as mock_extract:
                    with patch("src.agents.sdr_agent.persist_lead_data", new_callable=AsyncMock):
                        mock_memory.is_first_message.return_value = False
                        mock_memory.get_messages_for_llm.return_value = []
                        mock_memory.get_question_count.return_value = 0
                        mock_extract.return_value = {}

                        phone = "5511999990021"
                        response = await process_message(
                            phone=phone,
                            message="Qual o preço da FBM100?",
                        )

                        # Should be blocked by commercial guardrail
                        assert "consultor" in response.lower() or "vendas" in response.lower()

                        # Should NOT have registered upsell (blocked before)
                        assert has_suggested_fb300(phone) is False


class TestUpsellContextContent:
    """Test suite for upsell context content verification."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Clear upsell history before and after each test."""
        clear_upsell_history("5511999990030")
        yield
        clear_upsell_history("5511999990030")

    @pytest.mark.asyncio
    async def test_upsell_context_contains_consultive_tone(self):
        """Test that upsell context has consultive tone markers."""
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

                            phone = "5511999990030"
                            await process_message(
                                phone=phone,
                                message="Quero a FBM100",
                            )

                            # Verify context content
                            call_args = mock_agent.run.call_args
                            input_message = call_args[0][0] if call_args[0] else ""

                            # Should have consultive markers
                            input_lower = input_message.lower()
                            has_consultive = "consultivo" in input_lower or "consultiva" in input_lower
                            has_no_pressure = "pressão" in input_lower or "pressione" in input_lower
                            assert has_consultive or has_no_pressure

    @pytest.mark.asyncio
    async def test_upsell_context_contains_productivity_comparison(self):
        """Test that upsell context contains productivity comparison."""
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
                            clear_upsell_history("5511999990031")

                            phone = "5511999990031"
                            await process_message(
                                phone=phone,
                                message="Quero saber da formadora manual",
                            )

                            call_args = mock_agent.run.call_args
                            input_message = call_args[0][0] if call_args[0] else ""

                            # Should have productivity numbers
                            has_fbm100_prod = "500-600" in input_message
                            has_fb300_prod = "300-350" in input_message
                            assert has_fbm100_prod and has_fb300_prod

                            # Cleanup
                            clear_upsell_history("5511999990031")


class TestUpsellFlowIntegrity:
    """Test suite to ensure upsell doesn't break normal flow."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Clear upsell history before and after each test."""
        clear_upsell_history("5511999990040")
        yield
        clear_upsell_history("5511999990040")

    @pytest.mark.asyncio
    async def test_upsell_does_not_block_agent_response(self):
        """Test that upsell context doesn't prevent agent from responding."""
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

                            expected_response = "A FBM100 é excelente para começar!"
                            mock_response = MagicMock()
                            mock_response.content = expected_response
                            mock_agent.run.return_value = mock_response

                            phone = "5511999990040"
                            response = await process_message(
                                phone=phone,
                                message="Me fale da FBM100",
                            )

                            # Agent should still respond normally
                            assert response == expected_response

    @pytest.mark.asyncio
    async def test_messages_added_to_history_with_upsell(self):
        """Test that messages are still added to history when upsell is triggered."""
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
                            clear_upsell_history("5511999990041")

                            phone = "5511999990041"
                            await process_message(
                                phone=phone,
                                message="Quero a FBM100",
                            )

                            # Should add both user and assistant messages
                            assert mock_memory.add_message.call_count == 2
                            calls = mock_memory.add_message.call_args_list
                            assert calls[0][0][1] == "user"
                            assert calls[1][0][1] == "assistant"

                            # Cleanup
                            clear_upsell_history("5511999990041")


class TestUpsellLogging:
    """Test suite for upsell logging verification."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Clear upsell history before and after each test."""
        clear_upsell_history("5511999990050")
        yield
        clear_upsell_history("5511999990050")

    @pytest.mark.asyncio
    async def test_upsell_logs_when_triggered(self):
        """Test that upsell logs an info message when triggered."""
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

                                phone = "5511999990050"
                                await process_message(
                                    phone=phone,
                                    message="Me fale da FBM100",
                                )

                                # Verify logging was called for upsell
                                info_calls = [
                                    call for call in mock_logger.info.call_args_list
                                    if "upsell" in str(call).lower() or "Upsell" in str(call)
                                ]
                                assert len(info_calls) >= 1
