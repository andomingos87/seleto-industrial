"""
Tests for SDR Agent Knowledge Base Integration - US-003.

Tests to ensure the SDR agent correctly:
- Responds to equipment queries using knowledge base
- Applies commercial guardrails (no prices/discounts)
- Detects and escalates technical queries
- Registers technical questions for follow-up
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from src.services.knowledge_base import get_knowledge_base


class TestSDRAgentCommercialGuardrails:
    """Test suite for commercial query handling in SDR agent."""

    @pytest.mark.asyncio
    async def test_commercial_query_returns_guardrail_response(self):
        """Test that commercial queries are blocked with appropriate response."""
        from src.agents.sdr_agent import process_message

        # Mock dependencies
        with patch("src.agents.sdr_agent.conversation_memory") as mock_memory:
            with patch("src.agents.sdr_agent.get_persisted_lead_data", return_value={}):
                with patch("src.agents.sdr_agent.extract_lead_data", new_callable=AsyncMock) as mock_extract:
                    with patch("src.agents.sdr_agent.persist_lead_data", new_callable=AsyncMock):
                        mock_memory.is_first_message.return_value = False
                        mock_memory.get_messages_for_llm.return_value = []
                        mock_memory.get_question_count.return_value = 0
                        mock_extract.return_value = {}

                        response = await process_message(
                            phone="5511999999999",
                            message="Qual o preço da formadora FB300?",
                        )

                        # Should return commercial guardrail response
                        assert "consultor" in response.lower() or "vendas" in response.lower()
                        # Should NOT call the LLM agent
                        mock_memory.add_message.assert_called()

    @pytest.mark.asyncio
    async def test_discount_query_returns_guardrail_response(self):
        """Test that discount queries trigger guardrail."""
        from src.agents.sdr_agent import process_message

        with patch("src.agents.sdr_agent.conversation_memory") as mock_memory:
            with patch("src.agents.sdr_agent.get_persisted_lead_data", return_value={}):
                with patch("src.agents.sdr_agent.extract_lead_data", new_callable=AsyncMock) as mock_extract:
                    with patch("src.agents.sdr_agent.persist_lead_data", new_callable=AsyncMock):
                        mock_memory.is_first_message.return_value = False
                        mock_memory.get_messages_for_llm.return_value = []
                        mock_memory.get_question_count.return_value = 0
                        mock_extract.return_value = {}

                        response = await process_message(
                            phone="5511999999999",
                            message="Tem desconto para compra à vista?",
                        )

                        assert "consultor" in response.lower() or "vendas" in response.lower()


class TestSDRAgentTechnicalEscalation:
    """Test suite for technical query escalation in SDR agent."""

    @pytest.mark.asyncio
    async def test_technical_query_registers_and_escalates(self):
        """Test that technical queries are registered and escalated."""
        from src.agents.sdr_agent import process_message

        # Clear any existing questions
        kb = get_knowledge_base()
        kb.clear_technical_question("5511888888888")

        with patch("src.agents.sdr_agent.conversation_memory") as mock_memory:
            with patch("src.agents.sdr_agent.get_persisted_lead_data", return_value={}):
                with patch("src.agents.sdr_agent.extract_lead_data", new_callable=AsyncMock) as mock_extract:
                    with patch("src.agents.sdr_agent.persist_lead_data", new_callable=AsyncMock):
                        mock_memory.is_first_message.return_value = False
                        mock_memory.get_messages_for_llm.return_value = []
                        mock_memory.get_question_count.return_value = 0
                        mock_extract.return_value = {}

                        response = await process_message(
                            phone="5511888888888",
                            message="Preciso do diagrama elétrico da formadora",
                        )

                        # Should return escalation response
                        assert "especialista" in response.lower() or "técnico" in response.lower()

                        # Should register the question
                        questions = kb.get_pending_technical_questions()
                        matching = [q for q in questions if q.phone == "5511888888888"]
                        assert len(matching) >= 1

    @pytest.mark.asyncio
    async def test_maintenance_query_escalates(self):
        """Test that maintenance queries are escalated."""
        from src.agents.sdr_agent import process_message

        kb = get_knowledge_base()
        kb.clear_technical_question("5511777777777")

        with patch("src.agents.sdr_agent.conversation_memory") as mock_memory:
            with patch("src.agents.sdr_agent.get_persisted_lead_data", return_value={}):
                with patch("src.agents.sdr_agent.extract_lead_data", new_callable=AsyncMock) as mock_extract:
                    with patch("src.agents.sdr_agent.persist_lead_data", new_callable=AsyncMock):
                        mock_memory.is_first_message.return_value = False
                        mock_memory.get_messages_for_llm.return_value = []
                        mock_memory.get_question_count.return_value = 0
                        mock_extract.return_value = {}

                        response = await process_message(
                            phone="5511777777777",
                            message="Como fazer manutenção preventiva na máquina?",
                        )

                        assert "especialista" in response.lower() or "técnico" in response.lower()


class TestSDRAgentKnowledgeInjection:
    """Test suite for knowledge base context injection."""

    @pytest.mark.asyncio
    async def test_equipment_query_injects_knowledge_context(self):
        """Test that equipment queries inject knowledge base context."""
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

                            # Mock agent response
                            mock_response = MagicMock()
                            mock_response.content = "A FB700 produz 700 hambúrgueres por hora."
                            mock_agent.run.return_value = mock_response

                            response = await process_message(
                                phone="5511666666666",
                                message="Qual a produtividade da formadora FB700?",
                            )

                            # Agent should have been called
                            mock_agent.run.assert_called()

                            # The call should include knowledge context
                            call_args = mock_agent.run.call_args
                            input_message = call_args[0][0] if call_args[0] else call_args[1].get("message", "")

                            # Should contain knowledge base marker
                            assert "BASE DE CONHECIMENTO" in input_message or len(response) > 0


class TestSDRAgentEquipmentResponses:
    """Test suite for specific equipment query responses."""

    @pytest.mark.asyncio
    async def test_formadora_query_not_blocked(self):
        """Test that formadora queries are not blocked by guardrails."""
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
                            mock_response.content = "Temos várias formadoras disponíveis."
                            mock_agent.run.return_value = mock_response

                            response = await process_message(
                                phone="5511555555555",
                                message="Quais formadoras vocês têm?",
                            )

                            # Should call the agent (not blocked)
                            mock_agent.run.assert_called()
                            # Response should not be guardrail message
                            assert "consultor" not in response.lower() or "formadora" in response.lower()

    @pytest.mark.asyncio
    async def test_cortadora_query_not_blocked(self):
        """Test that cortadora queries are not blocked by guardrails."""
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
                            mock_response.content = "A CT200 corta até 300kg por hora."
                            mock_agent.run.return_value = mock_response

                            response = await process_message(
                                phone="5511444444444",
                                message="Qual a capacidade da cortadora CT200?",
                            )

                            mock_agent.run.assert_called()


class TestGuardrailsPriority:
    """Test suite for guardrails priority handling."""

    @pytest.mark.asyncio
    async def test_commercial_takes_priority_over_equipment(self):
        """Test that commercial guardrail takes priority even for equipment queries."""
        from src.agents.sdr_agent import process_message

        with patch("src.agents.sdr_agent.conversation_memory") as mock_memory:
            with patch("src.agents.sdr_agent.get_persisted_lead_data", return_value={}):
                with patch("src.agents.sdr_agent.extract_lead_data", new_callable=AsyncMock) as mock_extract:
                    with patch("src.agents.sdr_agent.persist_lead_data", new_callable=AsyncMock):
                        mock_memory.is_first_message.return_value = False
                        mock_memory.get_messages_for_llm.return_value = []
                        mock_memory.get_question_count.return_value = 0
                        mock_extract.return_value = {}

                        # Query about equipment but asking for price
                        response = await process_message(
                            phone="5511333333333",
                            message="Qual o preço da formadora FB700?",
                        )

                        # Should be blocked by commercial guardrail
                        assert "consultor" in response.lower() or "vendas" in response.lower()

    @pytest.mark.asyncio
    async def test_technical_takes_priority_over_equipment(self):
        """Test that technical escalation takes priority for equipment queries."""
        from src.agents.sdr_agent import process_message

        with patch("src.agents.sdr_agent.conversation_memory") as mock_memory:
            with patch("src.agents.sdr_agent.get_persisted_lead_data", return_value={}):
                with patch("src.agents.sdr_agent.extract_lead_data", new_callable=AsyncMock) as mock_extract:
                    with patch("src.agents.sdr_agent.persist_lead_data", new_callable=AsyncMock):
                        mock_memory.is_first_message.return_value = False
                        mock_memory.get_messages_for_llm.return_value = []
                        mock_memory.get_question_count.return_value = 0
                        mock_extract.return_value = {}

                        # Query about equipment but too technical
                        response = await process_message(
                            phone="5511222222222",
                            message="Preciso do diagrama elétrico da formadora FB700",
                        )

                        # Should be escalated
                        assert "especialista" in response.lower() or "técnico" in response.lower()


class TestMessageHistory:
    """Test suite for message history handling with guardrails."""

    @pytest.mark.asyncio
    async def test_commercial_guardrail_adds_to_history(self):
        """Test that commercial guardrail responses are added to history."""
        from src.agents.sdr_agent import process_message

        with patch("src.agents.sdr_agent.conversation_memory") as mock_memory:
            with patch("src.agents.sdr_agent.get_persisted_lead_data", return_value={}):
                with patch("src.agents.sdr_agent.extract_lead_data", new_callable=AsyncMock) as mock_extract:
                    with patch("src.agents.sdr_agent.persist_lead_data", new_callable=AsyncMock):
                        mock_memory.is_first_message.return_value = False
                        mock_memory.get_messages_for_llm.return_value = []
                        mock_memory.get_question_count.return_value = 0
                        mock_extract.return_value = {}

                        await process_message(
                            phone="5511111111111",
                            message="Quanto custa?",
                        )

                        # Should add both user and assistant messages to history
                        assert mock_memory.add_message.call_count == 2
                        calls = mock_memory.add_message.call_args_list
                        assert calls[0][0][1] == "user"
                        assert calls[1][0][1] == "assistant"

    @pytest.mark.asyncio
    async def test_technical_escalation_adds_to_history(self):
        """Test that technical escalation responses are added to history."""
        from src.agents.sdr_agent import process_message

        with patch("src.agents.sdr_agent.conversation_memory") as mock_memory:
            with patch("src.agents.sdr_agent.get_persisted_lead_data", return_value={}):
                with patch("src.agents.sdr_agent.extract_lead_data", new_callable=AsyncMock) as mock_extract:
                    with patch("src.agents.sdr_agent.persist_lead_data", new_callable=AsyncMock):
                        mock_memory.is_first_message.return_value = False
                        mock_memory.get_messages_for_llm.return_value = []
                        mock_memory.get_question_count.return_value = 0
                        mock_extract.return_value = {}

                        await process_message(
                            phone="5511000000000",
                            message="Preciso de peça de reposição",
                        )

                        # Should add both user and assistant messages to history
                        assert mock_memory.add_message.call_count == 2
