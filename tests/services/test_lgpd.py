"""
Tests for LGPD compliance services (TECH-031).

This module tests data retention, anonymization, and
LGPD rights (access, correction, deletion, portability).
"""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from src.services.data_retention import (
    anonymize_text,
    anonymize_phone,
    anonymize_context_data,
    get_expired_messages_cutoff,
    get_expired_context_cutoff,
    get_inactive_lead_cutoff,
    PHONE_PLACEHOLDER,
    EMAIL_PLACEHOLDER,
    CNPJ_PLACEHOLDER,
    CPF_PLACEHOLDER,
    NAME_PLACEHOLDER,
)
from src.config.settings import settings


class TestAnonymizeText:
    """Tests for text anonymization function."""

    def test_anonymizes_phone_numbers(self):
        """Test that phone numbers are replaced with placeholder."""
        text = "Meu telefone é 11999999999"
        result = anonymize_text(text)
        assert PHONE_PLACEHOLDER in result
        assert "11999999999" not in result

    def test_anonymizes_phone_with_formatting(self):
        """Test that formatted phone numbers are anonymized."""
        text = "Ligue para (11) 99999-9999"
        result = anonymize_text(text)
        assert PHONE_PLACEHOLDER in result

    def test_anonymizes_phone_with_country_code(self):
        """Test that phone with country code is anonymized."""
        text = "WhatsApp: +55 11 99999-9999"
        result = anonymize_text(text)
        assert PHONE_PLACEHOLDER in result

    def test_anonymizes_email(self):
        """Test that email addresses are replaced with placeholder."""
        text = "Email: teste@exemplo.com"
        result = anonymize_text(text)
        assert EMAIL_PLACEHOLDER in result
        assert "teste@exemplo.com" not in result

    def test_anonymizes_cnpj(self):
        """Test that CNPJs are replaced with placeholder."""
        text = "CNPJ: 12.345.678/0001-90"
        result = anonymize_text(text)
        assert CNPJ_PLACEHOLDER in result

    def test_anonymizes_cpf(self):
        """Test that CPFs are replaced with placeholder."""
        text = "CPF: 123.456.789-00"
        result = anonymize_text(text)
        assert CPF_PLACEHOLDER in result

    def test_anonymizes_multiple_patterns(self):
        """Test that multiple patterns in same text are all anonymized."""
        text = "Contato: teste@email.com, telefone 11999999999"
        result = anonymize_text(text)
        assert EMAIL_PLACEHOLDER in result
        assert PHONE_PLACEHOLDER in result
        assert "teste@email.com" not in result
        assert "11999999999" not in result

    def test_preserves_non_sensitive_text(self):
        """Test that non-sensitive text is preserved."""
        text = "Olá, gostaria de um orçamento para FBM100"
        result = anonymize_text(text)
        assert result == text

    def test_handles_empty_text(self):
        """Test that empty text is handled."""
        assert anonymize_text("") == ""
        assert anonymize_text(None) is None


class TestAnonymizePhone:
    """Tests for phone anonymization function."""

    def test_anonymizes_phone_with_last_4_digits(self):
        """Test that phone is anonymized keeping last 4 digits."""
        result = anonymize_phone("5511999999999")
        assert result == "ANON-9999"

    def test_handles_short_phone(self):
        """Test that short phone numbers are handled."""
        result = anonymize_phone("123")
        assert result == "ANON-XXXX"

    def test_handles_empty_phone(self):
        """Test that empty phone is handled."""
        assert anonymize_phone("") == ""
        assert anonymize_phone(None) is None


