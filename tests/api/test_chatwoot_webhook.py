"""
Tests for Chatwoot webhook endpoint.

This module tests the Chatwoot webhook functionality including:
- Webhook payload parsing
- SDR intervention detection
- Agent pause/resume commands
- Phone number extraction
"""

import pytest
import json
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from src.main import app
from src.api.routes.webhook import (
    ChatwootWebhookPayload,
    ChatwootMessage,
    ChatwootSender,
    ChatwootConversation,
    ChatwootContact,
    _is_sdr_message,
    _extract_phone_from_payload,
    process_chatwoot_message,
)


client = TestClient(app)


@pytest.fixture
def chatwoot_message_from_contact():
    """Fixture for a message from a contact (lead)."""
    return {
        "event": "message_created",
        "message": {
            "id": 1,
            "content": "Ola, gostaria de saber mais sobre produtos",
            "message_type": "incoming",
            "private": False,
            "sender": {
                "id": 100,
                "name": "Lead Test",
                "type": "contact",
                "email": "lead@test.com"
            },
            "conversation_id": 10,
            "created_at": "2026-01-06T10:00:00Z"
        },
        "conversation": {
            "id": 10,
            "inbox_id": 1,
            "meta": {
                "sender": {
                    "phone_number": "+5511999999999"
                }
            }
        },
        "contact": {
            "id": 100,
            "name": "Lead Test",
            "phone_number": "+5511999999999",
            "email": "lead@test.com"
        },
        "account": {"id": 1}
    }


@pytest.fixture
def chatwoot_message_from_sdr():
    """Fixture for a message from an SDR (agent/user)."""
    return {
        "event": "message_created",
        "message": {
            "id": 2,
            "content": "Ola, sou o atendente humano",
            "message_type": "outgoing",
            "private": False,
            "sender": {
                "id": 1,
                "name": "SDR John",
                "type": "user",
                "email": "sdr@seleto.com"
            },
            "conversation_id": 10,
            "created_at": "2026-01-06T10:05:00Z"
        },
        "conversation": {
            "id": 10,
            "inbox_id": 1,
            "meta": {}
        },
        "contact": {
            "id": 100,
            "name": "Lead Test",
            "phone_number": "+5511999999999",
            "email": "lead@test.com"
        },
        "account": {"id": 1}
    }


@pytest.fixture
def chatwoot_private_note():
    """Fixture for a private note from SDR."""
    return {
        "event": "message_created",
        "message": {
            "id": 3,
            "content": "Nota interna para o time",
            "message_type": "outgoing",
            "private": True,
            "sender": {
                "id": 1,
                "name": "SDR John",
                "type": "user",
                "email": "sdr@seleto.com"
            },
            "conversation_id": 10,
            "created_at": "2026-01-06T10:10:00Z"
        },
        "conversation": {
            "id": 10,
            "inbox_id": 1,
            "meta": {}
        },
        "contact": {
            "id": 100,
            "name": "Lead Test",
            "phone_number": "+5511999999999",
            "email": "lead@test.com"
        },
        "account": {"id": 1}
    }


@pytest.fixture
def chatwoot_resume_command():
    """Fixture for a resume command from SDR."""
    return {
        "event": "message_created",
        "message": {
            "id": 4,
            "content": "/retomar",
            "message_type": "outgoing",
            "private": False,
            "sender": {
                "id": 1,
                "name": "SDR John",
                "type": "user",
                "email": "sdr@seleto.com"
            },
            "conversation_id": 10,
            "created_at": "2026-01-06T10:15:00Z"
        },
        "conversation": {
            "id": 10,
            "inbox_id": 1,
            "meta": {}
        },
        "contact": {
            "id": 100,
            "name": "Lead Test",
            "phone_number": "+5511999999999",
            "email": "lead@test.com"
        },
        "account": {"id": 1}
    }


