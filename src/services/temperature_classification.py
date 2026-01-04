"""
Temperature classification service for lead qualification.

This service classifies leads as frio (cold), morno (warm), or quente (hot)
based on engagement, data completeness, volume, and urgency criteria.

Implements US-006 and TECH-011 from the product backlog.
"""

import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from openai import AsyncOpenAI

from src.config.settings import settings
from src.services.conversation_persistence import get_supabase_client
from src.utils.logging import get_logger
from src.utils.validation import normalize_phone

logger = get_logger(__name__)

# Base directory for prompts
_PROMPTS_BASE_DIR = Path(__file__).parent.parent.parent / "prompts" / "system_prompt"

# Required fields for lead qualification
REQUIRED_FIELDS = ["name", "company", "city", "product"]
OPTIONAL_FIELDS = ["volume", "urgency", "uf", "knows_seleto"]
ALL_FIELDS = REQUIRED_FIELDS + OPTIONAL_FIELDS


def load_temperature_prompt() -> str:
    """
    Load the temperature classification prompt from XML file.

    The prompt is loaded from prompts/system_prompt/sp_calcula_temperatura.xml
    and formatted for use with the LLM.

    Returns:
        Formatted prompt string for temperature classification

    Raises:
        FileNotFoundError: If the XML file doesn't exist
        ValueError: If the XML structure is invalid
    """
    xml_path = _PROMPTS_BASE_DIR / "sp_calcula_temperatura.xml"

    if not xml_path.exists():
        logger.error(f"Temperature prompt file not found: {xml_path}")
        raise FileNotFoundError(f"Temperature prompt XML file not found: {xml_path}")

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        prompt_parts = []

        # Extract instructions
        instrucoes = root.find("instrucoes")
        if instrucoes is not None:
            prompt_parts.append("=== INSTRUCOES ===")
            for child in instrucoes:
                if child.tag == "fluxo":
                    for item in child.findall("item"):
                        if item.text:
                            prompt_parts.append(f"- {item.text.strip()}")
                elif child.text:
                    prompt_parts.append(child.text.strip())

        # Extract rules
        regra = root.find("regra")
        if regra is not None:
            prompt_parts.append("\n=== REGRAS ===")
            for item in regra.findall("item"):
                if item.text:
                    prompt_parts.append(f"- {item.text.strip()}")

        # Extract criteria
        criterios = root.find("criterios")
        if criterios is not None:
            prompt_parts.append("\n=== CRITERIOS DE CLASSIFICACAO ===")

            for temp_type in ["frio", "morno", "quente"]:
                temp_elem = criterios.find(temp_type)
                if temp_elem is not None:
                    prompt_parts.append(f"\n{temp_type.upper()}:")
                    for item in temp_elem.findall("item"):
                        if item.text:
                            prompt_parts.append(f"  - {item.text.strip()}")

        full_prompt = "\n".join(prompt_parts)

        logger.info(
            "Temperature prompt loaded successfully",
            extra={"prompt_length": len(full_prompt)},
        )

        return full_prompt

    except ET.ParseError as e:
        logger.error(f"Failed to parse temperature prompt XML: {e}")
        raise ValueError(f"Invalid XML structure in temperature prompt: {e}")
    except Exception as e:
        logger.error(f"Unexpected error loading temperature prompt: {e}", exc_info=True)
        raise