class TestAnonymizeContextData:
    """Tests for context data anonymization."""

    def test_anonymizes_name_field(self):
        """Test that name field is anonymized."""
        context = {"name": "João Silva"}
        result = anonymize_context_data(context)
        assert result["name"] == NAME_PLACEHOLDER

    def test_anonymizes_email_field(self):
        """Test that email field is anonymized."""
        context = {"email": "joao@email.com"}
        result = anonymize_context_data(context)
        assert result["email"] == EMAIL_PLACEHOLDER

    def test_anonymizes_phone_field(self):
        """Test that phone field is anonymized."""
        context = {"phone": "11999999999"}
        result = anonymize_context_data(context)
        assert result["phone"] == PHONE_PLACEHOLDER

    def test_preserves_non_sensitive_fields(self):
        """Test that non-sensitive fields are preserved."""
        context = {
            "name": "João",
            "product_interest": "FBM100",
            "volume": "1000 L/dia",
        }
        result = anonymize_context_data(context)
        assert result["product_interest"] == "FBM100"
        assert result["volume"] == "1000 L/dia"

    def test_scans_unknown_fields_for_patterns(self):
        """Test that unknown text fields are scanned for patterns."""
        context = {
            "notes": "Cliente em teste@email.com pediu orçamento",
        }
        result = anonymize_context_data(context)
        assert EMAIL_PLACEHOLDER in result["notes"]
        assert "teste@email.com" not in result["notes"]

    def test_handles_nested_dicts(self):
        """Test that nested dicts are anonymized."""
        context = {
            "contact": {
                "name": "João",
                "email": "joao@email.com",
            }
        }
        result = anonymize_context_data(context)
        assert result["contact"]["name"] == NAME_PLACEHOLDER
        assert result["contact"]["email"] == EMAIL_PLACEHOLDER

    def test_handles_empty_context(self):
        """Test that empty context is handled."""
        assert anonymize_context_data({}) == {}
        assert anonymize_context_data(None) is None


class TestRetentionCutoffs:
    """Tests for retention period cutoff calculations."""

    def test_messages_cutoff_uses_settings(self):
        """Test that messages cutoff uses TRANSCRIPT_RETENTION_DAYS."""
        cutoff = get_expired_messages_cutoff()
        expected = datetime.utcnow() - timedelta(days=settings.TRANSCRIPT_RETENTION_DAYS)
        # Allow 1 second tolerance
        assert abs((cutoff - expected).total_seconds()) < 1

    def test_context_cutoff_uses_settings(self):
        """Test that context cutoff uses CONTEXT_RETENTION_DAYS."""
        cutoff = get_expired_context_cutoff()
        expected = datetime.utcnow() - timedelta(days=settings.CONTEXT_RETENTION_DAYS)
        assert abs((cutoff - expected).total_seconds()) < 1

    def test_lead_cutoff_uses_settings(self):
        """Test that lead cutoff uses LEAD_INACTIVITY_DAYS."""
        cutoff = get_inactive_lead_cutoff()
        expected = datetime.utcnow() - timedelta(days=settings.LEAD_INACTIVITY_DAYS)
        assert abs((cutoff - expected).total_seconds()) < 1


class TestAnonymizeExpiredMessages:
    """Tests for message anonymization job."""

    @patch("src.services.data_retention.get_supabase_client")
    def test_skips_when_supabase_unavailable(self, mock_client):
        """Test that job skips when Supabase is unavailable."""
        from src.services.data_retention import anonymize_expired_messages

        mock_client.return_value = None
        result = anonymize_expired_messages()
        assert result == {"processed": 0, "anonymized": 0, "errors": 0}

    @patch("src.services.data_retention.get_supabase_client")
    def test_processes_expired_messages(self, mock_client):
        """Test that expired messages are processed."""
        from src.services.data_retention import anonymize_expired_messages

        # Mock Supabase client
        client = MagicMock()
        mock_client.return_value = client

        # Mock response with messages
        client.table.return_value.select.return_value.lt.return_value.not_.like.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[
                {"id": "1", "content": "Email: teste@email.com", "lead_phone": "5511999999999"},
            ]
        )
        client.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock()

        result = anonymize_expired_messages()
        assert result["processed"] == 1
        assert result["anonymized"] == 1
        assert result["errors"] == 0


