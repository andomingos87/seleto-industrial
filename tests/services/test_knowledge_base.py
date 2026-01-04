"""
Tests for Knowledge Base Service - US-003: Responder dúvidas usando base de conhecimento.

This module tests:
- Loading equipment knowledge files
- Searching the knowledge base
- Detecting commercial queries (guardrail)
- Detecting overly technical queries
- Registering technical questions for follow-up
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

import src.services.knowledge_base as kb_module
from src.services.knowledge_base import (
    KnowledgeBase,
    get_knowledge_base,
    search_knowledge,
    is_commercial_query,
    is_too_technical,
    register_technical_question,
    TechnicalQuestion,
)


class TestKnowledgeBaseLoading:
    """Test suite for knowledge base file loading."""

    def test_load_equipment_files_success(self):
        """Test that equipment files are loaded successfully."""
        kb = KnowledgeBase()
        kb.load_equipment_files()

        assert kb._loaded is True
        assert len(kb._knowledge_content) > 0

    def test_load_equipment_files_twice_skips_reload(self):
        """Test that loading twice doesn't reload files."""
        kb = KnowledgeBase()
        kb.load_equipment_files()
        original_content = kb._knowledge_content

        kb.load_equipment_files()  # Should skip

        assert kb._knowledge_content == original_content

    def test_load_equipment_files_directory_not_found(self):
        """Test handling of missing equipment directory."""
        kb = KnowledgeBase()

        with patch.object(Path, "exists", return_value=False):
            kb.load_equipment_files()

        # Should not raise, just log warning
        assert kb._loaded is False or kb._knowledge_content == ""

    def test_knowledge_content_includes_equipment_info(self):
        """Test that loaded content includes equipment information."""
        kb = KnowledgeBase()
        kb.load_equipment_files()

        # Check for key equipment mentions
        content_lower = kb._knowledge_content.lower()
        assert "fbm100" in content_lower or "formadora" in content_lower
        assert "ct200" in content_lower or "cortadora" in content_lower


class TestCommercialGuardrails:
    """Test suite for commercial query detection (guardrails)."""

    @pytest.mark.parametrize(
        "query",
        [
            "Qual o preço da formadora FB300?",
            "Quanto custa o equipamento?",
            "Qual o valor da máquina?",
            "Tem desconto para compra à vista?",
            "Quais as condições de pagamento?",
            "Qual o prazo de entrega?",
            "Como faço para comprar?",
            "Quero comprar uma formadora",
            "Pode fazer um orçamento?",
            "Tem promoção?",
            "Dá para parcelar?",
            "Quanto fica o frete?",
            "Pode negociar o preço?",
        ],
    )
    def test_commercial_query_detected(self, query: str):
        """Test that commercial queries are correctly detected."""
        kb = KnowledgeBase()
        assert kb.is_commercial_query(query) is True

    @pytest.mark.parametrize(
        "query",
        [
            "Qual a produtividade da FB700?",
            "A formadora é automática?",
            "Quais os modelos disponíveis?",
            "A máquina é em inox?",
            "Quantos hambúrgueres por hora?",
            "Tem cortadora de bifes?",
            "Como funciona a ensacadeira?",
        ],
    )
    def test_non_commercial_query_not_detected(self, query: str):
        """Test that non-commercial queries are not flagged."""
        kb = KnowledgeBase()
        assert kb.is_commercial_query(query) is False

    def test_get_commercial_response_content(self):
        """Test that commercial response is appropriate."""
        kb = KnowledgeBase()
        response = kb.get_commercial_response()

        assert "consultor" in response.lower() or "vendas" in response.lower()
        assert len(response) > 50  # Should be a substantial response


