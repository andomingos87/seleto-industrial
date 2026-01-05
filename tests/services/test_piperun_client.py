"""
Unit tests for Piperun CRM client.

Tests for TECH-015 through TECH-021:
- TECH-015: HTTP client with retry and authentication
- TECH-016: get_city_id with cache
- TECH-017: get_company_by_cnpj
- TECH-018: create_company
- TECH-019: create_person
- TECH-020: create_deal
- TECH-021: create_note and generate_note_template
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from src.services.piperun_client import (
    PiperunClient,
    PiperunError,
    PiperunAuthError,
    PiperunNotFoundError,
    PiperunValidationError,
    PiperunRateLimitError,
    generate_note_template,
)


# ==================== Fixtures ====================

@pytest.fixture
def piperun_client():
    """Create a configured Piperun client for testing."""
    return PiperunClient(
        api_url="https://api.pipe.run/v1",
        api_token="test-token-12345",
        pipeline_id=100848,
        stage_id=647558,
        origin_id=556735,
    )


@pytest.fixture
def unconfigured_client():
    """Create an unconfigured Piperun client for testing."""
    # Use explicit None to override settings defaults
    client = PiperunClient()
    client.api_url = None
    client.api_token = None
    return client


@pytest.fixture
def mock_response_success():
    """Create a mock successful response."""
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"data": [{"id": 123}]}
    response.headers = {}
    return response


@pytest.fixture
def mock_response_created():
    """Create a mock created response."""
    response = MagicMock()
    response.status_code = 201
    response.json.return_value = {"data": {"id": 456}}
    response.headers = {}
    return response


# ==================== TECH-015: Client Configuration Tests ====================

class TestPiperunClientConfiguration:
    """Tests for client configuration and initialization."""

    def test_client_initialization_with_values(self, piperun_client):
        """Test client initializes with provided values."""
        assert piperun_client.api_url == "https://api.pipe.run/v1"
        assert piperun_client.api_token == "test-token-12345"
        assert piperun_client.pipeline_id == 100848
        assert piperun_client.stage_id == 647558
        assert piperun_client.origin_id == 556735

    def test_client_initialization_defaults(self):
        """Test client uses defaults from settings when not provided."""
        with patch("src.services.piperun_client.settings") as mock_settings:
            mock_settings.PIPERUN_API_URL = "https://default.api.com"
            mock_settings.PIPERUN_API_TOKEN = "default-token"
            mock_settings.PIPERUN_PIPELINE_ID = 999
            mock_settings.PIPERUN_STAGE_ID = 888
            mock_settings.PIPERUN_ORIGIN_ID = 777

            client = PiperunClient()
            assert client.api_url == "https://default.api.com"
            assert client.api_token == "default-token"
            assert client.pipeline_id == 999
            assert client.stage_id == 888
            assert client.origin_id == 777

    def test_is_configured_true(self, piperun_client):
        """Test is_configured returns True when configured."""
        assert piperun_client.is_configured() is True

    def test_is_configured_false_no_url(self):
        """Test is_configured returns False when URL is missing."""
        client = PiperunClient(api_url="https://api.test.com", api_token="token")
        client.api_url = None  # Explicitly set to None after creation
        assert client.is_configured() is False

    def test_is_configured_false_no_token(self):
        """Test is_configured returns False when token is missing."""
        client = PiperunClient(api_url="https://api.test.com", api_token="token")
        client.api_token = None  # Explicitly set to None after creation
        assert client.is_configured() is False

    def test_headers_include_token(self, piperun_client):
        """Test headers include Token header."""
        headers = piperun_client._get_headers()
        assert "Token" in headers
        assert headers["Token"] == "test-token-12345"
        assert headers["Content-Type"] == "application/json"


# ==================== TECH-015: Request/Retry Tests ====================

class TestPiperunClientRequests:
    """Tests for HTTP requests and retry logic."""

    @pytest.mark.asyncio
    async def test_make_request_not_configured_raises_error(self, unconfigured_client):
        """Test _make_request raises ValueError when not configured."""
        with pytest.raises(ValueError) as exc_info:
            await unconfigured_client._make_request("GET", "/cities")
        assert "not configured" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_make_request_success(self, piperun_client, mock_response_success):
        """Test successful request returns data."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response_success)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            result = await piperun_client._make_request("GET", "/cities")

            assert result == {"data": [{"id": 123}]}
            mock_client.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_make_request_retry_on_500(self, piperun_client):
        """Test retry on server error (5xx)."""
        response_500 = MagicMock()
        response_500.status_code = 500
        response_500.headers = {}

        response_200 = MagicMock()
        response_200.status_code = 200
        response_200.json.return_value = {"data": []}
        response_200.headers = {}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(side_effect=[response_500, response_200])
            mock_client_class.return_value.__aenter__.return_value = mock_client

            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await piperun_client._make_request("GET", "/test")

            assert result == {"data": []}
            assert mock_client.request.call_count == 2

    @pytest.mark.asyncio
    async def test_make_request_no_retry_on_400(self, piperun_client):
        """Test no retry on client error (4xx)."""
        response_400 = MagicMock()
        response_400.status_code = 400
        response_400.text = "Bad Request"
        response_400.json.return_value = {"error": "validation_error"}
        response_400.headers = {}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=response_400)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            with pytest.raises(PiperunValidationError):
                await piperun_client._make_request("GET", "/test")

            # Should only be called once (no retry)
            assert mock_client.request.call_count == 1

    @pytest.mark.asyncio
    async def test_make_request_auth_error_401(self, piperun_client):
        """Test 401 raises PiperunAuthError."""
        response_401 = MagicMock()
        response_401.status_code = 401
        response_401.headers = {}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=response_401)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            with pytest.raises(PiperunAuthError) as exc_info:
                await piperun_client._make_request("GET", "/test")

            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_make_request_not_found_404(self, piperun_client):
        """Test 404 raises PiperunNotFoundError."""
        response_404 = MagicMock()
        response_404.status_code = 404
        response_404.headers = {}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=response_404)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            with pytest.raises(PiperunNotFoundError):
                await piperun_client._make_request("GET", "/test")

    @pytest.mark.asyncio
    async def test_make_request_rate_limit_429_retry(self, piperun_client):
        """Test retry on rate limit (429)."""
        response_429 = MagicMock()
        response_429.status_code = 429
        response_429.headers = {"Retry-After": "1"}

        response_200 = MagicMock()
        response_200.status_code = 200
        response_200.json.return_value = {"data": []}
        response_200.headers = {}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(side_effect=[response_429, response_200])
            mock_client_class.return_value.__aenter__.return_value = mock_client

            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await piperun_client._make_request("GET", "/test")

            assert result == {"data": []}
            assert mock_client.request.call_count == 2

    @pytest.mark.asyncio
    async def test_make_request_timeout_retry(self, piperun_client):
        """Test retry on timeout."""
        response_200 = MagicMock()
        response_200.status_code = 200
        response_200.json.return_value = {"data": []}
        response_200.headers = {}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(
                side_effect=[httpx.TimeoutException("timeout"), response_200]
            )
            mock_client_class.return_value.__aenter__.return_value = mock_client

            with patch("asyncio.sleep", new_callable=AsyncMock):
                result = await piperun_client._make_request("GET", "/test")

            assert result == {"data": []}
            assert mock_client.request.call_count == 2

    @pytest.mark.asyncio
    async def test_make_request_max_retries_exceeded(self, piperun_client):
        """Test error after max retries exceeded."""
        response_500 = MagicMock()
        response_500.status_code = 500
        response_500.headers = {}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=response_500)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            with patch("asyncio.sleep", new_callable=AsyncMock):
                with pytest.raises(PiperunError) as exc_info:
                    await piperun_client._make_request("GET", "/test")

            assert "500" in str(exc_info.value)
            assert mock_client.request.call_count == 3  # max_retries = 3


