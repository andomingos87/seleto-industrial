"""
Upsell Service - US-004: Sugerir upsell de FBM100 para FB300.

This module provides functionality to:
- Detect interest in FBM100 (manual hamburguer former)
- Suggest FB300 (semi-automatic) as a superior alternative
- Track upsell suggestions to avoid repetition
- Register suggestions in conversation context
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class UpsellSuggestion:
    """Record of an upsell suggestion made to a lead."""

    phone: str
    from_product: str
    to_product: str
    timestamp: str
    message_trigger: str  # The message that triggered the upsell


# In-memory storage for upsell suggestions (keyed by phone)
_upsell_suggestions: Dict[str, List[UpsellSuggestion]] = {}


# Keywords that indicate interest in FBM100
FBM100_KEYWORDS = [
    "fbm100",
    "fbm 100",
    "fbm-100",
    "formadora manual",
    "formadora de hambúrguer manual",
    "formadora de hamburguer manual",
    "formadora hambúrguer manual",
    "formadora hamburguer manual",
    "hambúrguer manual",
    "hamburguer manual",
    "máquina manual",
    "maquina manual",
    "produção manual",
    "producao manual",
    "fazer hambúrguer manual",
    "fazer hamburguer manual",
]

# Keywords that indicate user is asking about production capacity (context for upsell)
PRODUCTION_CONTEXT_KEYWORDS = [
    "produção",
    "producao",
    "produtividade",
    "capacidade",
    "quantidade",
    "quanto produz",
    "quantos hambúrgueres",
    "quantos hamburgueres",
    "por hora",
    "por dia",
    "aumentar produção",
    "aumentar producao",
    "mais produção",
    "mais producao",
    "escalar",
    "crescer",
    "expandir",
]


def detect_fbm100_interest(message: str) -> bool:
    """
    Detect if the user message indicates interest in FBM100.

    Uses keyword matching with variations to identify when a lead
    is asking about or interested in the manual former FBM100.

    Args:
        message: User's message text

    Returns:
        True if interest in FBM100 is detected
    """
    if not message:
        return False

    message_lower = message.lower()

    # Check for direct FBM100 keywords
    for keyword in FBM100_KEYWORDS:
        if keyword in message_lower:
            logger.debug(
                "FBM100 interest detected",
                extra={"keyword": keyword, "message_preview": message[:50]},
            )
            return True

    return False


def has_production_context(message: str) -> bool:
    """
    Check if the message has production/capacity context.

    This helps identify leads who might benefit from a higher
    capacity machine suggestion.

    Args:
        message: User's message text

    Returns:
        True if production context is detected
    """
    if not message:
        return False

    message_lower = message.lower()
    return any(keyword in message_lower for keyword in PRODUCTION_CONTEXT_KEYWORDS)


def get_upsell_suggestions(phone: str) -> List[UpsellSuggestion]:
    """
    Get all upsell suggestions made to a specific phone number.

    Args:
        phone: Normalized phone number

    Returns:
        List of upsell suggestions made to this lead
    """
    return _upsell_suggestions.get(phone, [])


def has_suggested_fb300(phone: str) -> bool:
    """
    Check if FB300 has already been suggested to this lead.

    Used to avoid repetitive upsell suggestions in the same conversation.

    Args:
        phone: Normalized phone number

    Returns:
        True if FB300 has already been suggested
    """
    suggestions = get_upsell_suggestions(phone)
    return any(s.to_product == "FB300" for s in suggestions)


def should_suggest_upsell(phone: str, message: str) -> bool:
    """
    Determine if an upsell from FBM100 to FB300 should be suggested.

    The suggestion should be made when:
    1. User shows interest in FBM100 (detected via keywords)
    2. FB300 hasn't been suggested yet in this conversation

    Args:
        phone: Normalized phone number
        message: User's message text

    Returns:
        True if upsell should be suggested
    """
    # Check if FBM100 interest is detected
    if not detect_fbm100_interest(message):
        return False

    # Check if we already suggested FB300 to this lead
    if has_suggested_fb300(phone):
        logger.debug(
            "FB300 already suggested to this lead",
            extra={"phone": phone},
        )
        return False

    logger.info(
        "Upsell opportunity detected: FBM100 -> FB300",
        extra={"phone": phone, "message_preview": message[:50]},
    )
    return True


def generate_fb300_suggestion() -> str:
    """
    Generate a consultive suggestion for FB300.

    The suggestion is crafted to be:
    - Consultive, not pushy
    - Informative about benefits
    - Positioned as an "upgrade option"

    Returns:
        Formatted suggestion text for injection into agent context
    """
    suggestion = """
