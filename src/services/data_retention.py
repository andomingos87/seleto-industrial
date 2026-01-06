"""
Data retention service for LGPD compliance (TECH-031).

This service provides functions for:
- Anonymizing conversation messages/transcripts after retention period
- Anonymizing conversation context after retention period
- Anonymizing inactive leads
- Cleaning up completed pending operations

Retention periods are configurable via environment variables:
- TRANSCRIPT_RETENTION_DAYS: Days to retain conversation messages (default: 90)
- CONTEXT_RETENTION_DAYS: Days to retain conversation context (default: 90)
- LEAD_INACTIVITY_DAYS: Days of inactivity before lead anonymization (default: 365)
- PENDING_OPERATIONS_RETENTION_DAYS: Days to retain completed pending operations (default: 7)
"""

import re
from datetime import datetime, timedelta
from typing import Any

from src.config.settings import settings
from src.services.conversation_persistence import get_supabase_client
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Regex patterns for identifying personal data in text
PHONE_PATTERN = re.compile(
    r"\b(?:\+?55\s?)?(?:\(?\d{2}\)?\s?)?\d{4,5}[-.\s]?\d{4}\b"
)
EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
)
CNPJ_PATTERN = re.compile(
    r"\b\d{2}\.?\d{3}\.?\d{3}/?0001-?\d{2}\b"
)
CPF_PATTERN = re.compile(
    r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"
)

# Placeholders for anonymization
PHONE_PLACEHOLDER = "[TELEFONE]"
EMAIL_PLACEHOLDER = "[EMAIL]"
CNPJ_PLACEHOLDER = "[CNPJ]"
CPF_PLACEHOLDER = "[CPF]"
NAME_PLACEHOLDER = "[NOME]"


def anonymize_text(text: str) -> str:
    """
    Anonymize personal data in text by replacing with placeholders.

    Replaces:
    - Phone numbers with [TELEFONE]
    - Email addresses with [EMAIL]
    - CNPJs with [CNPJ]
    - CPFs with [CPF]

    Args:
        text: Text to anonymize

    Returns:
        Anonymized text with placeholders
    """
    if not text:
        return text

    result = text
    result = PHONE_PATTERN.sub(PHONE_PLACEHOLDER, result)
    result = EMAIL_PATTERN.sub(EMAIL_PLACEHOLDER, result)
    result = CNPJ_PATTERN.sub(CNPJ_PLACEHOLDER, result)
    result = CPF_PATTERN.sub(CPF_PLACEHOLDER, result)

    return result


def anonymize_phone(phone: str) -> str:
    """
    Anonymize a phone number by hashing or replacing.

    For LGPD compliance, we use a placeholder instead of hash
    to ensure the data cannot be re-identified.

    Args:
        phone: Phone number to anonymize

    Returns:
        Anonymized phone string
    """
    if not phone:
        return phone

    # Use a deterministic but anonymized format
    # Keep last 4 digits for potential reference, mask the rest
    if len(phone) >= 4:
        return f"ANON-{phone[-4:]}"
    return "ANON-XXXX"


def anonymize_context_data(context: dict[str, Any]) -> dict[str, Any]:
    """
    Anonymize personal data fields in conversation context.

    Anonymizes known personal data fields:
    - name -> [NOME]
    - email -> [EMAIL]
    - phone -> [TELEFONE]
    - company -> keeps (non-identifying)
    - Other fields: scans for patterns and anonymizes

    Args:
        context: Context dictionary to anonymize

    Returns:
        Anonymized context dictionary
    """
    if not context:
        return context

    anonymized = {}
    personal_fields = {"name", "nome", "email", "phone", "telefone", "cpf", "cnpj"}

    for key, value in context.items():
        key_lower = key.lower()

        if key_lower in personal_fields:
            # Known personal data field - use placeholder
            if key_lower in ("name", "nome"):
                anonymized[key] = NAME_PLACEHOLDER
            elif key_lower == "email":
                anonymized[key] = EMAIL_PLACEHOLDER
            elif key_lower in ("phone", "telefone"):
                anonymized[key] = PHONE_PLACEHOLDER
            elif key_lower == "cpf":
                anonymized[key] = CPF_PLACEHOLDER
            elif key_lower == "cnpj":
                anonymized[key] = CNPJ_PLACEHOLDER
        elif isinstance(value, str):
            # Unknown field - scan for patterns
            anonymized[key] = anonymize_text(value)
        elif isinstance(value, dict):
            # Nested dict - recurse
            anonymized[key] = anonymize_context_data(value)
        else:
            # Keep as-is (numbers, booleans, etc.)
            anonymized[key] = value

    return anonymized


def get_expired_messages_cutoff() -> datetime:
    """Get the cutoff datetime for expired messages."""
    return datetime.utcnow() - timedelta(days=settings.TRANSCRIPT_RETENTION_DAYS)