class TestAnonymizeExpiredContext:
    """Tests for context anonymization job."""

    @patch("src.services.data_retention.get_supabase_client")
    def test_skips_when_supabase_unavailable(self, mock_client):
        """Test that job skips when Supabase is unavailable."""
        from src.services.data_retention import anonymize_expired_context

        mock_client.return_value = None
        result = anonymize_expired_context()
        assert result == {"processed": 0, "anonymized": 0, "errors": 0}


class TestAnonymizeInactiveLeads:
    """Tests for inactive lead anonymization job."""

    @patch("src.services.data_retention.get_supabase_client")
    def test_skips_when_supabase_unavailable(self, mock_client):
        """Test that job skips when Supabase is unavailable."""
        from src.services.data_retention import anonymize_inactive_leads

        mock_client.return_value = None
        result = anonymize_inactive_leads()
        assert result == {"processed": 0, "anonymized": 0, "errors": 0}


class TestCleanupCompletedOperations:
    """Tests for completed operations cleanup job."""

    @patch("src.services.data_retention.get_supabase_client")
    def test_skips_when_supabase_unavailable(self, mock_client):
        """Test that job skips when Supabase is unavailable."""
        from src.services.data_retention import cleanup_completed_operations

        mock_client.return_value = None
        result = cleanup_completed_operations()
        assert result == {"processed": 0, "deleted": 0, "errors": 0}


class TestRunAllRetentionJobs:
    """Tests for running all retention jobs."""

    @patch("src.services.data_retention.cleanup_completed_operations")
    @patch("src.services.data_retention.anonymize_inactive_leads")
    @patch("src.services.data_retention.anonymize_expired_context")
    @patch("src.services.data_retention.anonymize_expired_messages")
    def test_runs_all_jobs(
        self, mock_messages, mock_context, mock_leads, mock_operations
    ):
        """Test that all jobs are executed."""
        from src.services.data_retention import run_all_retention_jobs

        mock_messages.return_value = {"processed": 1, "anonymized": 1, "errors": 0}
        mock_context.return_value = {"processed": 2, "anonymized": 2, "errors": 0}
        mock_leads.return_value = {"processed": 3, "anonymized": 3, "errors": 0}
        mock_operations.return_value = {"processed": 4, "deleted": 4, "errors": 0}

        result = run_all_retention_jobs()

        assert "messages" in result
        assert "context" in result
        assert "leads" in result
        assert "operations" in result

        mock_messages.assert_called_once()
        mock_context.assert_called_once()
        mock_leads.assert_called_once()
        mock_operations.assert_called_once()


class TestDataRetentionSettings:
    """Tests for data retention settings."""

    def test_default_transcript_retention_days(self):
        """Test default transcript retention period."""
        assert settings.TRANSCRIPT_RETENTION_DAYS == 90

    def test_default_context_retention_days(self):
        """Test default context retention period."""
        assert settings.CONTEXT_RETENTION_DAYS == 90

    def test_default_lead_inactivity_days(self):
        """Test default lead inactivity period."""
        assert settings.LEAD_INACTIVITY_DAYS == 365

    def test_default_pending_operations_retention_days(self):
        """Test default pending operations retention period."""
        assert settings.PENDING_OPERATIONS_RETENTION_DAYS == 7


class TestAnonymizationIrreversibility:
    """Tests to ensure anonymization is irreversible."""

    def test_anonymized_phone_not_recoverable(self):
        """Test that original phone cannot be recovered from anonymized."""
        original = "5511999999999"
        anonymized = anonymize_phone(original)
        # Only last 4 digits are kept, original cannot be recovered
        assert original not in anonymized
        assert len(anonymized) < len(original)

    def test_anonymized_text_placeholders_uniform(self):
        """Test that all instances of same type use same placeholder."""
        text = "Email1: a@b.com, Email2: c@d.com"
        result = anonymize_text(text)
        # Both emails should use same placeholder
        assert result.count(EMAIL_PLACEHOLDER) == 2
        assert "a@b.com" not in result
        assert "c@d.com" not in result
