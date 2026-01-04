"""
Unavailable Products Service - US-005: Tratar interesse em produto indisponível.

This module provides functionality to:
- Detect interest in the espeto (skewer) production line
- Inform that the project is under improvement (expected March/2026)
- Register interest for future contact
- Suggest CT200 (cube cutting machine) as an alternative when appropriate
"""

import re
from dataclasses import dataclass
from datetime import datetime

from src.services.knowledge_base import get_knowledge_base
from src.utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ProductInterest:
    """Record of a lead's interest in an unavailable product."""

    phone: str
    product: str
    timestamp: str
    context: str | None = None


# In-memory storage for product interests (can be moved to Supabase later)
_product_interests: list[ProductInterest] = []


# Keywords that indicate interest in espeto/skewer production line
ESPETO_KEYWORDS = [
    # Direct mentions
    "espeto",
    "espetos",
    "espetinho",
    "espetinhos",
    "espetar",
    # Machine references
    "linha automática para espeto",
    "linha automatica para espeto",
    "máquina de espeto",
    "maquina de espeto",
    "máquina de espetos",
    "maquina de espetos",
    "produção de espeto",
    "producao de espeto",
    "produzir espeto",
    "fabricar espeto",
    "fazer espeto",
    # Production context
    "espetar carne",
    "espetar carnes",
    "carne no palito",
    "espetaria",
    "churrascaria.*espeto",
]

# Keywords that suggest CT200 might be a relevant alternative
# (when lead mentions cutting, cubes, or preparing meat for skewers)
CT200_RELEVANCE_KEYWORDS = [
    # Cutting needs
    "cortar",
    "corte",
    "cubo",
    "cubos",
    "tira",
    "tiras",
    "picar",
    "fatiar",
    # Preparation context
    "preparar carne",
    "preparar a carne",
    "pedaço",
    "pedaços",
    "pedaco",
    "pedacos",
    # Production volume
    "produção",
    "producao",
    "volume",
    "escala",
]


def detect_espeto_interest(message: str) -> bool:
    """
    Detect if the message indicates interest in the espeto production line.

    Args:
        message: User's message text

    Returns:
        True if interest in espeto line is detected
    """
    message_lower = message.lower()

    # Check each keyword pattern
    for keyword in ESPETO_KEYWORDS:
        # Some keywords are regex patterns (contain .*)
        if ".*" in keyword:
            if re.search(keyword, message_lower, re.IGNORECASE):
                logger.debug(
                    f"Espeto interest detected via pattern: {keyword}",
                    extra={"message_preview": message[:50]},
                )
                return True
        else:
            if keyword in message_lower:
                logger.debug(
                    f"Espeto interest detected via keyword: {keyword}",
                    extra={"message_preview": message[:50]},
                )
                return True

    return False


def should_suggest_ct200(message: str, conversation_context: dict | None = None) -> bool:
    """
    Determine if CT200 should be suggested as an alternative.

    CT200 is suggested when:
    - Lead mentions cutting/cubes/strips needs
    - Lead mentions meat preparation context
    - Lead has production volume needs

    Args:
        message: User's message text
        conversation_context: Optional context from conversation history

    Returns:
        True if CT200 should be suggested
    """
    message_lower = message.lower()

    # Check for CT200 relevance keywords in current message
    relevance_score = 0
    matched_keywords = []

    for keyword in CT200_RELEVANCE_KEYWORDS:
        if keyword in message_lower:
            relevance_score += 1
            matched_keywords.append(keyword)

    # Also check conversation context if available
    if conversation_context:
        context_text = str(conversation_context).lower()
        for keyword in CT200_RELEVANCE_KEYWORDS:
            if keyword in context_text and keyword not in matched_keywords:
                relevance_score += 1  # Context keywords also count fully
                matched_keywords.append(f"ctx:{keyword}")

    # Suggest CT200 if we have at least 1 relevance indicator
    should_suggest = relevance_score >= 1

    if should_suggest:
        logger.debug(
            "CT200 suggestion triggered",
            extra={
                "relevance_score": relevance_score,
                "matched_keywords": matched_keywords,
            },
        )

    return should_suggest


def get_unavailable_product_message(product: str = "espeto") -> str:
    """
    Get the message to inform about an unavailable product.

    Args:
        product: Product identifier (currently only "espeto" is supported)

    Returns:
        Formatted message about product unavailability
    """
    if product == "espeto":
        return (
            "No momento não temos a linha de espetos disponível. "
            "O modelo está passando por melhorias e em breve teremos novidades. "
            "Estou registrando seu interesse para que nossa equipe entre em contato "
            "assim que tivermos atualizações sobre o projeto."
        )

    # Default message for other products
    return (
        f"No momento o produto {product} não está disponível. "
        "Estou registrando seu interesse para contato futuro."
    )