def get_expired_context_cutoff() -> datetime:
    """Get the cutoff datetime for expired context."""
    return datetime.utcnow() - timedelta(days=settings.CONTEXT_RETENTION_DAYS)


def get_inactive_lead_cutoff() -> datetime:
    """Get the cutoff datetime for inactive leads."""
    return datetime.utcnow() - timedelta(days=settings.LEAD_INACTIVITY_DAYS)


def anonymize_expired_messages() -> dict[str, int]:
    """
    Anonymize conversation messages older than retention period.

    This function:
    1. Finds messages older than TRANSCRIPT_RETENTION_DAYS
    2. Anonymizes the content (replaces personal data with placeholders)
    3. Updates the records in place

    Returns:
        Dictionary with counts: {"processed": N, "anonymized": N, "errors": N}
    """
    client = get_supabase_client()
    if not client:
        logger.warning("Supabase not available - skipping message anonymization")
        return {"processed": 0, "anonymized": 0, "errors": 0}

    cutoff = get_expired_messages_cutoff()
    cutoff_str = cutoff.isoformat()

    stats = {"processed": 0, "anonymized": 0, "errors": 0}

    try:
        # Fetch messages older than cutoff that haven't been anonymized
        # We identify already-anonymized messages by checking for placeholders
        response = (
            client.table("conversation_messages")
            .select("id, content, lead_phone")
            .lt("timestamp", cutoff_str)
            .not_.like("content", f"%{PHONE_PLACEHOLDER}%")
            .limit(1000)  # Process in batches
            .execute()
        )

        messages = response.data or []
        stats["processed"] = len(messages)

        for msg in messages:
            try:
                msg_id = msg.get("id")
                content = msg.get("content", "")
                lead_phone = msg.get("lead_phone", "")

                # Anonymize content
                anonymized_content = anonymize_text(content)
                anonymized_phone = anonymize_phone(lead_phone)

                # Update only if changes were made
                if anonymized_content != content or anonymized_phone != lead_phone:
                    client.table("conversation_messages").update(
                        {
                            "content": anonymized_content,
                            "lead_phone": anonymized_phone,
                        }
                    ).eq("id", msg_id).execute()

                    stats["anonymized"] += 1
                    logger.debug(
                        "Message anonymized",
                        extra={"message_id": msg_id},
                    )

            except Exception as e:
                stats["errors"] += 1
                logger.error(
                    "Failed to anonymize message",
                    extra={"message_id": msg.get("id"), "error": str(e)},
                )

        logger.info(
            "Message anonymization completed",
            extra=stats,
        )

    except Exception as e:
        logger.error(
            "Failed to fetch messages for anonymization",
            extra={"error": str(e)},
            exc_info=True,
        )

    return stats


def anonymize_expired_context() -> dict[str, int]:
    """
    Anonymize conversation context older than retention period.

    This function:
    1. Finds context records older than CONTEXT_RETENTION_DAYS
    2. Anonymizes the context_data JSON
    3. Updates the records in place

    Returns:
        Dictionary with counts: {"processed": N, "anonymized": N, "errors": N}
    """
    client = get_supabase_client()
    if not client:
        logger.warning("Supabase not available - skipping context anonymization")
        return {"processed": 0, "anonymized": 0, "errors": 0}

    cutoff = get_expired_context_cutoff()
    cutoff_str = cutoff.isoformat()

    stats = {"processed": 0, "anonymized": 0, "errors": 0}

    try:
        # Fetch context older than cutoff
        response = (
            client.table("conversation_context")
            .select("id, lead_phone, context_data, updated_at")
            .lt("updated_at", cutoff_str)
            .limit(1000)
            .execute()
        )

        contexts = response.data or []
        stats["processed"] = len(contexts)

        for ctx in contexts:
            try:
                ctx_id = ctx.get("id")
                lead_phone = ctx.get("lead_phone", "")
                context_data = ctx.get("context_data", {})

                # Skip if already anonymized (lead_phone starts with ANON-)
                if lead_phone.startswith("ANON-"):
                    continue

                # Anonymize context data
                anonymized_data = anonymize_context_data(context_data)
                anonymized_phone = anonymize_phone(lead_phone)

                client.table("conversation_context").update(
                    {
                        "context_data": anonymized_data,
                        "lead_phone": anonymized_phone,
                    }
                ).eq("id", ctx_id).execute()

                stats["anonymized"] += 1
                logger.debug(
                    "Context anonymized",
                    extra={"context_id": ctx_id},
                )

            except Exception as e:
                stats["errors"] += 1
                logger.error(
                    "Failed to anonymize context",
                    extra={"context_id": ctx.get("id"), "error": str(e)},
                )

        logger.info(
            "Context anonymization completed",
            extra=stats,
        )

    except Exception as e:
        logger.error(
            "Failed to fetch context for anonymization",
            extra={"error": str(e)},
            exc_info=True,
        )

    return stats


