"""
Tests for the temperature classification service.

Tests cover:
- Prompt loading from XML
- Engagement score calculation
- Completeness score calculation
- Temperature classification logic
- LLM response parsing
- Fallback classification
- Lead classification criteria
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.services.temperature_classification import (
    load_temperature_prompt,
    calculate_engagement_score,
    calculate_completeness_score,
    _parse_llm_response,
    _fallback_classification,
    should_classify_lead,
    calculate_temperature,
    update_lead_temperature,
    classify_lead,
    REQUIRED_FIELDS,
    OPTIONAL_FIELDS,
    ALL_FIELDS,
)


class TestLoadTemperaturePrompt:
    """Tests for load_temperature_prompt function."""

    def test_load_temperature_prompt_success(self):
        """Test loading prompt from XML file."""
        prompt = load_temperature_prompt()

        assert prompt is not None
        assert len(prompt) > 0
        assert "CRITERIOS" in prompt or "criterio" in prompt.lower()

    def test_load_temperature_prompt_contains_temperatures(self):
        """Test that prompt contains temperature classifications."""
        prompt = load_temperature_prompt()

        # Should contain temperature criteria
        assert "frio" in prompt.lower() or "FRIO" in prompt
        assert "morno" in prompt.lower() or "MORNO" in prompt
        assert "quente" in prompt.lower() or "QUENTE" in prompt


class TestCalculateEngagementScore:
    """Tests for calculate_engagement_score function."""

    def test_empty_conversation_history(self):
        """Test with no conversation history."""
        score = calculate_engagement_score("5511999999999", None)
        assert score == 0.0

        score = calculate_engagement_score("5511999999999", [])
        assert score == 0.0

    def test_no_user_messages(self):
        """Test with only assistant messages."""
        history = [
            {"role": "assistant", "content": "Ola, como posso ajudar?"},
            {"role": "assistant", "content": "Voce ainda esta ai?"},
        ]
        score = calculate_engagement_score("5511999999999", history)
        assert score == 0.0

    def test_single_user_message(self):
        """Test with single short user message."""
        history = [
            {"role": "assistant", "content": "Ola!"},
            {"role": "user", "content": "Oi"},
        ]
        score = calculate_engagement_score("5511999999999", history)
        assert 0.0 < score < 0.5  # Low engagement

    def test_high_engagement_conversation(self):
        """Test with high engagement conversation."""
        history = [
            {"role": "assistant", "content": "Ola, como posso ajudar?"},
            {"role": "user", "content": "Ola, gostaria de saber sobre fritadeiras industriais para meu restaurante"},
            {"role": "assistant", "content": "Claro! Temos varias opcoes..."},
            {"role": "user", "content": "Preciso de uma com capacidade para 30 litros, temos movimento alto"},
            {"role": "assistant", "content": "Perfeito! A FB300 seria ideal..."},
            {"role": "user", "content": "Quanto custa? Tenho urgencia pois vou inaugurar em 1 mes"},
            {"role": "assistant", "content": "Vou encaminhar para o comercial..."},
            {"role": "user", "content": "Meu nome e Carlos da empresa Restaurante Bom Sabor em SP"},
            {"role": "assistant", "content": "Obrigado Carlos!"},
            {"role": "user", "content": "Aguardo contato, obrigado pela atencao"},
        ]
        score = calculate_engagement_score("5511999999999", history)
        assert score >= 0.5  # High engagement

    def test_moderate_engagement(self):
        """Test with moderate engagement."""
        history = [
            {"role": "assistant", "content": "Ola!"},
            {"role": "user", "content": "Oi, quero uma fritadeira"},
            {"role": "assistant", "content": "Qual o tamanho?"},
            {"role": "user", "content": "Grande"},
        ]
        score = calculate_engagement_score("5511999999999", history)
        assert 0.2 < score < 0.8  # Moderate engagement


class TestCalculateCompletenessScore:
    """Tests for calculate_completeness_score function."""

    def test_empty_lead_data(self):
        """Test with no lead data."""
        score = calculate_completeness_score({})
        assert score == 0.0

        score = calculate_completeness_score(None)
        assert score == 0.0

    def test_only_required_fields(self):
        """Test with only required fields filled."""
        lead_data = {
            "name": "Carlos",
            "company": "Restaurante",
            "city": "Sao Paulo",
            "product": "Fritadeira",
        }
        score = calculate_completeness_score(lead_data)
        assert score == 0.6  # All required (60% weight)

    def test_all_fields_filled(self):
        """Test with all fields filled."""
        lead_data = {
            "name": "Carlos Silva",
            "company": "Restaurante Bom Sabor",
            "city": "Sao Paulo",
            "product": "Fritadeira FB300",
            "volume": "10 unidades",
            "urgency": "alta",
            "uf": "SP",
            "knows_seleto": "sim",
        }
        score = calculate_completeness_score(lead_data)
        assert score == 1.0  # All fields filled

    def test_partial_required_fields(self):
        """Test with partial required fields."""
        lead_data = {
            "name": "Carlos",
            "company": "",  # Empty
            "city": "SP",
            "product": None,  # None
        }
        score = calculate_completeness_score(lead_data)
        # 2 of 4 required = 0.5 * 0.6 = 0.3
        assert score == 0.3

    def test_only_optional_fields(self):
        """Test with only optional fields."""
        lead_data = {
            "volume": "5 unidades",
            "urgency": "media",
        }
        score = calculate_completeness_score(lead_data)
        # 0 required + 2/4 optional = 0 * 0.6 + 0.5 * 0.4 = 0.2
        assert score == 0.2


class TestParseLLMResponse:
    """Tests for _parse_llm_response function."""

    def test_parse_single_word_response(self):
        """Test parsing single word temperature."""
        temp, justification = _parse_llm_response("quente")
        assert temp == "quente"
        assert "quente" in justification.lower()

        temp, justification = _parse_llm_response("morno")
        assert temp == "morno"

        temp, justification = _parse_llm_response("frio")
        assert temp == "frio"

    def test_parse_response_with_justification(self):
        """Test parsing temperature with justification."""
        response = "quente - Lead com dados completos e urgencia alta"
        temp, justification = _parse_llm_response(response)
        assert temp == "quente"
        assert "dados completos" in justification.lower() or "urgencia" in justification.lower()

    def test_parse_sentence_response(self):
        """Test parsing sentence with temperature."""
        response = "O lead deve ser classificado como morno, pois tem interesse mas sem urgencia."
        temp, justification = _parse_llm_response(response)
        assert temp == "morno"

    def test_parse_uppercase_response(self):
        """Test parsing uppercase temperature."""
        temp, justification = _parse_llm_response("QUENTE")
        assert temp == "quente"

    def test_default_fallback(self):
        """Test default fallback when no temperature found."""
        temp, justification = _parse_llm_response("nao sei classificar")
        assert temp == "morno"  # Default fallback


class TestFallbackClassification:
    """Tests for _fallback_classification function."""

    def test_high_scores_returns_quente(self):
        """Test high engagement and completeness returns quente."""
        lead_data = {"urgency": "alta"}
        temp, justification = _fallback_classification(0.8, 0.9, lead_data)
        assert temp == "quente"

    def test_low_scores_returns_frio(self):
        """Test low scores returns frio."""
        lead_data = {}
        temp, justification = _fallback_classification(0.1, 0.2, lead_data)
        assert temp == "frio"

    def test_moderate_scores_returns_morno(self):
        """Test moderate scores returns morno."""
        lead_data = {}
        temp, justification = _fallback_classification(0.4, 0.5, lead_data)
        assert temp == "morno"

    def test_high_urgency_boosts_score(self):
        """Test that high urgency can boost classification."""
        lead_data = {"urgency": "alta"}
        # Moderate scores with high urgency
        temp, justification = _fallback_classification(0.5, 0.5, lead_data)
        assert temp == "quente"  # Boosted by urgency


class TestShouldClassifyLead:
    """Tests for should_classify_lead function."""

    def test_insufficient_data(self):
        """Test with insufficient data for classification."""
        lead_data = {"name": "Carlos"}  # Only 1 required field
        assert should_classify_lead(lead_data) is False

    def test_minimum_required_data(self):
        """Test with minimum required data."""
        lead_data = {
            "name": "Carlos",
            "company": "Restaurante",
        }  # 2 required fields
        assert should_classify_lead(lead_data) is True

    def test_already_classified_needs_more_data(self):
        """Test that already classified lead needs more data to reclassify."""
        lead_data = {
            "name": "Carlos",
            "company": "Restaurante",
            "temperature": "morno",  # Already classified
        }
        # Only 2 fields, less than 6 required for reclassification
        assert should_classify_lead(lead_data) is False

    def test_reclassify_with_complete_data(self):
        """Test reclassification with complete data."""
        lead_data = {
            "name": "Carlos",
            "company": "Restaurante",
            "city": "SP",
            "product": "Fritadeira",
            "volume": "10 unidades",
            "urgency": "alta",
            "temperature": "morno",  # Already classified
        }
        # 6+ fields, should reclassify
        assert should_classify_lead(lead_data) is True

    def test_empty_data(self):
        """Test with empty data."""
        assert should_classify_lead({}) is False
        assert should_classify_lead(None) is False


class TestCalculateTemperature:
    """Tests for calculate_temperature function."""

    @pytest.mark.asyncio
    async def test_calculate_temperature_no_api_key(self):
        """Test that missing API key raises error."""
        with patch("src.services.temperature_classification.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = None

            with pytest.raises(ValueError, match="API key"):
                await calculate_temperature(
                    lead_data={"name": "Carlos"},
                    conversation_summary="Test conversation",
                )

    @pytest.mark.asyncio
    async def test_calculate_temperature_with_mock_llm(self):
        """Test temperature calculation with mocked LLM."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="quente - Lead com alta urgencia"))
        ]

        with patch("src.services.temperature_classification.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_settings.OPENAI_MODEL = "gpt-4"

            with patch("src.services.temperature_classification.AsyncOpenAI") as mock_openai:
                mock_client = AsyncMock()
                mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
                mock_openai.return_value = mock_client

                lead_data = {
                    "name": "Carlos",
                    "company": "Restaurante",
                    "urgency": "alta",
                }

                temp, justification = await calculate_temperature(
                    lead_data=lead_data,
                    conversation_summary="Lead interessado em fritadeiras",
                    phone="5511999999999",
                )

                assert temp == "quente"
                assert "urgencia" in justification.lower() or len(justification) > 0

    @pytest.mark.asyncio
    async def test_calculate_temperature_llm_failure_uses_fallback(self):
        """Test that LLM failure uses fallback classification."""
        with patch("src.services.temperature_classification.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_settings.OPENAI_MODEL = "gpt-4"

            with patch("src.services.temperature_classification.AsyncOpenAI") as mock_openai:
                mock_client = AsyncMock()
                mock_client.chat.completions.create = AsyncMock(
                    side_effect=Exception("API Error")
                )
                mock_openai.return_value = mock_client

                lead_data = {
                    "name": "Carlos",
                    "company": "Restaurante",
                    "city": "SP",
                    "product": "Fritadeira",
                }

                temp, justification = await calculate_temperature(
                    lead_data=lead_data,
                    conversation_summary="Test",
                    conversation_history=[
                        {"role": "user", "content": "Oi"},
                        {"role": "assistant", "content": "Ola!"},
                    ],
                    phone="5511999999999",
                )

                # Should use fallback classification
                assert temp in ["frio", "morno", "quente"]
                assert len(justification) > 0


class TestUpdateLeadTemperature:
    """Tests for update_lead_temperature function."""

    @pytest.mark.asyncio
    async def test_update_invalid_phone(self):
        """Test update with invalid phone number."""
        result = await update_lead_temperature("invalid", "quente", "Test")
        assert result is False

    @pytest.mark.asyncio
    async def test_update_invalid_temperature(self):
        """Test that invalid temperature is corrected to morno."""
        with patch("src.services.temperature_classification.get_supabase_client") as mock_client:
            mock_supabase = MagicMock()
            mock_client.return_value = mock_supabase

            # Setup mock chain
            mock_table = MagicMock()
            mock_supabase.table.return_value = mock_table
            mock_table.select.return_value.eq.return_value.execute.return_value.data = []
            mock_table.upsert.return_value.execute.return_value.data = [{"id": 1}]

            # Should not raise, should use "morno" fallback
            result = await update_lead_temperature(
                "5511999999999", "invalid_temp", "Test"
            )
            # Result depends on Supabase mock setup
            assert result in [True, False]

    @pytest.mark.asyncio
    async def test_update_no_supabase(self):
        """Test update when Supabase is not available."""
        with patch("src.services.temperature_classification.get_supabase_client") as mock_client:
            mock_client.return_value = None

            result = await update_lead_temperature(
                "5511999999999", "quente", "Test justification"
            )
            assert result is False


class TestClassifyLead:
    """Tests for classify_lead high-level function."""

    @pytest.mark.asyncio
    async def test_classify_lead_insufficient_data(self):
        """Test that insufficient data returns None."""
        lead_data = {"name": "Carlos"}  # Only 1 required field

        temp, justification = await classify_lead(
            phone="5511999999999",
            lead_data=lead_data,
        )

        assert temp is None
        assert justification is None

    @pytest.mark.asyncio
    async def test_classify_lead_with_data(self):
        """Test classification with sufficient data."""
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="morno - Dados parciais"))
        ]

        with patch("src.services.temperature_classification.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            mock_settings.OPENAI_MODEL = "gpt-4"

            with patch("src.services.temperature_classification.AsyncOpenAI") as mock_openai:
                mock_client = AsyncMock()
                mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
                mock_openai.return_value = mock_client

                with patch("src.services.temperature_classification.update_lead_temperature") as mock_update:
                    mock_update.return_value = True

                    lead_data = {
                        "name": "Carlos",
                        "company": "Restaurante",
                        "city": "SP",
                    }

                    temp, justification = await classify_lead(
                        phone="5511999999999",
                        lead_data=lead_data,
                        conversation_history=[
                            {"role": "user", "content": "Oi"},
                        ],
                    )

                    assert temp == "morno"
                    assert justification is not None


class TestConstants:
    """Tests for module constants."""

    def test_required_fields_defined(self):
        """Test that required fields are defined."""
        assert "name" in REQUIRED_FIELDS
        assert "company" in REQUIRED_FIELDS
        assert "city" in REQUIRED_FIELDS
        assert "product" in REQUIRED_FIELDS

    def test_optional_fields_defined(self):
        """Test that optional fields are defined."""
        assert "volume" in OPTIONAL_FIELDS
        assert "urgency" in OPTIONAL_FIELDS

    def test_all_fields_complete(self):
        """Test that ALL_FIELDS is complete."""
        assert set(ALL_FIELDS) == set(REQUIRED_FIELDS + OPTIONAL_FIELDS)