def get_ct200_suggestion_message() -> str:
    """
    Get the message suggesting CT200 as an alternative.

    Returns:
        Formatted message suggesting CT200
    """
    return (
        "\n\nEnquanto isso, posso te apresentar uma solução imediata que já resolve "
        "uma etapa essencial do processo: a CT200 – máquina de corte em cubos.\n\n"
        "Ela otimiza grande parte da demanda de preparação e deixa o produto "
        "no padrão ideal para a etapa de espetar, com produção de até 300kg/hora. "
        "Corta carne bovina, frango, suíno, bacon e embutidos.\n\n"
        "Posso te apresentar mais detalhes sobre a cortadora CT200?"
    )


def get_ct200_knowledge() -> str:
    """
    Get knowledge base content about CT200.

    Returns:
        CT200 equipment information from knowledge base
    """
    kb = get_knowledge_base()
    return kb.search_knowledge_base("CT200 cortadora cubo")


def register_product_interest(
    phone: str,
    product: str,
    context: str | None = None,
) -> bool:
    """
    Register a lead's interest in an unavailable product for future contact.

    Args:
        phone: Lead's phone number
        product: Product identifier (e.g., "espeto")
        context: Optional conversation context

    Returns:
        True if registered successfully
    """
    try:
        interest = ProductInterest(
            phone=phone,
            product=product,
            timestamp=datetime.now().isoformat(),
            context=context,
        )

        _product_interests.append(interest)

        logger.info(
            "Product interest registered for future contact",
            extra={
                "phone": phone,
                "product": product,
                "total_interests": len(_product_interests),
            },
        )

        return True

    except Exception as e:
        logger.error(
            "Failed to register product interest",
            extra={
                "phone": phone,
                "product": product,
                "error": str(e),
            },
            exc_info=True,
        )
        return False


def get_pending_product_interests() -> list[ProductInterest]:
    """
    Get all pending product interests for follow-up.

    Returns:
        List of ProductInterest records
    """
    return _product_interests.copy()


def get_product_interests_for_phone(phone: str) -> list[ProductInterest]:
    """
    Get product interests for a specific phone number.

    Args:
        phone: Phone number to look up

    Returns:
        List of ProductInterest records for this phone
    """
    return [i for i in _product_interests if i.phone == phone]


def clear_product_interest(phone: str, product: str | None = None) -> None:
    """
    Clear product interests for a specific phone number.

    Args:
        phone: Phone number
        product: Optional product to filter (clears all if None)
    """
    global _product_interests

    if product:
        _product_interests = [
            i for i in _product_interests if not (i.phone == phone and i.product == product)
        ]
    else:
        _product_interests = [i for i in _product_interests if i.phone != phone]


def get_espeto_context_for_agent(phone: str, message: str) -> str | None:
    """
    Get context to inject into agent when espeto interest is detected.

    This is the main entry point for integrating with the SDR agent.
    It handles detection, message generation, registration, and CT200 suggestion.

    Args:
        phone: Lead's phone number
        message: Current message from lead

    Returns:
        Context string to inject into agent, or None if not applicable
    """
    if not detect_espeto_interest(message):
        return None

    logger.info(
        "Espeto interest detected - preparing context for agent",
        extra={"phone": phone, "message_preview": message[:50]},
    )

    # Register interest for future contact
    register_product_interest(
        phone=phone,
        product="espeto",
        context=f"Mensagem original: {message}",
    )

    # Build context for agent
    context_parts = [
        "\n=== PRODUTO INDISPONÍVEL - LINHA DE ESPETOS ===",
        "O lead demonstrou interesse na linha de espetos (máquina de espetar carnes).",
        "",
        "INSTRUÇÃO: Informe que:",
        "1. No momento não temos a linha de espetos disponível",
        "2. O modelo está passando por melhorias e em breve teremos novidades",
        "3. O interesse foi registrado para contato futuro quando houver atualizações",
        "",
        "Tom: Profissional, empático, demonstrando que a empresa está investindo em melhorias.",
        "NÃO mencione a data de previsão (março/2026) - esta é informação interna.",
    ]

    # Check if we should suggest CT200
    if should_suggest_ct200(message):
        context_parts.extend([
            "",
            "=== SUGESTÃO DE ALTERNATIVA: CT200 ===",
            "O contexto indica que CT200 pode ser uma alternativa relevante.",
            "",
            "INSTRUÇÃO: Após informar sobre indisponibilidade, ofereça a CT200:",
            "- Cortadora de cubos e tiras",
            "- Produção até 300kg/hora",
            "- Ideal para preparar carnes antes de espetar",
            "- Corta bovina, frango, suíno, bacon, embutidos",
            "",
            "Apresente como 'solução imediata que resolve etapa essencial do processo'.",
            "Pergunte se o lead gostaria de conhecer mais sobre a CT200.",
        ])

        # Get CT200 knowledge for additional context
        ct200_knowledge = get_ct200_knowledge()
        if ct200_knowledge:
            context_parts.extend([
                "",
                "=== INFORMAÇÕES CT200 ===",
                ct200_knowledge,
            ])

    return "\n".join(context_parts)