=== SUGESTÃO DE UPSELL (TOM CONSULTIVO) ===
O lead demonstrou interesse na Formadora Manual FBM100.

IMPORTANTE: Apresente a Formadora Semi Automática FB300 como uma opção "acima", de forma consultiva e sem pressão. Use um tom de conselheiro, não de vendedor.

Comparativo para sua referência:
- FBM100 (Manual): 500-600 hambúrgueres/DIA, cuba de 1,5kg
- FB300 (Semi Automática): 300-350 hambúrgueres/HORA, reservatório de 5kg

Pontos a destacar sobre a FB300:
- Produtividade muito superior (300-350/hora vs 500-600/dia)
- Sistema pneumático (menos esforço do operador)
- Reservatório maior (5kg vs 1,5kg)
- Estrutura em inox 304 com acabamento jateado
- Ideal para quem planeja crescer

EXEMPLO DE ABORDAGEM CONSULTIVA:
"A FBM100 é uma ótima opção para começar! Mas se você planeja aumentar a produção, vale conhecer a FB300 - ela é semi-automática e produz muito mais por hora. Posso te contar mais sobre as duas opções?"

⚠️ NÃO pressione a venda. Apenas apresente como alternativa se fizer sentido para o lead.
"""
    return suggestion


def register_upsell_suggestion(
    phone: str,
    from_product: str,
    to_product: str,
    message_trigger: str,
) -> None:
    """
    Register an upsell suggestion in the conversation context.

    This tracks when upsells are made to:
    1. Avoid repetitive suggestions
    2. Enable analytics on upsell effectiveness
    3. Provide context for future conversations

    Args:
        phone: Normalized phone number
        from_product: Product the lead was interested in (e.g., "FBM100")
        to_product: Product suggested as upgrade (e.g., "FB300")
        message_trigger: The message that triggered the upsell
    """
    suggestion = UpsellSuggestion(
        phone=phone,
        from_product=from_product,
        to_product=to_product,
        timestamp=datetime.now().isoformat(),
        message_trigger=message_trigger[:200],  # Limit trigger message size
    )

    if phone not in _upsell_suggestions:
        _upsell_suggestions[phone] = []

    _upsell_suggestions[phone].append(suggestion)

    logger.info(
        "Upsell suggestion registered",
        extra={
            "phone": phone,
            "from_product": from_product,
            "to_product": to_product,
        },
    )


def clear_upsell_history(phone: str) -> None:
    """
    Clear upsell suggestion history for a phone number.

    Useful for testing or starting a fresh conversation.

    Args:
        phone: Normalized phone number
    """
    if phone in _upsell_suggestions:
        del _upsell_suggestions[phone]
        logger.debug(
            "Upsell history cleared",
            extra={"phone": phone},
        )


def get_upsell_context_for_agent(phone: str, message: str) -> Optional[str]:
    """
    Get upsell context to inject into the agent's response generation.

    This is the main function to be called from the SDR agent.
    It checks if an upsell should be suggested and returns the
    appropriate context for the agent.

    Args:
        phone: Normalized phone number
        message: User's message text

    Returns:
        Upsell suggestion context string, or None if no upsell should be made
    """
    if not should_suggest_upsell(phone, message):
        return None

    # Register that we're making this suggestion
    register_upsell_suggestion(
        phone=phone,
        from_product="FBM100",
        to_product="FB300",
        message_trigger=message,
    )

    # Generate and return the suggestion context
    return generate_fb300_suggestion()