class TestIsSdrMessage:
    """Tests for _is_sdr_message function."""

    def test_identifies_sdr_message(self, chatwoot_message_from_sdr):
        """Test that SDR messages are identified correctly."""
        payload = ChatwootWebhookPayload(**chatwoot_message_from_sdr)
        assert _is_sdr_message(payload) is True

    def test_identifies_contact_message(self, chatwoot_message_from_contact):
        """Test that contact messages are identified correctly."""
        payload = ChatwootWebhookPayload(**chatwoot_message_from_contact)
        assert _is_sdr_message(payload) is False

    def test_handles_missing_sender(self):
        """Test handling of missing sender."""
        payload = ChatwootWebhookPayload(
            event="message_created",
            message=ChatwootMessage(id=1, content="test")
        )
        assert _is_sdr_message(payload) is False

    def test_handles_missing_message(self):
        """Test handling of missing message."""
        payload = ChatwootWebhookPayload(event="message_created")
        assert _is_sdr_message(payload) is False


class TestExtractPhoneFromPayload:
    """Tests for _extract_phone_from_payload function."""

    def test_extracts_from_contact(self, chatwoot_message_from_contact):
        """Test phone extraction from contact object."""
        payload = ChatwootWebhookPayload(**chatwoot_message_from_contact)
        phone = _extract_phone_from_payload(payload)
        assert phone == "5511999999999"

    def test_extracts_from_conversation_meta(self):
        """Test phone extraction from conversation metadata."""
        payload = ChatwootWebhookPayload(
            event="message_created",
            conversation=ChatwootConversation(
                id=10,
                meta={"sender": {"phone_number": "+5511888888888"}}
            )
        )
        phone = _extract_phone_from_payload(payload)
        assert phone == "5511888888888"

    def test_returns_none_when_no_phone(self):
        """Test that None is returned when no phone is available."""
        payload = ChatwootWebhookPayload(event="message_created")
        phone = _extract_phone_from_payload(payload)
        assert phone is None


