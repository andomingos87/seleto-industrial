"""
Handoff Summary Service for Hot Leads.

This module generates and sends structured handoff summaries to Chatwoot
when a lead is classified as "quente" (hot). The summary follows the template
defined in the PRD (Appendix 20.4) and is sent as an internal note.

Features:
- Generate structured summary from lead, orcamento, and empresa data
- Send summary as private message in Chatwoot
- Prevent duplicate summaries using context flags
- Handle missing data gracefully with "Nao informado" placeholder
"""

import asyncio
from datetime import datetime
from typing import Dict, Optional, Any

from src.services.chatwoot_sync import send_internal_message_to_chatwoot
from src.services.conversation_persistence import (
    get_context_from_supabase,
    save_context_to_supabase,
)
from src.utils.logging import get_logger
from src.utils.validation import normalize_phone

logger = get_logger(__name__)

# Default value for missing fields
NOT_INFORMED = "Nao informado"

# Context key for tracking handoff summary sent
HANDOFF_SUMMARY_SENT_KEY = "handoff_summary_sent"


def _get_field_value(
    *sources: Dict[str, Any],
    keys: list[str],
    default: str = NOT_INFORMED,
) -> str:
    """
    Get field value from multiple sources, trying each key in order.

    Args:
        *sources: Variable number of source dictionaries
        keys: List of keys to try in each source
        default: Default value if not found

    Returns:
        First non-empty value found, or default
    """
    for source in sources:
        if not source:
            continue
        for key in keys:
            value = source.get(key)
            if value and str(value).strip():
                return str(value).strip()
    return default


def generate_handoff_summary(
    lead_data: Optional[Dict[str, Any]] = None,
    orcamento_data: Optional[Dict[str, Any]] = None,
    empresa_data: Optional[Dict[str, Any]] = None,
    conversation_summary: Optional[str] = None,
    canal: str = "WhatsApp",
) -> str:
    """
    Generate a structured handoff summary for a hot lead.

    The summary follows the template from PRD Appendix 20.4:
    - Nome
    - Empresa
    - Localizacao (cidade/UF)
    - Produto de Interesse
    - Capacidade / Volume
    - Urgencia
    - Ja conhece a Seleto Industrial?
    - Observacoes adicionais

    Args:
        lead_data: Dictionary with lead data (name, company, city, uf, product, volume, urgency, knows_seleto)
        orcamento_data: Dictionary with orcamento data (produto, volume_diario, urgencia_compra, resumo)
        empresa_data: Dictionary with empresa data (nome, cidade, uf)
        conversation_summary: Summary of the conversation
        canal: Channel name (default: WhatsApp)

    Returns:
        Formatted handoff summary string
    """
    lead_data = lead_data or {}
    orcamento_data = orcamento_data or {}
    empresa_data = empresa_data or {}

    # Extract fields with fallbacks
    nome = _get_field_value(lead_data, keys=["name", "nome"])

    empresa = _get_field_value(
        lead_data, empresa_data,
        keys=["company", "empresa", "nome"]
    )

    cidade = _get_field_value(
        lead_data, empresa_data,
        keys=["city", "cidade"]
    )

    uf = _get_field_value(
        lead_data, empresa_data,
        keys=["uf", "estado"]
    )

    # Format location
    if cidade != NOT_INFORMED and uf != NOT_INFORMED:
        localizacao = f"{cidade}/{uf}"
    elif cidade != NOT_INFORMED:
        localizacao = cidade
    elif uf != NOT_INFORMED:
        localizacao = uf
    else:
        localizacao = NOT_INFORMED

    produto = _get_field_value(
        lead_data, orcamento_data,
        keys=["product", "produto", "produto_interesse"]
    )

    volume = _get_field_value(
        lead_data, orcamento_data,
        keys=["volume", "volume_diario", "volume_estimado", "capacidade"]
    )

    urgencia = _get_field_value(
        lead_data, orcamento_data,
        keys=["urgency", "urgencia", "urgencia_compra"]
    )

    conhece_seleto = _get_field_value(
        lead_data,
        keys=["knows_seleto", "conhece_seleto", "ja_conhece"]
    )

    # Get observations from orcamento or conversation summary
    observacoes = _get_field_value(
        orcamento_data,
        keys=["resumo", "observacoes", "notas"]
    )
    if observacoes == NOT_INFORMED and conversation_summary:
        observacoes = conversation_summary

    # Build the summary using the PRD template
    summary_lines = [
        f"Novo Lead Quente - via {canal}",
        "",
        f"  - Nome: {nome}",
        f"  - Empresa: {empresa}",
        f"  - Localizacao: {localizacao}",
        f"  - Produto de Interesse: {produto}",
        f"  - Capacidade / Volume: {volume}",
        f"  - Urgencia: {urgencia}",
        f"  - Ja conhece a Seleto Industrial?: {conhece_seleto}",
        f"  - Observacoes adicionais: {observacoes}",
    ]

    summary = "\n".join(summary_lines)

    logger.debug(
        "Handoff summary generated",
        extra={
            "nome": nome,
            "empresa": empresa,
            "produto": produto,
            "urgencia": urgencia,
            "summary_length": len(summary),
        },
    )

    return summary


def is_handoff_summary_sent(phone: str) -> bool:
    """
    Check if a handoff summary has already been sent for a lead.

    Args:
        phone: Phone number (will be normalized)

    Returns:
        True if summary was already sent, False otherwise
    """
    normalized_phone = normalize_phone(phone)
    if not normalized_phone:
        logger.warning(f"Invalid phone number: {phone}")
        return False

    context = get_context_from_supabase(normalized_phone)

    summary_state = context.get(HANDOFF_SUMMARY_SENT_KEY, {})
    is_sent = summary_state.get("sent", False)

    logger.debug(
        "Handoff summary sent check",
        extra={"phone": normalized_phone, "is_sent": is_sent},
    )

    return is_sent


