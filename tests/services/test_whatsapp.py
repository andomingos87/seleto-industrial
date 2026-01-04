"""
Tests for WhatsApp service (Z-API integration)
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from src.services.whatsapp import WhatsAppService


class TestWhatsAppService:
    """Test suite for WhatsAppService"""

    def test_is_configured_with_all_variables(self):
        """Test is_configured() returns True when all Z-API variables are set"""
        with patch("src.services.whatsapp.settings") as mock_settings:
            mock_settings.ZAPI_INSTANCE_ID = "test_instance_id"
            mock_settings.ZAPI_INSTANCE_TOKEN = "test_instance_token"
            mock_settings.ZAPI_CLIENT_TOKEN = "test_client_token"
            
            service = WhatsAppService()
            assert service.is_configured() is True

    def test_is_configured_missing_instance_id(self):
        """Test is_configured() returns False when ZAPI_INSTANCE_ID is missing"""
        with patch("src.services.whatsapp.settings") as mock_settings:
            mock_settings.ZAPI_INSTANCE_ID = None
            mock_settings.ZAPI_INSTANCE_TOKEN = "test_token"
            mock_settings.ZAPI_CLIENT_TOKEN = "test_client"
            
            service = WhatsAppService()
            assert service.is_configured() is False

    def test_is_configured_missing_client_token(self):
        """Test is_configured() returns False when ZAPI_CLIENT_TOKEN is missing"""
        with patch("src.services.whatsapp.settings") as mock_settings:
            mock_settings.ZAPI_INSTANCE_ID = "test_id"
            mock_settings.ZAPI_INSTANCE_TOKEN = "test_token"
            mock_settings.ZAPI_CLIENT_TOKEN = None
            
            service = WhatsAppService()
            assert service.is_configured() is False

    @pytest.mark.asyncio
    async def test_send_message_raises_error_when_not_configured(self):
        """Test send_message() raises ValueError with clear message when not configured"""
        with patch("src.services.whatsapp.settings") as mock_settings:
            mock_settings.ZAPI_INSTANCE_ID = None
            mock_settings.ZAPI_INSTANCE_TOKEN = None
            mock_settings.ZAPI_CLIENT_TOKEN = None
            
            service = WhatsAppService()
            
            with pytest.raises(ValueError) as exc_info:
                await service.send_message("5511999999999", "test")
            
            assert "Z-API service not configured" in str(exc_info.value)
            assert "ZAPI_INSTANCE_ID" in str(exc_info.value)
            assert "ZAPI_INSTANCE_TOKEN" in str(exc_info.value)
            assert "ZAPI_CLIENT_TOKEN" in str(exc_info.value)

    def test_api_url_construction(self):
        """Test that Z-API URL is constructed correctly"""
        with patch("src.services.whatsapp.settings") as mock_settings:
            mock_settings.ZAPI_INSTANCE_ID = "test_instance_123"
            mock_settings.ZAPI_INSTANCE_TOKEN = "test_token_456"
            mock_settings.ZAPI_CLIENT_TOKEN = "test_client_789"
            
            service = WhatsAppService()
            expected_url = "https://api.z-api.io/instances/test_instance_123/token/test_token_456"
            assert service.api_url == expected_url

    @pytest.mark.asyncio
    async def test_send_message_uses_client_token_header(self):
        """Test that send_message uses Client-Token header for Z-API"""
        with patch("src.services.whatsapp.settings") as mock_settings:
            mock_settings.ZAPI_INSTANCE_ID = "test_id"
            mock_settings.ZAPI_INSTANCE_TOKEN = "test_token"
            mock_settings.ZAPI_CLIENT_TOKEN = "test_client_token"

            service = WhatsAppService()

            with patch("httpx.AsyncClient") as mock_client:
                # Create mock response with integer status_code (not AsyncMock)
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"success": True}
                mock_response.headers = {}

                # Create mock client instance with post method
                mock_client_instance = MagicMock()
                mock_post = AsyncMock(return_value=mock_response)
                mock_client_instance.post = mock_post

                # Configure AsyncClient as async context manager
                mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
                mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

                result = await service.send_message("5511999999999", "test message")

                # Verify Client-Token header was used
                assert mock_post.called
                call_kwargs = mock_post.call_args.kwargs
                headers = call_kwargs.get("headers", {})
                assert "Client-Token" in headers
                assert headers["Client-Token"] == "test_client_token"
                assert result is True