class TestTechnicalQueryDetection:
    """Test suite for overly technical query detection."""

    @pytest.mark.parametrize(
        "query",
        [
            "Preciso do diagrama elétrico da máquina",
            "Qual o esquema elétrico?",
            "Tem peça de reposição disponível?",
            "Como fazer manutenção preventiva?",
            "A máquina precisa de calibração?",
            "A máquina travou, o que fazer?",
            "Qual a pressão de ar necessária?",
            "Preciso de instalação elétrica especial?",
            "A máquina tem certificação ANVISA?",
            "Quero customizar a máquina",
            "Dá para integrar com meu sistema?",
            "A máquina não funciona, preciso de reparo",
        ],
    )
    def test_technical_query_detected(self, query: str):
        """Test that overly technical queries are correctly detected."""
        kb = KnowledgeBase()
        assert kb.is_too_technical(query) is True

    @pytest.mark.parametrize(
        "query",
        [
            "Qual a produtividade da FB700?",
            "A formadora é automática?",
            "Quais os modelos disponíveis?",
            "A máquina é em inox?",
            "Quantos hambúrgueres por hora?",
            "Tem cortadora de bifes?",
            "Como funciona a ensacadeira?",
            "Qual a capacidade da cuba?",
        ],
    )
    def test_non_technical_query_not_detected(self, query: str):
        """Test that simple product queries are not flagged as technical."""
        kb = KnowledgeBase()
        assert kb.is_too_technical(query) is False

    def test_get_technical_escalation_response_content(self):
        """Test that technical escalation response is appropriate."""
        kb = KnowledgeBase()
        response = kb.get_technical_escalation_response()

        assert "especialista" in response.lower() or "técnico" in response.lower()
        assert "contato" in response.lower()
        assert len(response) > 50


class TestTechnicalQuestionRegistration:
    """Test suite for technical question registration."""

    def setup_method(self):
        """Clear technical questions before each test."""
        kb_module._technical_questions.clear()

    def test_register_technical_question(self):
        """Test that technical questions are registered correctly."""
        kb = KnowledgeBase()
        kb.register_technical_question(
            phone="5511999999999",
            question="Preciso do diagrama elétrico",
            context="Lead interessado em FB700",
        )

        questions = kb.get_pending_technical_questions()
        assert len(questions) == 1
        assert questions[0].phone == "5511999999999"
        assert questions[0].question == "Preciso do diagrama elétrico"
        assert questions[0].context == "Lead interessado em FB700"
        assert questions[0].timestamp is not None

    def test_register_multiple_questions(self):
        """Test that multiple questions can be registered."""
        kb = KnowledgeBase()
        kb.register_technical_question("5511111111111", "Question 1")
        kb.register_technical_question("5522222222222", "Question 2")
        kb.register_technical_question("5511111111111", "Question 3")

        questions = kb.get_pending_technical_questions()
        assert len(questions) == 3

    def test_clear_technical_questions_by_phone(self):
        """Test clearing questions for a specific phone."""
        kb = KnowledgeBase()
        kb.register_technical_question("5511111111111", "Question 1")
        kb.register_technical_question("5522222222222", "Question 2")

        kb.clear_technical_question("5511111111111")

        questions = kb.get_pending_technical_questions()
        assert len(questions) == 1
        assert questions[0].phone == "5522222222222"


class TestEquipmentQueryDetection:
    """Test suite for equipment query detection."""

    @pytest.mark.parametrize(
        "query",
        [
            "Qual a produtividade da formadora?",
            "Vocês têm cortadora de carne?",
            "Quero saber sobre ensacadeira",
            "Informações sobre a linha automática",
            "Capacidade do misturador",
            "Quais equipamentos vocês vendem?",
            "Máquina de hambúrguer",
            "Produção de hambúrgueres",
        ],
    )
    def test_equipment_query_detected(self, query: str):
        """Test that equipment queries are correctly detected."""
        kb = KnowledgeBase()
        assert kb.is_equipment_query(query) is True

    @pytest.mark.parametrize(
        "query",
        [
            "Olá, bom dia!",
            "Obrigado pela informação",
            "Onde fica a empresa?",
            "Qual o horário de atendimento?",
        ],
    )
    def test_non_equipment_query_not_detected(self, query: str):
        """Test that general queries are not flagged as equipment queries."""
        kb = KnowledgeBase()
        assert kb.is_equipment_query(query) is False