def mark_handoff_summary_sent(
    phone: str,
    temperature: str = "quente",
) -> bool:
    """
    Mark that a handoff summary has been sent for a lead.

    Args:
        phone: Phone number (will be normalized)
        temperature: Temperature at which summary was sent

    Returns:
        True if marked successfully, False otherwise
    """
    normalized_phone = normalize_phone(phone)
    if not normalized_phone:
        logger.warning(f"Invalid phone number: {phone}")
        return False

    context = get_context_from_supabase(normalized_phone)

    context[HANDOFF_SUMMARY_SENT_KEY] = {
        "sent": True,
        "sent_at": datetime.utcnow().isoformat(),
        "temperature": temperature,
    }

    success = save_context_to_supabase(normalized_phone, context)

    if success:
        logger.info(
            "Handoff summary marked as sent",
            extra={"phone": normalized_phone, "temperature": temperature},
        )
    else:
        logger.error(
            "Failed to mark handoff summary as sent",
            extra={"phone": normalized_phone},
        )

    return success


async def send_handoff_summary(
    phone: str,
    lead_data: Optional[Dict[str, Any]] = None,
    orcamento_data: Optional[Dict[str, Any]] = None,
    empresa_data: Optional[Dict[str, Any]] = None,
    conversation_summary: Optional[str] = None,
    canal: str = "WhatsApp",
    force: bool = False,
) -> bool:
    """
    Generate and send a handoff summary to Chatwoot.

    This function:
    1. Checks if summary was already sent (unless force=True)
    2. Generates the summary using the PRD template
    3. Sends the summary as a private message in Chatwoot
    4. Marks the summary as sent to prevent duplicates

    Args:
        phone: Phone number (will be normalized)
        lead_data: Dictionary with lead data
        orcamento_data: Dictionary with orcamento data
        empresa_data: Dictionary with empresa data
        conversation_summary: Summary of the conversation
        canal: Channel name (default: WhatsApp)
        force: If True, send even if already sent (for manual resend)

    Returns:
        True if summary was sent successfully, False otherwise
    """
    normalized_phone = normalize_phone(phone)
    if not normalized_phone:
        logger.warning(f"Invalid phone number: {phone}")
        return False

    # Check if already sent (unless force)
    if not force and is_handoff_summary_sent(normalized_phone):
        logger.info(
            "Handoff summary already sent - skipping",
            extra={"phone": normalized_phone},
        )
        return False

    # Generate summary
    summary = generate_handoff_summary(
        lead_data=lead_data,
        orcamento_data=orcamento_data,
        empresa_data=empresa_data,
        conversation_summary=conversation_summary,
        canal=canal,
    )

    # Send to Chatwoot as internal message
    try:
        success = await send_internal_message_to_chatwoot(
            phone=normalized_phone,
            content=summary,
            sender_name="Sistema - Lead Quente",
        )

        if success:
            # Mark as sent
            mark_handoff_summary_sent(normalized_phone)
            logger.info(
                "Handoff summary sent successfully",
                extra={"phone": normalized_phone},
            )
            return True
        else:
            logger.warning(
                "Failed to send handoff summary to Chatwoot",
                extra={"phone": normalized_phone},
            )
            return False

    except Exception as e:
        logger.error(
            "Error sending handoff summary",
            extra={"phone": normalized_phone, "error": str(e)},
            exc_info=True,
        )
        return False


async def trigger_handoff_on_hot_lead(
    phone: str,
    lead_data: Optional[Dict[str, Any]] = None,
    temperature: str = "quente",
    justification: Optional[str] = None,
) -> bool:
    """
    Trigger handoff summary when a lead is classified as hot.

    This is the main entry point to be called from temperature classification.

    Args:
        phone: Phone number
        lead_data: Lead data dictionary
        temperature: Temperature classification (should be "quente")
        justification: Justification from temperature classification

    Returns:
        True if handoff was triggered successfully, False otherwise
    """
    # Only trigger for hot leads
    if temperature.lower() != "quente":
        logger.debug(
            "Handoff not triggered - lead not hot",
            extra={"phone": phone, "temperature": temperature},
        )
        return False

    logger.info(
        "Triggering handoff summary for hot lead",
        extra={"phone": phone, "temperature": temperature},
    )

    # Use justification as conversation summary if available
    conversation_summary = justification

    # Send the handoff summary
    return await send_handoff_summary(
        phone=phone,
        lead_data=lead_data,
        conversation_summary=conversation_summary,
    )


def clear_handoff_summary_flag(phone: str) -> bool:
    """
    Clear the handoff summary sent flag for a lead.

    This allows the summary to be sent again (useful for testing or manual resend).

    Args:
        phone: Phone number (will be normalized)

    Returns:
        True if cleared successfully, False otherwise
    """
    normalized_phone = normalize_phone(phone)
    if not normalized_phone:
        logger.warning(f"Invalid phone number: {phone}")
        return False

    context = get_context_from_supabase(normalized_phone)

    if HANDOFF_SUMMARY_SENT_KEY in context:
        context[HANDOFF_SUMMARY_SENT_KEY] = {
            "sent": False,
            "cleared_at": datetime.utcnow().isoformat(),
        }
        success = save_context_to_supabase(normalized_phone, context)

        if success:
            logger.info(
                "Handoff summary flag cleared",
                extra={"phone": normalized_phone},
            )
        return success

    return True