# ==================== TECH-016: City ID Tests ====================

class TestGetCityId:
    """Tests for get_city_id function."""

    @pytest.mark.asyncio
    async def test_get_city_id_success(self, piperun_client):
        """Test successful city ID lookup."""
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {"data": [{"id": 12345, "name": "São Paulo"}]}
        response.headers = {}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            city_id = await piperun_client.get_city_id("São Paulo", "SP")

            assert city_id == 12345

    @pytest.mark.asyncio
    async def test_get_city_id_not_found(self, piperun_client):
        """Test city not found returns None."""
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {"data": []}
        response.headers = {}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            city_id = await piperun_client.get_city_id("Cidade Inexistente", "XX")

            assert city_id is None

    @pytest.mark.asyncio
    async def test_get_city_id_normalizes_inputs(self, piperun_client):
        """Test city name and UF are normalized."""
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {"data": [{"id": 999}]}
        response.headers = {}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Test with lowercase/messy input
            city_id = await piperun_client.get_city_id("  são paulo  ", "sp")

            assert city_id == 999
            # Check that normalized values were passed
            call_args = mock_client.request.call_args
            assert call_args.kwargs["params"]["name"] == "São Paulo"
            assert call_args.kwargs["params"]["uf"] == "SP"

    @pytest.mark.asyncio
    async def test_get_city_id_invalid_inputs(self, piperun_client):
        """Test invalid inputs return None."""
        assert await piperun_client.get_city_id("", "SP") is None
        assert await piperun_client.get_city_id("São Paulo", "") is None
        assert await piperun_client.get_city_id(None, "SP") is None

    @pytest.mark.asyncio
    async def test_get_city_id_cache_hit(self, piperun_client):
        """Test cache hit prevents duplicate API calls."""
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {"data": [{"id": 123}]}
        response.headers = {}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # First call - should hit API
            city_id1 = await piperun_client.get_city_id("São Paulo", "SP")
            # Second call - should hit cache
            city_id2 = await piperun_client.get_city_id("São Paulo", "SP")

            assert city_id1 == city_id2 == 123
            assert mock_client.request.call_count == 1  # Only one API call

    @pytest.mark.asyncio
    async def test_get_city_id_cache_disabled(self, piperun_client):
        """Test cache can be disabled."""
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {"data": [{"id": 123}]}
        response.headers = {}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            piperun_client.disable_city_cache()

            # Both calls should hit API
            await piperun_client.get_city_id("São Paulo", "SP")
            await piperun_client.get_city_id("São Paulo", "SP")

            assert mock_client.request.call_count == 2