class TestKnowledgeBaseSearch:
    """Test suite for knowledge base search functionality."""

    def test_search_formadora_returns_content(self):
        """Test searching for formadora returns relevant content."""
        kb = KnowledgeBase()
        kb.load_equipment_files()

        result = kb.search_knowledge_base("formadora de hambúrguer")
        assert len(result) > 0

    def test_search_cortadora_returns_content(self):
        """Test searching for cortadora returns relevant content."""
        kb = KnowledgeBase()
        kb.load_equipment_files()

        result = kb.search_knowledge_base("cortadora CT200")
        assert len(result) > 0

    def test_search_general_query_returns_overview(self):
        """Test that general query returns equipment overview."""
        kb = KnowledgeBase()
        kb.load_equipment_files()

        result = kb.search_knowledge_base("quais equipamentos vocês têm?")
        assert "formadora" in result.lower() or "Formadora" in result

    def test_get_general_overview_content(self):
        """Test that general overview includes all categories."""
        kb = KnowledgeBase()
        overview = kb._get_general_overview()

        assert "Formadora" in overview
        assert "Cortadora" in overview
        assert "Ensacadeira" in overview
        assert "Misturador" in overview
        assert "Linha" in overview


class TestGetEquipmentResponse:
    """Test suite for get_equipment_response method."""

    def test_commercial_query_returns_commercial_type(self):
        """Test that commercial queries return commercial response type."""
        kb = KnowledgeBase()
        kb.load_equipment_files()

        response_type, content = kb.get_equipment_response("Qual o preço?")
        assert response_type == "commercial"
        assert "consultor" in content.lower() or "vendas" in content.lower()

    def test_technical_query_returns_technical_type(self):
        """Test that technical queries return technical response type."""
        kb = KnowledgeBase()
        kb.load_equipment_files()

        response_type, content = kb.get_equipment_response("Preciso do diagrama elétrico")
        assert response_type == "technical"
        assert "especialista" in content.lower()

    def test_equipment_query_returns_knowledge_type(self):
        """Test that equipment queries return knowledge response type."""
        kb = KnowledgeBase()
        kb.load_equipment_files()

        response_type, content = kb.get_equipment_response("Qual a capacidade da formadora FB700?")
        assert response_type in ["knowledge", "general"]
        assert len(content) > 0


class TestConvenienceFunctions:
    """Test suite for module-level convenience functions."""

    def test_get_knowledge_base_singleton(self):
        """Test that get_knowledge_base returns singleton instance."""
        kb1 = get_knowledge_base()
        kb2 = get_knowledge_base()
        assert kb1 is kb2

    def test_search_knowledge_function(self):
        """Test the search_knowledge convenience function."""
        result = search_knowledge("formadora")
        assert len(result) > 0

    def test_is_commercial_query_function(self):
        """Test the is_commercial_query convenience function."""
        assert is_commercial_query("Qual o preço?") is True
        assert is_commercial_query("Qual a capacidade?") is False

    def test_is_too_technical_function(self):
        """Test the is_too_technical convenience function."""
        assert is_too_technical("diagrama elétrico") is True
        assert is_too_technical("capacidade da cuba") is False

    def test_register_technical_question_function(self):
        """Test the register_technical_question convenience function."""
        # Clear before test
        kb = get_knowledge_base()
        kb.clear_technical_question("5599999999999")

        register_technical_question("5599999999999", "Test question")

        questions = kb.get_pending_technical_questions()
        matching = [q for q in questions if q.phone == "5599999999999"]
        assert len(matching) >= 1


class TestSpecificEquipmentQueries:
    """Test suite for specific equipment model queries."""

    def test_query_fbm100(self):
        """Test query about FBM100 returns relevant info."""
        kb = KnowledgeBase()
        kb.load_equipment_files()

        result = kb.search_knowledge_base("FBM100")
        # Should contain FBM100 info or general formadora info
        assert len(result) > 0

    def test_query_se6000(self):
        """Test query about SE6000 returns relevant info."""
        kb = KnowledgeBase()
        kb.load_equipment_files()

        result = kb.search_knowledge_base("SE6000 produtividade")
        assert len(result) > 0

    def test_query_ct200(self):
        """Test query about CT200 returns relevant info."""
        kb = KnowledgeBase()
        kb.load_equipment_files()

        result = kb.search_knowledge_base("cortadora CT200")
        assert len(result) > 0

    def test_query_linha_epe1200(self):
        """Test query about EPE1200 returns relevant info."""
        kb = KnowledgeBase()
        kb.load_equipment_files()

        result = kb.search_knowledge_base("linha automática EPE1200")
        assert len(result) > 0