def calculate_engagement_score(
    phone: str,
    conversation_history: Optional[List[Dict]] = None,
) -> float:
    """
    Calculate engagement score based on conversation history.

    The score is based on:
    - Number of messages from the user
    - Response rate (user messages / assistant messages)
    - Average message length
    - Number of questions answered

    Args:
        phone: Lead's phone number (normalized)
        conversation_history: List of conversation messages with 'role' and 'content'

    Returns:
        Engagement score between 0.0 (low) and 1.0 (high)
    """
    if not conversation_history:
        return 0.0

    user_messages = [msg for msg in conversation_history if msg.get("role") == "user"]
    assistant_messages = [msg for msg in conversation_history if msg.get("role") == "assistant"]

    if not user_messages:
        return 0.0

    # Calculate metrics
    num_user_messages = len(user_messages)
    num_assistant_messages = len(assistant_messages)

    # Response rate (user responded to assistant's messages)
    response_rate = min(num_user_messages / max(num_assistant_messages, 1), 1.0)

    # Average message length (longer messages indicate more engagement)
    avg_message_length = sum(len(msg.get("content", "")) for msg in user_messages) / num_user_messages
    # Normalize to 0-1 (assume 100 chars is good engagement)
    length_score = min(avg_message_length / 100, 1.0)

    # Message count score (more messages = more engagement)
    # Assume 5+ messages is high engagement
    message_count_score = min(num_user_messages / 5, 1.0)

    # Combine scores with weights
    engagement_score = (
        response_rate * 0.3 +
        length_score * 0.3 +
        message_count_score * 0.4
    )

    logger.debug(
        "Engagement score calculated",
        extra={
            "phone": phone,
            "user_messages": num_user_messages,
            "response_rate": response_rate,
            "length_score": length_score,
            "message_count_score": message_count_score,
            "final_score": engagement_score,
        },
    )

    return round(engagement_score, 2)


def calculate_completeness_score(lead_data: Dict[str, Optional[str]]) -> float:
    """
    Calculate data completeness score based on collected lead information.

    The score considers:
    - Required fields (name, company, city, product) - weight: 60%
    - Optional fields (volume, urgency, uf, knows_seleto) - weight: 40%

    Args:
        lead_data: Dictionary with lead data fields

    Returns:
        Completeness score between 0.0 (no data) and 1.0 (all data collected)
    """
    if not lead_data:
        return 0.0

    # Count filled required fields
    required_filled = sum(
        1 for field in REQUIRED_FIELDS
        if lead_data.get(field) and str(lead_data.get(field)).strip()
    )
    required_score = required_filled / len(REQUIRED_FIELDS)

    # Count filled optional fields
    optional_filled = sum(
        1 for field in OPTIONAL_FIELDS
        if lead_data.get(field) and str(lead_data.get(field)).strip()
    )
    optional_score = optional_filled / len(OPTIONAL_FIELDS) if OPTIONAL_FIELDS else 0

    # Weighted score
    completeness_score = required_score * 0.6 + optional_score * 0.4

    logger.debug(
        "Completeness score calculated",
        extra={
            "required_filled": required_filled,
            "optional_filled": optional_filled,
            "required_score": required_score,
            "optional_score": optional_score,
            "final_score": completeness_score,
        },
    )

    return round(completeness_score, 2)


def _parse_llm_response(response_text: str) -> Tuple[str, str]:
    """
    Parse LLM response to extract temperature and justification.

    The response should contain one of: frio, morno, quente
    The justification is extracted from any additional text.

    Args:
        response_text: Raw response from LLM

    Returns:
        Tuple of (temperature, justification)
    """
    response_lower = response_text.lower().strip()

    # Extract temperature
    temperature = "morno"  # Default fallback
    if "quente" in response_lower:
        temperature = "quente"
    elif "frio" in response_lower:
        temperature = "frio"
    elif "morno" in response_lower:
        temperature = "morno"

    # Extract justification (everything after the temperature word)
    justification = response_text.strip()
    for temp in ["quente", "morno", "frio"]:
        if temp in justification.lower():
            # Get text after the temperature word
            idx = justification.lower().find(temp)
            remaining = justification[idx + len(temp):].strip()
            if remaining:
                # Clean up punctuation
                remaining = remaining.lstrip(".:- ")
                if remaining:
                    justification = remaining
                    break

    # If no justification extracted, create a default one
    if justification.lower() in ["frio", "morno", "quente"]:
        justification = f"Lead classificado como {temperature} com base nos dados coletados."

    return temperature, justification