# ==================== TECH-017: Company by CNPJ Tests ====================

class TestGetCompanyByCnpj:
    """Tests for get_company_by_cnpj function."""

    @pytest.mark.asyncio
    async def test_get_company_by_cnpj_success(self, piperun_client):
        """Test successful company lookup by CNPJ."""
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {
            "data": [{"id": 789, "name": "Test Company", "cnpj": "12345678000190"}]
        }
        response.headers = {}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            company = await piperun_client.get_company_by_cnpj("12.345.678/0001-90")

            assert company is not None
            assert company["id"] == 789

    @pytest.mark.asyncio
    async def test_get_company_by_cnpj_not_found(self, piperun_client):
        """Test company not found returns None."""
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {"data": []}
        response.headers = {}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            company = await piperun_client.get_company_by_cnpj("99999999000199")

            assert company is None

    @pytest.mark.asyncio
    async def test_get_company_by_cnpj_normalizes_input(self, piperun_client):
        """Test CNPJ is normalized before lookup."""
        response = MagicMock()
        response.status_code = 200
        response.json.return_value = {"data": [{"id": 1}]}
        response.headers = {}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=response)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            # Pass formatted CNPJ
            await piperun_client.get_company_by_cnpj("12.345.678/0001-90")

            # Check normalized value was passed
            call_args = mock_client.request.call_args
            assert call_args.kwargs["params"]["cnpj"] == "12345678000190"

    @pytest.mark.asyncio
    async def test_get_company_by_cnpj_invalid_cnpj(self, piperun_client):
        """Test invalid CNPJ returns None."""
        assert await piperun_client.get_company_by_cnpj("") is None
        assert await piperun_client.get_company_by_cnpj("123") is None  # Too short
        assert await piperun_client.get_company_by_cnpj(None) is None


# ==================== TECH-018: Create Company Tests ====================

class TestCreateCompany:
    """Tests for create_company function."""

    @pytest.mark.asyncio
    async def test_create_company_success(self, piperun_client, mock_response_created):
        """Test successful company creation."""
        mock_response_created.json.return_value = {"data": {"id": 456, "name": "New Company"}}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response_created)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            company_id = await piperun_client.create_company(
                name="New Company",
                city_id=123,
                cnpj="12345678000190",
                website="https://example.com",
                email="company@example.com",
            )

            assert company_id == 456

    @pytest.mark.asyncio
    async def test_create_company_minimal(self, piperun_client, mock_response_created):
        """Test company creation with minimal data (name only)."""
        mock_response_created.json.return_value = {"data": {"id": 789}}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response_created)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            company_id = await piperun_client.create_company(name="Minimal Company")

            assert company_id == 789

    @pytest.mark.asyncio
    async def test_create_company_normalizes_cnpj(self, piperun_client, mock_response_created):
        """Test CNPJ is normalized before creation."""
        mock_response_created.json.return_value = {"data": {"id": 1}}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response_created)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            await piperun_client.create_company(
                name="Test",
                cnpj="12.345.678/0001-90",
            )

            call_args = mock_client.request.call_args
            assert call_args.kwargs["json"]["cnpj"] == "12345678000190"

    @pytest.mark.asyncio
    async def test_create_company_no_name_returns_none(self, piperun_client):
        """Test company creation fails without name."""
        company_id = await piperun_client.create_company(name="")
        assert company_id is None

        company_id = await piperun_client.create_company(name=None)
        assert company_id is None


