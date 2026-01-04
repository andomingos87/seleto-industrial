"""
SDR Agent - Conversational agent for lead qualification.

This module implements the main agent logic with system prompt loading,
conversation memory, response generation, and knowledge base integration (US-003).
"""

import asyncio
import time
from typing import Optional

from agno.agent import Agent
from agno.models.openai import OpenAIChat

from src.config.settings import settings
from src.services.conversation_memory import conversation_memory
from src.services.data_extraction import extract_lead_data
from src.services.knowledge_base import (
    get_knowledge_base,
    is_commercial_query,
    is_too_technical,
    register_technical_question,
)
from src.services.unavailable_products import get_espeto_context_for_agent
from src.services.upsell import get_upsell_context_for_agent
from src.services.lead_persistence import get_persisted_lead_data, persist_lead_data
from src.services.prompt_loader import get_system_prompt_path, load_system_prompt_from_xml
from src.services.temperature_classification import classify_lead, should_classify_lead
from src.utils.logging import get_logger, set_phone

logger = get_logger(__name__)

# System prompt loaded at module level (cached for performance)
# Cache is cleared on process restart, allowing prompt changes to take effect
_system_prompt: Optional[str] = None


def _load_system_prompt(force_reload: bool = False) -> str:
    """
    Load system prompt from XML file.

    The prompt is cached in memory for performance. Cache is automatically
    cleared on process restart, so changes to the XML file take effect
    after restarting the service.

    Args:
        force_reload: If True, reload from file even if cached

    Returns:
        System prompt as formatted string

    Raises:
        FileNotFoundError: If prompt XML file doesn't exist
        ValueError: If prompt path is invalid (security check)
        ET.ParseError: If XML is malformed
    """
    global _system_prompt
    if _system_prompt is None or force_reload:
        prompt_path = get_system_prompt_path("sp_agente_v1.xml")
        logger.info(
            "Loading system prompt from XML",
            extra={"path": str(prompt_path), "force_reload": force_reload},
        )
        _system_prompt = load_system_prompt_from_xml(prompt_path)
        logger.info(
            "System prompt loaded successfully",
            extra={"prompt_length": len(_system_prompt), "path": str(prompt_path)},
        )
    return _system_prompt


def reload_system_prompt() -> str:
    """
    Force reload the system prompt from XML file.

    Useful for development/testing to reload prompt without restarting.

    Returns:
        Newly loaded system prompt
    """
    return _load_system_prompt(force_reload=True)