async def calculate_temperature(
    lead_data: Dict[str, Optional[str]],
    conversation_summary: str,
    conversation_history: Optional[List[Dict]] = None,
    phone: Optional[str] = None,
) -> Tuple[str, str]:
    """
    Calculate lead temperature using LLM classification.

    This function:
    1. Loads the temperature classification prompt
    2. Calculates engagement and completeness scores
    3. Sends data to LLM for classification
    4. Returns temperature and justification

    Args:
        lead_data: Dictionary with collected lead data
        conversation_summary: Summary of the conversation
        conversation_history: Optional list of conversation messages
        phone: Optional phone number for logging

    Returns:
        Tuple of (temperature, justification) where temperature is one of:
        - "frio" (cold): Low engagement, incomplete data
        - "morno" (warm): Moderate engagement, partial data
        - "quente" (hot): High engagement, complete data, urgency

    Raises:
        ValueError: If OpenAI API key is not configured
    """
    if not settings.OPENAI_API_KEY:
        error_msg = "OpenAI API key not configured for temperature classification"
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Calculate scores
    engagement_score = calculate_engagement_score(phone or "", conversation_history)
    completeness_score = calculate_completeness_score(lead_data)

    # Load prompt
    try:
        base_prompt = load_temperature_prompt()
    except Exception as e:
        logger.warning(f"Failed to load temperature prompt, using default: {e}")
        base_prompt = _get_default_temperature_prompt()

    # Build context for LLM
    context_parts = [
        base_prompt,
        "\n\n=== DADOS DO LEAD ===",
    ]

    # Add lead data
    for field in ALL_FIELDS:
        value = lead_data.get(field)
        if value:
            context_parts.append(f"- {field}: {value}")
        else:
            context_parts.append(f"- {field}: (nao informado)")

    # Add calculated scores
    context_parts.extend([
        f"\n=== METRICAS CALCULADAS ===",
        f"- Score de Engajamento: {engagement_score:.0%}",
        f"- Score de Completude: {completeness_score:.0%}",
    ])

    # Add urgency context
    urgency = lead_data.get("urgency", "").lower()
    if urgency:
        if "alta" in urgency or "urgente" in urgency:
            context_parts.append("- Urgencia: ALTA (favorece classificacao quente)")
        elif "baixa" in urgency or "sem" in urgency:
            context_parts.append("- Urgencia: BAIXA (favorece classificacao morno ou frio)")
        else:
            context_parts.append(f"- Urgencia: {urgency}")

    # Add volume context
    volume = lead_data.get("volume", "")
    if volume:
        context_parts.append(f"- Volume solicitado: {volume}")

    # Add conversation summary
    if conversation_summary:
        context_parts.extend([
            "\n=== RESUMO DA CONVERSA ===",
            conversation_summary,
        ])

    # Build final prompt
    full_prompt = "\n".join(context_parts)
    full_prompt += "\n\n=== RESPOSTA ===\nClassifique este lead como frio, morno ou quente. Explique brevemente o motivo."

    try:
        # Call OpenAI
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Voce e um especialista em classificacao de leads. "
                        "Analise os dados fornecidos e classifique o lead como: frio, morno ou quente. "
                        "Responda com a classificacao seguida de uma breve justificativa."
                    ),
                },
                {"role": "user", "content": full_prompt},
            ],
            temperature=0.2,  # Low temperature for consistent classification
            max_tokens=150,
        )

        # Extract response
        response_text = ""
        if response.choices and len(response.choices) > 0:
            response_text = response.choices[0].message.content or ""

        # Parse response
        temperature, justification = _parse_llm_response(response_text)

        logger.info(
            "Temperature calculated successfully",
            extra={
                "phone": phone or "unknown",
                "temperature": temperature,
                "engagement_score": engagement_score,
                "completeness_score": completeness_score,
                "justification_preview": justification[:50] if justification else "",
            },
        )

        return temperature, justification

    except Exception as e:
        logger.error(
            "Failed to calculate temperature via LLM",
            extra={"phone": phone or "unknown", "error": str(e)},
            exc_info=True,
        )

        # Fallback classification based on scores
        return _fallback_classification(engagement_score, completeness_score, lead_data)


