"""
Tests for Piperun CRM synchronization service.

US-007: Tests for lead synchronization with Piperun CRM.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.services.piperun_sync import (
    build_deal_title,
    extract_ddd_from_phone,
    should_sync_to_piperun,
    sync_lead_to_piperun,
    PiperunSyncError,
    _get_next_step,
)


# ==================== Unit Tests ====================

class TestBuildDealTitle:
    """Tests for build_deal_title function."""

    def test_full_data(self):
        """Test with all fields provided."""
        title = build_deal_title(
            product="FBM100",
            city="São Paulo",
            uf="SP",
        )
        assert title == "Lead - FBM100 - São Paulo/SP"

    def test_product_only(self):
        """Test with product only."""
        title = build_deal_title(product="FB300")
        assert title == "Lead - FB300 - Brasil"

    def test_location_only(self):
        """Test with location only."""
        title = build_deal_title(city="Curitiba", uf="PR")
        assert title == "Lead - Interesse - Curitiba/PR"

    def test_no_data(self):
        """Test with no data."""
        title = build_deal_title()
        assert title == "Lead - Interesse - Brasil"

    def test_uf_only(self):
        """Test with UF only."""
        title = build_deal_title(uf="RJ")
        assert title == "Lead - Interesse - RJ"

    def test_normalizes_uf(self):
        """Test UF is normalized to uppercase."""
        title = build_deal_title(city="Belo Horizonte", uf="mg")
        assert "MG" in title


class TestExtractDddFromPhone:
    """Tests for extract_ddd_from_phone function."""

    def test_full_brazilian_number(self):
        """Test with full Brazilian number."""
        ddd = extract_ddd_from_phone("5511999999999")
        assert ddd == "11"

    def test_local_number_with_ddd(self):
        """Test with local number including DDD."""
        ddd = extract_ddd_from_phone("11999999999")
        assert ddd == "11"

    def test_empty_phone(self):
        """Test with empty phone."""
        ddd = extract_ddd_from_phone("")
        assert ddd == "XX"

    def test_none_phone(self):
        """Test with None phone."""
        ddd = extract_ddd_from_phone(None)
        assert ddd == "XX"

    def test_short_phone(self):
        """Test with too short phone number."""
        ddd = extract_ddd_from_phone("123")
        assert ddd == "XX"


class TestGetNextStep:
    """Tests for _get_next_step function."""

    def test_hot_lead(self):
        """Test next step for hot lead."""
        step = _get_next_step("Quente")
        assert "consultor" in step.lower() or "orçamento" in step.lower()

    def test_warm_lead(self):
        """Test next step for warm lead."""
        step = _get_next_step("Morno")
        assert "follow-up" in step.lower()

    def test_cold_lead(self):
        """Test next step for cold lead."""
        step = _get_next_step("Frio")
        assert "nutrição" in step.lower() or "catálogo" in step.lower()

    def test_unknown_temperature(self):
        """Test next step for unknown temperature."""
        step = _get_next_step("Desconhecido")
        assert "aguardando" in step.lower()

    def test_english_temperature(self):
        """Test with English temperature values."""
        assert "consultor" in _get_next_step("hot").lower()
        assert "follow-up" in _get_next_step("warm").lower()
        assert "nutrição" in _get_next_step("cold").lower()


class TestShouldSyncToPiperun:
    """Tests for should_sync_to_piperun function."""

    def test_hot_lead_always_syncs(self):
        """Test that hot leads always sync."""
        with patch("src.services.piperun_sync.piperun_client") as mock_client:
            mock_client.is_configured.return_value = True

            result = should_sync_to_piperun(
                lead_data={"name": "Test"},
                temperature="hot",
            )
            assert result is True

    def test_quente_lead_always_syncs(self):
        """Test that 'quente' leads always sync."""
        with patch("src.services.piperun_sync.piperun_client") as mock_client:
            mock_client.is_configured.return_value = True

            result = should_sync_to_piperun(
                lead_data={},
                temperature="quente",
            )
            assert result is True

    def test_warm_lead_with_good_data_syncs(self):
        """Test warm lead with name and product syncs."""
        with patch("src.services.piperun_sync.piperun_client") as mock_client:
            mock_client.is_configured.return_value = True

            result = should_sync_to_piperun(
                lead_data={
                    "name": "João",
                    "produto_interesse": "FBM100",
                },
                temperature="morno",
            )
            assert result is True

    def test_warm_lead_without_product_no_sync(self):
        """Test warm lead without product doesn't sync."""
        with patch("src.services.piperun_sync.piperun_client") as mock_client:
            mock_client.is_configured.return_value = True

            result = should_sync_to_piperun(
                lead_data={"name": "João"},
                temperature="warm",
            )
            assert result is False

    def test_cold_lead_no_sync(self):
        """Test cold leads don't sync automatically."""
        with patch("src.services.piperun_sync.piperun_client") as mock_client:
            mock_client.is_configured.return_value = True

            result = should_sync_to_piperun(
                lead_data={
                    "name": "Maria",
                    "produto_interesse": "FB300",
                },
                temperature="frio",
            )
            assert result is False

    def test_client_not_configured(self):
        """Test returns False when client not configured."""
        with patch("src.services.piperun_sync.piperun_client") as mock_client:
            mock_client.is_configured.return_value = False

            result = should_sync_to_piperun(
                lead_data={"name": "Test"},
                temperature="hot",
            )
            assert result is False