# ==================== TECH-019: Create Person Tests ====================

class TestCreatePerson:
    """Tests for create_person function."""

    @pytest.mark.asyncio
    async def test_create_person_success(self, piperun_client, mock_response_created):
        """Test successful person creation."""
        mock_response_created.json.return_value = {"data": {"id": 111, "name": "John Doe"}}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response_created)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            person_id = await piperun_client.create_person(
                name="John Doe",
                phones=["11999999999", "1188888888"],
                emails=["john@example.com"],
                city_id=123,
                company_id=456,
            )

            assert person_id == 111

    @pytest.mark.asyncio
    async def test_create_person_normalizes_phones(self, piperun_client, mock_response_created):
        """Test phone numbers are normalized."""
        mock_response_created.json.return_value = {"data": {"id": 1}}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response_created)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            await piperun_client.create_person(
                name="Test",
                phones=["+55 (11) 99999-9999"],
            )

            call_args = mock_client.request.call_args
            phones = call_args.kwargs["json"]["phones"]
            assert phones[0]["phone"] == "5511999999999"

    @pytest.mark.asyncio
    async def test_create_person_normalizes_emails(self, piperun_client, mock_response_created):
        """Test emails are normalized to lowercase."""
        mock_response_created.json.return_value = {"data": {"id": 1}}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response_created)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            await piperun_client.create_person(
                name="Test",
                emails=["John@Example.COM"],
            )

            call_args = mock_client.request.call_args
            emails = call_args.kwargs["json"]["emails"]
            assert emails[0]["email"] == "john@example.com"

    @pytest.mark.asyncio
    async def test_create_person_no_name_returns_none(self, piperun_client):
        """Test person creation fails without name."""
        person_id = await piperun_client.create_person(name="")
        assert person_id is None


# ==================== TECH-020: Create Deal Tests ====================

class TestCreateDeal:
    """Tests for create_deal function."""

    @pytest.mark.asyncio
    async def test_create_deal_success(self, piperun_client, mock_response_created):
        """Test successful deal creation."""
        mock_response_created.json.return_value = {"data": {"id": 222, "title": "Lead - FBM100 - São Paulo/SP"}}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response_created)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            deal_id = await piperun_client.create_deal(
                title="Lead - FBM100 - São Paulo/SP",
                person_id=111,
                company_id=456,
            )

            assert deal_id == 222

    @pytest.mark.asyncio
    async def test_create_deal_uses_default_pipeline(self, piperun_client, mock_response_created):
        """Test deal uses default pipeline/stage from client config."""
        mock_response_created.json.return_value = {"data": {"id": 1}}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response_created)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            await piperun_client.create_deal(title="Test Deal")

            call_args = mock_client.request.call_args
            payload = call_args.kwargs["json"]
            assert payload["pipeline_id"] == 100848
            assert payload["stage_id"] == 647558
            assert payload["origin_id"] == 556735

    @pytest.mark.asyncio
    async def test_create_deal_no_pipeline_returns_none(self):
        """Test deal creation fails without pipeline/stage."""
        client = PiperunClient(
            api_url="https://api.test.com",
            api_token="token",
            pipeline_id=None,
            stage_id=None,
        )
        deal_id = await client.create_deal(title="Test")
        assert deal_id is None

    @pytest.mark.asyncio
    async def test_create_deal_no_title_returns_none(self, piperun_client):
        """Test deal creation fails without title."""
        deal_id = await piperun_client.create_deal(title="")
        assert deal_id is None


# ==================== TECH-021: Create Note Tests ====================