def _fallback_classification(
    engagement_score: float,
    completeness_score: float,
    lead_data: Dict[str, Optional[str]],
) -> Tuple[str, str]:
    """
    Fallback classification when LLM is unavailable.

    Uses simple rule-based classification based on scores.

    Args:
        engagement_score: Engagement score (0-1)
        completeness_score: Completeness score (0-1)
        lead_data: Lead data dictionary

    Returns:
        Tuple of (temperature, justification)
    """
    # Check urgency
    urgency = lead_data.get("urgency", "").lower()
    has_high_urgency = "alta" in urgency or "urgente" in urgency

    # Combined score
    combined_score = (engagement_score + completeness_score) / 2

    if combined_score >= 0.7 or (combined_score >= 0.5 and has_high_urgency):
        temperature = "quente"
        justification = f"Lead com alto engajamento ({engagement_score:.0%}) e dados completos ({completeness_score:.0%})"
        if has_high_urgency:
            justification += " com urgencia alta"
    elif combined_score >= 0.4:
        temperature = "morno"
        justification = f"Lead com engajamento moderado ({engagement_score:.0%}) e dados parciais ({completeness_score:.0%})"
    else:
        temperature = "frio"
        justification = f"Lead com baixo engajamento ({engagement_score:.0%}) e poucos dados ({completeness_score:.0%})"

    logger.info(
        "Fallback temperature classification used",
        extra={
            "temperature": temperature,
            "engagement_score": engagement_score,
            "completeness_score": completeness_score,
        },
    )

    return temperature, justification


def _get_default_temperature_prompt() -> str:
    """
    Get default temperature classification prompt when XML is unavailable.

    Returns:
        Default prompt string
    """
    return """
=== INSTRUCOES ===
Classifique o lead como frio, morno ou quente com base nos criterios abaixo.

=== CRITERIOS DE CLASSIFICACAO ===

FRIO:
- Lead nao respondeu a maioria das perguntas
- Poucos dados coletados (nome ou empresa nao informados)
- Nenhum interesse claro em produtos
- Sem urgencia de compra

MORNO:
- Lead respondeu a algumas perguntas
- Dados parcialmente completos (nome e empresa informados)
- Interesse em produtos mas sem volume definido
- Urgencia baixa ou nao informada

QUENTE:
- Lead respondeu a todas as perguntas
- Dados completos (nome, empresa, cidade, produto, volume)
- Volume significativo solicitado
- Urgencia alta de compra
- Ja conhece a Seleto ou tem historico de compra
"""