def anonymize_inactive_leads() -> dict[str, int]:
    """
    Anonymize leads that have been inactive for longer than retention period.

    A lead is considered inactive if:
    - No conversation messages in the last LEAD_INACTIVITY_DAYS days

    This function:
    1. Finds inactive leads
    2. Anonymizes personal data (phone, name, email)
    3. Marks lead as anonymized
    4. Keeps non-identifying data for aggregate analysis

    Returns:
        Dictionary with counts: {"processed": N, "anonymized": N, "errors": N}
    """
    client = get_supabase_client()
    if not client:
        logger.warning("Supabase not available - skipping lead anonymization")
        return {"processed": 0, "anonymized": 0, "errors": 0}

    cutoff = get_inactive_lead_cutoff()
    cutoff_str = cutoff.isoformat()

    stats = {"processed": 0, "anonymized": 0, "errors": 0}

    try:
        # Fetch leads that haven't been updated since cutoff
        # and haven't been anonymized yet (phone doesn't start with ANON-)
        response = (
            client.table("leads")
            .select("id, phone, name, email")
            .lt("updated_at", cutoff_str)
            .not_.like("phone", "ANON-%")
            .limit(500)
            .execute()
        )

        leads = response.data or []
        stats["processed"] = len(leads)

        for lead in leads:
            try:
                lead_id = lead.get("id")
                phone = lead.get("phone", "")

                # Verify lead is truly inactive by checking messages
                msg_response = (
                    client.table("conversation_messages")
                    .select("id")
                    .eq("lead_phone", phone)
                    .gt("timestamp", cutoff_str)
                    .limit(1)
                    .execute()
                )

                if msg_response.data:
                    # Lead has recent messages, skip
                    continue

                # Anonymize lead
                anonymized_phone = anonymize_phone(phone)

                client.table("leads").update(
                    {
                        "phone": anonymized_phone,
                        "name": NAME_PLACEHOLDER,
                        "email": EMAIL_PLACEHOLDER,
                    }
                ).eq("id", lead_id).execute()

                stats["anonymized"] += 1
                logger.debug(
                    "Lead anonymized",
                    extra={"lead_id": lead_id},
                )

            except Exception as e:
                stats["errors"] += 1
                logger.error(
                    "Failed to anonymize lead",
                    extra={"lead_id": lead.get("id"), "error": str(e)},
                )

        logger.info(
            "Lead anonymization completed",
            extra=stats,
        )

    except Exception as e:
        logger.error(
            "Failed to fetch leads for anonymization",
            extra={"error": str(e)},
            exc_info=True,
        )

    return stats


def cleanup_completed_operations() -> dict[str, int]:
    """
    Delete completed pending operations older than retention period.

    This function:
    1. Finds completed operations older than PENDING_OPERATIONS_RETENTION_DAYS
    2. Deletes them permanently (they contain sensitive data)

    Returns:
        Dictionary with counts: {"processed": N, "deleted": N, "errors": N}
    """
    client = get_supabase_client()
    if not client:
        logger.warning("Supabase not available - skipping operations cleanup")
        return {"processed": 0, "deleted": 0, "errors": 0}

    cutoff = datetime.utcnow() - timedelta(
        days=settings.PENDING_OPERATIONS_RETENTION_DAYS
    )
    cutoff_str = cutoff.isoformat()

    stats = {"processed": 0, "deleted": 0, "errors": 0}

    try:
        # Delete completed operations older than cutoff
        response = (
            client.table("pending_operations")
            .delete()
            .eq("status", "completed")
            .lt("completed_at", cutoff_str)
            .execute()
        )

        deleted_count = len(response.data) if response.data else 0
        stats["processed"] = deleted_count
        stats["deleted"] = deleted_count

        logger.info(
            "Pending operations cleanup completed",
            extra=stats,
        )

    except Exception as e:
        stats["errors"] += 1
        logger.error(
            "Failed to cleanup pending operations",
            extra={"error": str(e)},
            exc_info=True,
        )

    return stats


def run_all_retention_jobs() -> dict[str, dict[str, int]]:
    """
    Run all data retention jobs.

    This function runs:
    1. anonymize_expired_messages
    2. anonymize_expired_context
    3. anonymize_inactive_leads
    4. cleanup_completed_operations

    Returns:
        Dictionary with results from each job
    """
    logger.info("Starting all retention jobs")

    results = {
        "messages": anonymize_expired_messages(),
        "context": anonymize_expired_context(),
        "leads": anonymize_inactive_leads(),
        "operations": cleanup_completed_operations(),
    }

    logger.info(
        "All retention jobs completed",
        extra={"results": results},
    )

    return results