class TestCreateNote:
    """Tests for create_note function."""

    @pytest.mark.asyncio
    async def test_create_note_success(self, piperun_client, mock_response_created):
        """Test successful note creation."""
        mock_response_created.json.return_value = {"data": {"id": 333}}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.request = AsyncMock(return_value=mock_response_created)
            mock_client_class.return_value.__aenter__.return_value = mock_client

            note_id = await piperun_client.create_note(
                deal_id=222,
                content="Test note content",
            )

            assert note_id == 333

    @pytest.mark.asyncio
    async def test_create_note_no_deal_id_returns_none(self, piperun_client):
        """Test note creation fails without deal_id."""
        note_id = await piperun_client.create_note(deal_id=None, content="Test")
        assert note_id is None

    @pytest.mark.asyncio
    async def test_create_note_no_content_returns_none(self, piperun_client):
        """Test note creation fails without content."""
        note_id = await piperun_client.create_note(deal_id=222, content="")
        assert note_id is None


# ==================== TECH-021: Note Template Tests ====================

class TestGenerateNoteTemplate:
    """Tests for generate_note_template function."""

    def test_generate_note_template_all_fields(self):
        """Test template with all fields provided."""
        note = generate_note_template(
            resumo="Cliente interessado em formadora",
            empresa="Empresa ABC",
            contato="João Silva",
            cidade="São Paulo",
            ddd="11",
            segmento="Frigorífico",
            necessidade="Aumentar produção de hambúrgueres",
            equipamento="FBM100",
            classificacao="Quente",
            proximo_passo="Encaminhado para consultor",
        )

        assert "Cliente interessado em formadora" in note
        assert "Empresa ABC" in note
        assert "João Silva" in note
        assert "São Paulo" in note
        assert "(11)" in note
        assert "Frigorífico" in note
        assert "Aumentar produção" in note
        assert "FBM100" in note
        assert "Quente" in note
        assert "Encaminhado para consultor" in note

    def test_generate_note_template_defaults(self):
        """Test template with default values."""
        note = generate_note_template()

        # All fields should show "Não informado"
        assert note.count("Não informado") >= 8  # Most fields
        assert "(XX)" in note  # Default DDD

    def test_generate_note_template_partial_fields(self):
        """Test template with partial fields."""
        note = generate_note_template(
            resumo="Consulta sobre equipamentos",
            contato="Maria",
            classificacao="Morno",
        )

        assert "Consulta sobre equipamentos" in note
        assert "Maria" in note
        assert "Morno" in note
        assert "Empresa: Não informado" in note


# ==================== Cache Helper Tests ====================

class TestCacheHelpers:
    """Tests for cache helper methods."""

    def test_clear_city_cache(self, piperun_client):
        """Test cache can be cleared."""
        piperun_client._city_cache["test:key"] = 123
        piperun_client.clear_city_cache()
        assert len(piperun_client._city_cache) == 0

    def test_disable_enable_city_cache(self, piperun_client):
        """Test cache can be disabled and re-enabled."""
        assert piperun_client._city_cache_enabled is True

        piperun_client.disable_city_cache()
        assert piperun_client._city_cache_enabled is False

        piperun_client.enable_city_cache()
        assert piperun_client._city_cache_enabled is True


# ==================== Error Class Tests ====================

class TestErrorClasses:
    """Tests for custom error classes."""

    def test_piperun_error_with_status_code(self):
        """Test PiperunError with status code."""
        error = PiperunError("Test error", status_code=500)
        assert str(error) == "Test error"
        assert error.status_code == 500

    def test_piperun_error_with_response_data(self):
        """Test PiperunError with response data."""
        error = PiperunError(
            "Validation failed",
            status_code=400,
            response_data={"field": "name", "error": "required"},
        )
        assert error.response_data["field"] == "name"

    def test_piperun_auth_error(self):
        """Test PiperunAuthError inheritance."""
        error = PiperunAuthError("Auth failed", status_code=401)
        assert isinstance(error, PiperunError)
        assert error.status_code == 401

    def test_piperun_not_found_error(self):
        """Test PiperunNotFoundError inheritance."""
        error = PiperunNotFoundError("Not found", status_code=404)
        assert isinstance(error, PiperunError)

    def test_piperun_validation_error(self):
        """Test PiperunValidationError inheritance."""
        error = PiperunValidationError("Invalid data", status_code=422)
        assert isinstance(error, PiperunError)

    def test_piperun_rate_limit_error(self):
        """Test PiperunRateLimitError inheritance."""
        error = PiperunRateLimitError("Rate limited", status_code=429)
        assert isinstance(error, PiperunError)