async def update_lead_temperature(
    phone: str,
    temperature: str,
    justification: str,
) -> bool:
    """
    Update lead temperature in the database.

    Persists the temperature classification and justification to Supabase
    via the conversation_context table.

    Args:
        phone: Lead's phone number (will be normalized)
        temperature: Temperature classification (frio, morno, quente)
        justification: Justification text for the classification

    Returns:
        True if update was successful, False otherwise
    """
    normalized_phone = normalize_phone(phone)
    if not normalized_phone:
        logger.warning(f"Invalid phone number for temperature update: {phone}")
        return False

    # Validate temperature value
    valid_temperatures = ["frio", "morno", "quente"]
    if temperature.lower() not in valid_temperatures:
        logger.warning(f"Invalid temperature value: {temperature}")
        temperature = "morno"  # Default fallback

    client = get_supabase_client()
    if not client:
        logger.warning("Supabase not available - temperature not persisted")
        return False

    try:
        # First, get existing context
        response = (
            client.table("conversation_context")
            .select("context_data")
            .eq("lead_phone", normalized_phone)
            .execute()
        )

        existing_context = {}
        if response.data and len(response.data) > 0:
            existing_context = response.data[0].get("context_data", {})
            if not isinstance(existing_context, dict):
                existing_context = {}

        # Update with temperature data
        existing_context.update({
            "temperature": temperature.lower(),
            "temperature_justification": justification,
            "temperature_updated_at": datetime.utcnow().isoformat(),
        })

        # Upsert to database
        upsert_response = (
            client.table("conversation_context")
            .upsert(
                {
                    "lead_phone": normalized_phone,
                    "context_data": existing_context,
                    "updated_at": datetime.utcnow().isoformat(),
                },
                on_conflict="lead_phone",
            )
            .execute()
        )

        if upsert_response.data:
            logger.info(
                "Lead temperature updated successfully",
                extra={
                    "phone": normalized_phone,
                    "temperature": temperature,
                },
            )
            return True
        else:
            logger.warning("No data returned from temperature update")
            return False

    except Exception as e:
        logger.error(
            "Failed to update lead temperature",
            extra={
                "phone": normalized_phone,
                "temperature": temperature,
                "error": str(e),
            },
            exc_info=True,
        )
        return False


def should_classify_lead(lead_data: Dict[str, Optional[str]]) -> bool:
    """
    Determine if a lead should be classified.

    Classification should happen when:
    - At least 2 required fields are filled (minimum data for classification)
    - Lead hasn't been classified recently (within last 10 messages)

    Args:
        lead_data: Dictionary with lead data fields

    Returns:
        True if lead should be classified, False otherwise
    """
    if not lead_data:
        return False

    # Count filled required fields
    required_filled = sum(
        1 for field in REQUIRED_FIELDS
        if lead_data.get(field) and str(lead_data.get(field)).strip()
    )

    # Need at least 2 required fields to classify
    min_required = 2
    should_classify = required_filled >= min_required

    # Check if already classified (has temperature)
    already_classified = lead_data.get("temperature") is not None

    # If already classified, only reclassify if significant new data
    if already_classified:
        # Count total filled fields
        total_filled = sum(
            1 for field in ALL_FIELDS
            if lead_data.get(field) and str(lead_data.get(field)).strip()
        )
        # Reclassify if we now have more complete data (e.g., 6+ fields)
        should_classify = total_filled >= 6

    logger.debug(
        "Classification check",
        extra={
            "required_filled": required_filled,
            "already_classified": already_classified,
            "should_classify": should_classify,
        },
    )

    return should_classify


async def classify_lead(
    phone: str,
    lead_data: Dict[str, Optional[str]],
    conversation_history: Optional[List[Dict]] = None,
) -> Tuple[Optional[str], Optional[str]]:
    """
    High-level function to classify a lead and persist the result.

    This function:
    1. Checks if the lead should be classified
    2. Calculates the temperature using LLM
    3. Persists the result to the database
    4. Returns the classification

    Args:
        phone: Lead's phone number
        lead_data: Dictionary with lead data
        conversation_history: Optional conversation history

    Returns:
        Tuple of (temperature, justification) or (None, None) if not classified
    """
    # Check if we should classify
    if not should_classify_lead(lead_data):
        logger.debug(f"Lead {phone} does not meet criteria for classification")
        return None, None

    # Build conversation summary
    conversation_summary = ""
    if conversation_history:
        user_messages = [
            msg.get("content", "")
            for msg in conversation_history
            if msg.get("role") == "user"
        ]
        if user_messages:
            # Get last 5 user messages as summary
            recent_messages = user_messages[-5:]
            conversation_summary = " | ".join(recent_messages)

    # Calculate temperature
    temperature, justification = await calculate_temperature(
        lead_data=lead_data,
        conversation_summary=conversation_summary,
        conversation_history=conversation_history,
        phone=phone,
    )

    # Persist to database
    await update_lead_temperature(phone, temperature, justification)

    return temperature, justification