class TestChatwootWebhookEndpoint:
    """Tests for the Chatwoot webhook endpoint."""

    def test_returns_200_on_valid_payload(self, chatwoot_message_from_contact):
        """Test that 200 is returned on valid payload."""
        response = client.post(
            "/webhook/chatwoot",
            json=chatwoot_message_from_contact,
        )
        assert response.status_code == 200

    def test_returns_200_and_ignores_non_message_events(self):
        """Test that non-message events are ignored."""
        payload = {
            "event": "conversation_created",
            "conversation": {"id": 10}
        }
        response = client.post(
            "/webhook/chatwoot",
            json=payload,
        )
        assert response.status_code == 200
        assert response.json().get("reason") == "event_type"

    def test_returns_400_on_invalid_json(self):
        """Test that 400 is returned on invalid JSON."""
        response = client.post(
            "/webhook/chatwoot",
            content="invalid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 400

    def test_processes_sdr_message_and_pauses_agent(self, chatwoot_message_from_sdr):
        """Test that SDR message pauses the agent."""
        with patch("src.api.routes.webhook.pause_agent") as mock_pause, \
             patch("src.api.routes.webhook.send_internal_message_to_chatwoot", new_callable=AsyncMock) as mock_send:
            mock_pause.return_value = True

            response = client.post(
                "/webhook/chatwoot",
                json=chatwoot_message_from_sdr,
            )

            assert response.status_code == 200
            # Give async task time to run
            import time
            time.sleep(0.1)
            mock_pause.assert_called_once()

    def test_ignores_contact_message(self, chatwoot_message_from_contact):
        """Test that contact messages don't trigger pause."""
        with patch("src.api.routes.webhook.pause_agent") as mock_pause:
            response = client.post(
                "/webhook/chatwoot",
                json=chatwoot_message_from_contact,
            )

            assert response.status_code == 200
            mock_pause.assert_not_called()

    def test_ignores_private_notes(self, chatwoot_private_note):
        """Test that private notes don't trigger pause."""
        with patch("src.api.routes.webhook.pause_agent") as mock_pause:
            response = client.post(
                "/webhook/chatwoot",
                json=chatwoot_private_note,
            )

            assert response.status_code == 200
            mock_pause.assert_not_called()


class TestProcessChatwootMessage:
    """Tests for process_chatwoot_message function."""

    @pytest.mark.asyncio
    async def test_ignores_message_without_phone(self):
        """Test that messages without phone are ignored."""
        payload = ChatwootWebhookPayload(
            event="message_created",
            message=ChatwootMessage(
                id=1,
                content="test",
                sender=ChatwootSender(id=1, type="user", name="SDR")
            )
        )

        result = await process_chatwoot_message(payload)

        assert result["status"] == "error"
        assert result["reason"] == "no_phone"

    @pytest.mark.asyncio
    async def test_ignores_contact_messages(self, chatwoot_message_from_contact):
        """Test that contact messages are ignored."""
        payload = ChatwootWebhookPayload(**chatwoot_message_from_contact)

        result = await process_chatwoot_message(payload)

        assert result["status"] == "ignored"
        assert result["reason"] == "contact_message"

    @pytest.mark.asyncio
    async def test_processes_resume_command(self, chatwoot_resume_command):
        """Test that resume command is processed."""
        payload = ChatwootWebhookPayload(**chatwoot_resume_command)

        with patch("src.api.routes.webhook.process_sdr_command") as mock_process, \
             patch("src.api.routes.webhook.send_internal_message_to_chatwoot", new_callable=AsyncMock):
            mock_process.return_value = (True, "Agente retomado com sucesso")

            result = await process_chatwoot_message(payload)

            assert result["status"] == "command_processed"
            mock_process.assert_called_once()

    @pytest.mark.asyncio
    async def test_pauses_agent_on_sdr_intervention(self, chatwoot_message_from_sdr):
        """Test that agent is paused on SDR intervention."""
        payload = ChatwootWebhookPayload(**chatwoot_message_from_sdr)

        with patch("src.api.routes.webhook.pause_agent") as mock_pause, \
             patch("src.api.routes.webhook.send_internal_message_to_chatwoot", new_callable=AsyncMock):
            mock_pause.return_value = True

            result = await process_chatwoot_message(payload)

            assert result["status"] == "agent_paused"
            mock_pause.assert_called_once()

    @pytest.mark.asyncio
    async def test_ignores_private_notes(self, chatwoot_private_note):
        """Test that private notes are ignored (no pause)."""
        payload = ChatwootWebhookPayload(**chatwoot_private_note)

        with patch("src.api.routes.webhook.pause_agent") as mock_pause:
            result = await process_chatwoot_message(payload)

            assert result["status"] == "ignored"
            assert result["reason"] == "private_note"
            mock_pause.assert_not_called()


class TestPayloadParsing:
    """Tests for Chatwoot webhook payload parsing."""

    def test_parses_complete_payload(self, chatwoot_message_from_sdr):
        """Test parsing of complete webhook payload."""
        payload = ChatwootWebhookPayload(**chatwoot_message_from_sdr)

        assert payload.event == "message_created"
        assert payload.message is not None
        assert payload.message.content == "Ola, sou o atendente humano"
        assert payload.message.sender.type == "user"
        assert payload.contact.phone_number == "+5511999999999"

    def test_parses_minimal_payload(self):
        """Test parsing of minimal webhook payload."""
        payload = ChatwootWebhookPayload(event="message_created")

        assert payload.event == "message_created"
        assert payload.message is None
        assert payload.contact is None

    def test_handles_missing_optional_fields(self):
        """Test handling of missing optional fields."""
        data = {
            "event": "message_created",
            "message": {
                "id": 1,
                "content": "test"
            }
        }
        payload = ChatwootWebhookPayload(**data)

        assert payload.message.id == 1
        assert payload.message.content == "test"
        assert payload.message.sender is None
        assert payload.message.private is False  # Default value
