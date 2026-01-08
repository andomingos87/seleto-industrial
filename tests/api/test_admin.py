"""
Tests for Admin Panel API endpoints.

Tests cover:
- System status endpoint
- Agent control endpoints (pause/resume)
- Business hours configuration
- Leads listing and details
- Conversation history
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestStatusEndpoint:
    """Tests for GET /api/admin/status."""

    def test_get_status_success(self, client):
        """Test successful status retrieval."""
        response = client.get("/api/admin/status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "timestamp" in data
        assert "agent_status" in data
        assert "integrations" in data
        assert isinstance(data["integrations"], dict)

    def test_status_contains_all_integrations(self, client):
        """Test that status contains all expected integrations."""
        response = client.get("/api/admin/status")
        
        assert response.status_code == 200
        data = response.json()
        
        expected_integrations = ["whatsapp", "supabase", "openai", "piperun", "chatwoot"]
        for integration in expected_integrations:
            assert integration in data["integrations"]

    def test_integration_status_format(self, client):
        """Test that each integration has correct status format."""
        response = client.get("/api/admin/status")
        
        assert response.status_code == 200
        data = response.json()
        
        for name, status in data["integrations"].items():
            assert "status" in status
            assert status["status"] in ["ok", "error", "warning"]


class TestAgentControlEndpoints:
    """Tests for agent control endpoints."""

    def test_get_agent_status(self, client):
        """Test GET /api/admin/agent/status."""
        response = client.get("/api/admin/agent/status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "paused_phones" in data
        assert "total_paused" in data
        assert isinstance(data["paused_phones"], list)
        assert isinstance(data["total_paused"], int)

    def test_pause_agent_without_phone(self, client):
        """Test pause without phone returns error (global pause not implemented)."""
        response = client.post("/api/admin/agent/pause", json={})
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is False
        assert "Global pause not implemented" in data["message"]

    @patch("src.api.routes.admin.pause_agent")
    def test_pause_agent_with_phone(self, mock_pause, client):
        """Test pause with specific phone number."""
        mock_pause.return_value = True
        
        response = client.post(
            "/api/admin/agent/pause",
            json={"phone": "5511999999999"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "5511999999999" in data["message"]
        mock_pause.assert_called_once()

    def test_resume_agent_without_phone(self, client):
        """Test resume without phone returns error (global resume not implemented)."""
        response = client.post("/api/admin/agent/resume", json={})
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is False
        assert "Global resume not implemented" in data["message"]

    @patch("src.api.routes.admin.resume_agent")
    def test_resume_agent_with_phone(self, mock_resume, client):
        """Test resume with specific phone number."""
        mock_resume.return_value = True
        
        response = client.post(
            "/api/admin/agent/resume",
            json={"phone": "5511999999999"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "5511999999999" in data["message"]
        mock_resume.assert_called_once()

    @patch("src.api.routes.admin.load_system_prompt_from_xml")
    @patch("src.api.routes.admin.get_system_prompt_path")
    def test_reload_prompt_success(self, mock_path, mock_load, client):
        """Test successful prompt reload."""
        mock_path.return_value = "/path/to/prompt.xml"
        mock_load.return_value = "System prompt content"
        
        response = client.post("/api/admin/agent/reload-prompt")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "reloaded" in data["message"].lower()

    @patch("src.api.routes.admin.load_system_prompt_from_xml")
    @patch("src.api.routes.admin.get_system_prompt_path")
    def test_reload_prompt_failure(self, mock_path, mock_load, client):
        """Test prompt reload failure."""
        mock_path.return_value = "/path/to/prompt.xml"
        mock_load.return_value = None
        
        response = client.post("/api/admin/agent/reload-prompt")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is False


class TestBusinessHoursEndpoints:
    """Tests for business hours configuration endpoints."""

    def test_get_business_hours(self, client):
        """Test GET /api/admin/config/business-hours."""
        response = client.get("/api/admin/config/business-hours")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "timezone" in data
        assert "schedule" in data
        assert "current_status" in data

    def test_business_hours_schedule_format(self, client):
        """Test that schedule contains all days of the week."""
        response = client.get("/api/admin/config/business-hours")
        
        assert response.status_code == 200
        data = response.json()
        
        expected_days = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
        for day in expected_days:
            assert day in data["schedule"]

    def test_update_business_hours(self, client):
        """Test PUT /api/admin/config/business-hours."""
        response = client.put(
            "/api/admin/config/business-hours",
            json={"timezone": "America/Sao_Paulo"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "timezone" in data
        assert "schedule" in data


class TestLeadsEndpoints:
    """Tests for leads listing and details endpoints."""

    @patch("src.api.routes.admin.get_supabase_client")
    def test_list_leads_success(self, mock_client, client):
        """Test GET /api/admin/leads with mock data."""
        mock_supabase = MagicMock()
        mock_client.return_value = mock_supabase
        
        # Mock the query chain
        mock_query = MagicMock()
        mock_supabase.table.return_value.select.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.range.return_value = mock_query
        mock_query.execute.return_value = MagicMock(
            data=[
                {
                    "id": "123",
                    "phone": "5511999999999",
                    "name": "Test Lead",
                    "temperature": "quente",
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                }
            ],
            count=1
        )
        
        response = client.get("/api/admin/leads")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "limit" in data

    @patch("src.api.routes.admin.get_supabase_client")
    def test_list_leads_with_temperature_filter(self, mock_client, client):
        """Test leads filtering by temperature."""
        mock_supabase = MagicMock()
        mock_client.return_value = mock_supabase
        
        mock_query = MagicMock()
        mock_supabase.table.return_value.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.range.return_value = mock_query
        mock_query.execute.return_value = MagicMock(data=[], count=0)
        
        response = client.get("/api/admin/leads?temperature=quente")
        
        assert response.status_code == 200
        mock_query.eq.assert_called_with("temperature", "quente")

    @patch("src.api.routes.admin.get_supabase_client")
    def test_list_leads_with_search(self, mock_client, client):
        """Test leads search functionality."""
        mock_supabase = MagicMock()
        mock_client.return_value = mock_supabase
        
        mock_query = MagicMock()
        mock_supabase.table.return_value.select.return_value = mock_query
        mock_query.or_.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.range.return_value = mock_query
        mock_query.execute.return_value = MagicMock(data=[], count=0)
        
        response = client.get("/api/admin/leads?search=test")
        
        assert response.status_code == 200
        mock_query.or_.assert_called_once()

    @patch("src.api.routes.admin.get_supabase_client")
    def test_list_leads_pagination(self, mock_client, client):
        """Test leads pagination parameters."""
        mock_supabase = MagicMock()
        mock_client.return_value = mock_supabase
        
        mock_query = MagicMock()
        mock_supabase.table.return_value.select.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.range.return_value = mock_query
        mock_query.execute.return_value = MagicMock(data=[], count=0)
        
        response = client.get("/api/admin/leads?page=2&limit=10")
        
        assert response.status_code == 200
        # Page 2 with limit 10 should start at offset 10
        mock_query.range.assert_called_with(10, 19)

    @patch("src.api.routes.admin.get_lead_by_phone")
    def test_get_lead_success(self, mock_get_lead, client):
        """Test GET /api/admin/leads/{phone} success."""
        mock_get_lead.return_value = {
            "id": "123",
            "phone": "5511999999999",
            "name": "Test Lead",
            "temperature": "quente",
        }
        
        response = client.get("/api/admin/leads/5511999999999")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["phone"] == "5511999999999"
        assert data["name"] == "Test Lead"

    @patch("src.api.routes.admin.get_lead_by_phone")
    def test_get_lead_not_found(self, mock_get_lead, client):
        """Test GET /api/admin/leads/{phone} when lead not found."""
        mock_get_lead.return_value = None
        
        response = client.get("/api/admin/leads/5511999999999")
        
        assert response.status_code == 404

    def test_get_lead_invalid_phone(self, client):
        """Test GET /api/admin/leads/{phone} with invalid phone."""
        response = client.get("/api/admin/leads/invalid")
        
        assert response.status_code == 400


class TestConversationEndpoint:
    """Tests for conversation history endpoint."""

    @patch("src.api.routes.admin.get_supabase_client")
    def test_get_conversation_success(self, mock_client, client):
        """Test GET /api/admin/leads/{phone}/conversation success."""
        mock_supabase = MagicMock()
        mock_client.return_value = mock_supabase
        
        mock_query = MagicMock()
        mock_supabase.table.return_value.select.return_value = mock_query
        mock_query.eq.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.execute.return_value = MagicMock(
            data=[
                {
                    "id": "msg1",
                    "role": "user",
                    "content": "Hello",
                    "timestamp": "2024-01-01T00:00:00Z",
                },
                {
                    "id": "msg2",
                    "role": "assistant",
                    "content": "Hi there!",
                    "timestamp": "2024-01-01T00:00:01Z",
                },
            ]
        )
        
        response = client.get("/api/admin/leads/5511999999999/conversation")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "messages" in data
        assert "total" in data
        assert len(data["messages"]) == 2

    def test_get_conversation_invalid_phone(self, client):
        """Test conversation endpoint with invalid phone."""
        response = client.get("/api/admin/leads/invalid/conversation")
        
        assert response.status_code == 400


class TestCacheEndpoint:
    """Tests for cache management endpoint."""

    @patch("src.api.routes.admin.clear_cache")
    def test_clear_cache_all(self, mock_clear, client):
        """Test clearing entire cache."""
        response = client.post("/api/admin/cache/clear")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        mock_clear.assert_called_once_with(None)

    @patch("src.api.routes.admin.clear_cache")
    def test_clear_cache_specific_phone(self, mock_clear, client):
        """Test clearing cache for specific phone."""
        response = client.post("/api/admin/cache/clear?phone=5511999999999")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert "5511999999999" in data["message"]
        mock_clear.assert_called_once_with("5511999999999")