# ==================== Integration Tests ====================

class TestSyncLeadToPiperun:
    """Integration tests for sync_lead_to_piperun function."""

    @pytest.mark.asyncio
    async def test_sync_success_full_flow(self):
        """Test full sync flow with all steps successful."""
        mock_client = MagicMock()
        mock_client.is_configured.return_value = True
        mock_client.get_city_id = AsyncMock(return_value=12345)
        mock_client.get_company_by_cnpj = AsyncMock(return_value=None)
        mock_client.create_company = AsyncMock(return_value=100)
        mock_client.create_person = AsyncMock(return_value=200)
        mock_client.create_deal = AsyncMock(return_value=300)
        mock_client.create_note = AsyncMock(return_value=400)

        lead_data = {
            "id": "lead-123",
            "name": "João Silva",
            "empresa": "Empresa ABC",
            "city": "São Paulo",
            "uf": "SP",
            "cnpj": "12345678000190",
            "produto_interesse": "FBM100",
            "temperature": "quente",
        }

        with patch("src.services.piperun_sync.get_lead_by_phone", return_value=None):
            with patch("src.services.piperun_sync.get_orcamentos_by_lead", return_value=[]):
                deal_id = await sync_lead_to_piperun(
                    phone="5511999999999",
                    lead_data=lead_data,
                    conversation_summary="Cliente interessado em formadora",
                    client=mock_client,
                )

        assert deal_id == 300
        mock_client.get_city_id.assert_called_once()
        mock_client.create_company.assert_called_once()
        mock_client.create_person.assert_called_once()
        mock_client.create_deal.assert_called_once()
        mock_client.create_note.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_reuses_existing_company(self):
        """Test sync reuses existing company by CNPJ."""
        mock_client = MagicMock()
        mock_client.is_configured.return_value = True
        mock_client.get_city_id = AsyncMock(return_value=12345)
        mock_client.get_company_by_cnpj = AsyncMock(
            return_value={"id": 999, "name": "Existing Company"}
        )
        mock_client.create_person = AsyncMock(return_value=200)
        mock_client.create_deal = AsyncMock(return_value=300)
        mock_client.create_note = AsyncMock(return_value=400)

        lead_data = {
            "name": "Maria",
            "cnpj": "12345678000190",
            "city": "Rio",
            "uf": "RJ",
        }

        with patch("src.services.piperun_sync.get_lead_by_phone", return_value=None):
            with patch("src.services.piperun_sync.get_orcamentos_by_lead", return_value=[]):
                deal_id = await sync_lead_to_piperun(
                    phone="5521999999999",
                    lead_data=lead_data,
                    client=mock_client,
                )

        assert deal_id == 300
        # Should not create company since it exists
        mock_client.create_company.assert_not_called()
        # Person should be linked to existing company
        mock_client.create_person.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_idempotency_existing_deal(self):
        """Test sync returns existing deal ID when opportunity exists."""
        mock_client = MagicMock()
        mock_client.is_configured.return_value = True

        existing_orcamento = {
            "id": "orc-123",
            "oportunidade_pipe_id": "500",
        }

        lead_data = {"id": "lead-123", "name": "Test"}

        with patch("src.services.piperun_sync.get_lead_by_phone", return_value=lead_data):
            with patch(
                "src.services.piperun_sync.get_orcamentos_by_lead",
                return_value=[existing_orcamento],
            ):
                deal_id = await sync_lead_to_piperun(
                    phone="5511999999999",
                    client=mock_client,
                )

        assert deal_id == 500
        # Should not create anything
        mock_client.create_company.assert_not_called()
        mock_client.create_person.assert_not_called()
        mock_client.create_deal.assert_not_called()

    @pytest.mark.asyncio
    async def test_sync_force_create_ignores_existing(self):
        """Test force_create creates new deal even if one exists."""
        mock_client = MagicMock()
        mock_client.is_configured.return_value = True
        mock_client.get_city_id = AsyncMock(return_value=None)
        mock_client.get_company_by_cnpj = AsyncMock(return_value=None)
        mock_client.create_person = AsyncMock(return_value=200)
        mock_client.create_deal = AsyncMock(return_value=600)
        mock_client.create_note = AsyncMock(return_value=700)

        existing_orcamento = {
            "id": "orc-123",
            "oportunidade_pipe_id": "500",
        }

        lead_data = {"id": "lead-123", "name": "Test"}

        with patch("src.services.piperun_sync.get_lead_by_phone", return_value=lead_data):
            with patch(
                "src.services.piperun_sync.get_orcamentos_by_lead",
                return_value=[existing_orcamento],
            ):
                deal_id = await sync_lead_to_piperun(
                    phone="5511999999999",
                    lead_data=lead_data,
                    force_create=True,
                    client=mock_client,
                )

        assert deal_id == 600  # New deal, not existing 500
        mock_client.create_deal.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_client_not_configured(self):
        """Test sync returns None when client not configured."""
        mock_client = MagicMock()
        mock_client.is_configured.return_value = False

        result = await sync_lead_to_piperun(
            phone="5511999999999",
            lead_data={"name": "Test"},
            client=mock_client,
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_sync_invalid_phone_raises_error(self):
        """Test sync raises error for invalid phone."""
        mock_client = MagicMock()
        mock_client.is_configured.return_value = True

        with pytest.raises(PiperunSyncError) as exc_info:
            await sync_lead_to_piperun(
                phone="invalid",
                lead_data={"name": "Test"},
                client=mock_client,
            )

        assert "Invalid phone" in str(exc_info.value)
        assert exc_info.value.step == "validation"

    @pytest.mark.asyncio
    async def test_sync_deal_creation_failure_raises_error(self):
        """Test sync raises error when deal creation fails."""
        mock_client = MagicMock()
        mock_client.is_configured.return_value = True
        mock_client.get_city_id = AsyncMock(return_value=None)
        mock_client.get_company_by_cnpj = AsyncMock(return_value=None)
        mock_client.create_person = AsyncMock(return_value=200)
        mock_client.create_deal = AsyncMock(return_value=None)  # Failure

        lead_data = {"name": "Test"}

        with patch("src.services.piperun_sync.get_lead_by_phone", return_value=None):
            with patch("src.services.piperun_sync.get_orcamentos_by_lead", return_value=[]):
                with pytest.raises(PiperunSyncError) as exc_info:
                    await sync_lead_to_piperun(
                        phone="5511999999999",
                        lead_data=lead_data,
                        client=mock_client,
                    )

        assert exc_info.value.step == "create_deal"

    @pytest.mark.asyncio
    async def test_sync_updates_orcamento_with_deal_id(self):
        """Test sync updates orcamento with Piperun deal ID."""
        mock_client = MagicMock()
        mock_client.is_configured.return_value = True
        mock_client.get_city_id = AsyncMock(return_value=None)
        mock_client.create_person = AsyncMock(return_value=200)
        mock_client.create_deal = AsyncMock(return_value=300)
        mock_client.create_note = AsyncMock(return_value=400)

        existing_orcamento = {
            "id": "orc-123",
            "oportunidade_pipe_id": None,
        }

        lead_data = {"id": "lead-123", "name": "Test"}

        with patch("src.services.piperun_sync.get_lead_by_phone", return_value=lead_data):
            with patch(
                "src.services.piperun_sync.get_orcamentos_by_lead",
                return_value=[existing_orcamento],
            ):
                with patch(
                    "src.services.piperun_sync.update_orcamento"
                ) as mock_update:
                    await sync_lead_to_piperun(
                        phone="5511999999999",
                        lead_data=lead_data,
                        client=mock_client,
                    )

                    mock_update.assert_called_once_with(
                        orcamento_id="orc-123",
                        data={"oportunidade_pipe_id": "300"},
                    )