def create_sdr_agent() -> Agent:
    """
    Create and configure the SDR agent.

    Returns:
        Configured Agent instance

    Raises:
        ValueError: If OPENAI_API_KEY is not configured
    """
    # Validate API key before creating model (TECH-035)
    if not settings.OPENAI_API_KEY:
        error_msg = (
            "OPENAI_API_KEY not configured. "
            "Please set OPENAI_API_KEY in .env file or environment variables."
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

    logger.info(
        "OpenAI API key configured",
        extra={"model": settings.OPENAI_MODEL, "key_length": len(settings.OPENAI_API_KEY)},
    )

    system_prompt = _load_system_prompt()

    agent = Agent(
        name="Seleto SDR",
        model=OpenAIChat(
            id=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,  # Pass API key explicitly (TECH-035)
        ),
        description="Agente de qualificação de leads para Seleto Industrial",
        instructions=[system_prompt],
        markdown=True,
    )

    logger.info("SDR agent created and configured")
    return agent


# Global agent instance
sdr_agent = create_sdr_agent()


async def process_message(phone: str, message: str, sender_name: Optional[str] = None) -> str:
    """
    Process an incoming message and generate a response.

    This function:
    1. Adds the user message to conversation history
    2. Checks if it's the first message (to send greeting)
    3. Generates agent response using conversation context
    4. Adds agent response to conversation history
    5. Returns the response text

    Args:
        phone: Phone number of the sender (will be normalized)
        message: Message text from the user
        sender_name: Optional sender name

    Returns:
        Response text from the agent

    Raises:
        Exception: If agent processing fails
    """
    from src.utils.validation import normalize_phone

    normalized_phone = normalize_phone(phone)
    if not normalized_phone:
        raise ValueError(f"Invalid phone number: {phone}")

    # Set phone in context for logging
    set_phone(normalized_phone)

    start_time = time.perf_counter()

    # Check if this is the first message
    is_first = conversation_memory.is_first_message(normalized_phone)

    # Get persisted lead data (from memory or Supabase)
    lead_data = get_persisted_lead_data(normalized_phone)

    # Extract new data from user message (US-002: coleta progressiva)
    extracted_data = await extract_lead_data(message, current_data=lead_data)

    # Persist extracted data (even if partial - US-002 requirement)
    if extracted_data:
        await persist_lead_data(normalized_phone, extracted_data)
        # Update local lead_data with new extracted data
        lead_data = {**lead_data, **extracted_data}

    # US-006/TECH-011: Classify lead temperature if criteria met
    if should_classify_lead(lead_data):
        try:
            # Get conversation history for classification
            conv_history = conversation_memory.get_messages_for_llm(
                normalized_phone, max_messages=20
            )
            temperature, justification = await classify_lead(
                phone=normalized_phone,
                lead_data=lead_data,
                conversation_history=conv_history,
            )
            if temperature:
                logger.info(
                    "Lead classified successfully",
                    extra={
                        "phone": normalized_phone,
                        "temperature": temperature,
                        "justification_preview": justification[:50] if justification else "",
                    },
                )
                # Update local lead_data with temperature
                lead_data["temperature"] = temperature
                lead_data["temperature_justification"] = justification
        except Exception as e:
            logger.warning(
                "Failed to classify lead temperature",
                extra={"phone": normalized_phone, "error": str(e)},
            )
            # Continue without classification - non-blocking

    # Reset question count when user responds (US-002: controle de ritmo)
    conversation_memory.reset_question_count(normalized_phone)

    # Get conversation history for context
    conversation_history = conversation_memory.get_messages_for_llm(normalized_phone, max_messages=20)

    # Get question count to enforce rate limit (US-002: máximo 2 perguntas diretas)
    question_count = conversation_memory.get_question_count(normalized_phone)

    # US-003: Apply knowledge base guardrails
    kb = get_knowledge_base()

    # Check for commercial query (guardrail: no prices/discounts/delivery)
    if is_commercial_query(message):
        logger.info(
            "Commercial query detected - applying guardrail",
            extra={"phone": normalized_phone, "message_preview": message[:50]},
        )
        commercial_response = kb.get_commercial_response()

        # Add messages to history
        conversation_memory.add_message(normalized_phone, "user", message)
        conversation_memory.add_message(normalized_phone, "assistant", commercial_response)

        return commercial_response

    # Check for overly technical query (escalate to human specialist)
    if is_too_technical(message):
        logger.info(
            "Technical query detected - registering for specialist follow-up",
            extra={"phone": normalized_phone, "message_preview": message[:50]},
        )
        # Register the question for follow-up
        register_technical_question(
            phone=normalized_phone,
            question=message,
            context=f"Lead data: {lead_data}" if lead_data else None,
        )
        technical_response = kb.get_technical_escalation_response()

        # Add messages to history
        conversation_memory.add_message(normalized_phone, "user", message)
        conversation_memory.add_message(normalized_phone, "assistant", technical_response)

        return technical_response

    # Build context message for the agent
    context_parts = []

    # US-003: Add knowledge base context if query is about equipment
    if kb.is_equipment_query(message):
        response_type, knowledge_content = kb.get_equipment_response(message)
        if response_type == "knowledge" and knowledge_content:
            context_parts.append("\n=== BASE DE CONHECIMENTO - EQUIPAMENTOS ===")
            context_parts.append("Use as informações abaixo para responder sobre equipamentos:")
            context_parts.append(knowledge_content)
            context_parts.append("\n⚠️ IMPORTANTE: NÃO informe preços, descontos ou prazos de entrega.")
            logger.debug(
                "Knowledge base context injected",
                extra={"phone": normalized_phone, "knowledge_size": len(knowledge_content)},
            )

    # US-004: Check for upsell opportunity (FBM100 -> FB300)
    upsell_context = get_upsell_context_for_agent(normalized_phone, message)
    if upsell_context:
        context_parts.append(upsell_context)
        logger.info(
            "Upsell context injected (FBM100 -> FB300)",
            extra={"phone": normalized_phone},
        )

    # US-005: Check for interest in unavailable products (espeto line)
    espeto_context = get_espeto_context_for_agent(normalized_phone, message)
    if espeto_context:
        context_parts.append(espeto_context)
        logger.info(
            "Espeto unavailable product context injected",
            extra={"phone": normalized_phone},
        )

    # Add lead data context if available
    if lead_data:
        context_parts.append("\n=== DADOS COLETADOS DO LEAD ===")
        for key, value in lead_data.items():
            if value:
                context_parts.append(f"{key}: {value}")

    # Add question count context (for rate control)
    if question_count >= 2:
        context_parts.append(
            f"\n⚠️ ATENÇÃO: Você já fez {question_count} perguntas diretas seguidas. "
            "NÃO faça mais perguntas diretas nesta resposta. "
            "Use as informações já coletadas para contextualizar sua resposta ou aguarde mais informações do lead."
        )

    # Build the full message with context
    full_message = message
    if context_parts:
        full_message = "\n".join(context_parts) + "\n\n=== MENSAGEM DO LEAD ===\n" + message

    # Generate response using the agent
    try:
        # Use the agent's run method
        # For Agno, we use run() which handles the conversation
        # The run() method expects 'input' as the first positional argument
        # We'll use the phone as a session identifier via thread_id if supported
        # Note: run() may be synchronous, so we run it in a thread pool
        try:
            response = await asyncio.to_thread(
                sdr_agent.run,
                full_message,  # input as positional argument
                stream=False,
                thread_id=normalized_phone,  # Use phone as thread ID for conversation continuity
            )
        except TypeError as e:
            # If thread_id is not supported, use run without it
            if "thread_id" in str(e) or "unexpected keyword" in str(e):
                response = await asyncio.to_thread(
                    sdr_agent.run,
                    full_message,  # input as positional argument
                    stream=False,
                )
            else:
                raise

        # Extract response text
        response_text = ""
        if hasattr(response, "content"):
            response_text = response.content
        elif hasattr(response, "messages") and response.messages:
            # Get the last message from the response
            last_msg = response.messages[-1]
            if hasattr(last_msg, "content"):
                response_text = last_msg.content
            else:
                response_text = str(last_msg)
        elif isinstance(response, str):
            response_text = response
        else:
            # Try to get text from response object
            response_text = str(response)

        # Ensure response is not empty
        if not response_text or not response_text.strip():
            logger.warning("Empty response from agent, using fallback")
            if is_first:
                response_text = (
                    "Olá! Seja bem-vindo à Seleto Industrial 👋\n"
                    "Sou seu assistente virtual e estou aqui para ajudar.\n"
                    "Pode me contar um pouco sobre o que está buscando?"
                )
            else:
                response_text = "Desculpe, não entendi. Pode repetir?"

        # Check if response contains direct questions (simple heuristic)
        # This is a basic check - the prompt should also enforce this
        question_indicators = ["?", "pode", "você", "qual", "quando", "onde", "como", "quanto"]
        has_question = "?" in response_text
        is_direct_question = has_question and any(
            indicator in response_text.lower() for indicator in question_indicators
        )

        # Track question count for rate control (US-002)
        if is_direct_question:
            conversation_memory.increment_question_count(normalized_phone)
            question_count = conversation_memory.get_question_count(normalized_phone)
            if question_count > 2:
                logger.warning(
                    "Agent exceeded question rate limit",
                    extra={
                        "phone": normalized_phone,
                        "question_count": question_count,
                    },
                )

        # Add user message to conversation history (after processing)
        conversation_memory.add_message(normalized_phone, "user", message)

        # Add agent response to conversation history
        conversation_memory.add_message(normalized_phone, "assistant", response_text)

        # Calculate response time
        duration_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            "Message processed successfully",
            extra={
                "phone": normalized_phone,
                "is_first_message": is_first,
                "response_length": len(response_text),
                "duration_ms": duration_ms,
                "conversation_length": len(conversation_history) + 2,  # +2 for user and assistant messages
            },
        )

        # Check if response time exceeds 5 seconds (requirement: < 5s)
        if duration_ms > 5000:
            logger.warning(
                "Response time exceeded 5 seconds",
                extra={
                    "phone": normalized_phone,
                    "duration_ms": duration_ms,
                },
            )

        return response_text

    except Exception as e:
        logger.error(
            "Failed to process message with agent",
            extra={
                "phone": normalized_phone,
                "error": str(e),
            },
            exc_info=True,
        )

        # Fallback response
        if is_first:
            fallback_response = (
                "Olá! Seja bem-vindo à Seleto Industrial 👋\n"
                "Sou seu assistente virtual e estou aqui para ajudar.\n"
                "Pode me contar um pouco sobre o que está buscando?"
            )
        else:
            fallback_response = (
                "Desculpe, tive um problema técnico. "
                "Pode repetir sua mensagem?"
            )

        # Add user message to history
        conversation_memory.add_message(normalized_phone, "user", message)

        # Add fallback to history
        conversation_memory.add_message(normalized_phone, "assistant", fallback_response)

        return fallback_response
