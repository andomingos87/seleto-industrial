"""
Data extraction service for extracting structured lead data from conversation messages.

This service uses LLM to extract structured data (name, company, city, product, etc.)
from natural language messages in a conversational context.
"""

import json
from typing import Dict, Optional

from openai import AsyncOpenAI

from src.config.settings import settings
from src.utils.logging import get_logger

logger = get_logger(__name__)


# Define the fields we want to extract
LEAD_DATA_FIELDS = {
    "name": "Nome completo do lead",
    "company": "Nome da empresa (opcional)",
    "city": "Cidade",
    "uf": "Estado (UF) - 2 letras",
    "product": "Produto ou necessidade de interesse",
    "volume": "Volume estimado ou capacidade necessária",
    "urgency": "Nível de urgência da compra (ex: alta, média, baixa, sem urgência)",
    "knows_seleto": "Se já conhece ou já comprou da Seleto Industrial (sim/não/desconhecido)",
}


def create_extraction_prompt(current_data: Dict[str, Optional[str]], message: str) -> str:
    """
    Create a prompt for extracting structured data from a message.

    Args:
        current_data: Currently collected data (to avoid re-extracting)
        message: The user's message to extract data from

    Returns:
        Formatted prompt for the LLM
    """
    prompt_parts = [
        "Você é um assistente especializado em extrair informações estruturadas de conversas.",
        "Analise a mensagem do usuário abaixo e extraia APENAS as informações novas que não estão",
        "já presentes nos dados coletados. Se uma informação já foi coletada, não a inclua novamente.",
        "",
        "=== DADOS JÁ COLETADOS ===",
    ]

    # List already collected data
    for field, description in LEAD_DATA_FIELDS.items():
        value = current_data.get(field)
        if value:
            prompt_parts.append(f"- {field}: {value}")

    if not any(current_data.values()):
        prompt_parts.append("(Nenhum dado coletado ainda)")

    prompt_parts.extend([
        "",
        "=== MENSAGEM DO USUÁRIO ===",
        message,
        "",
        "=== INSTRUÇÕES ===",
        "Extraia APENAS as informações novas mencionadas na mensagem acima.",
        "Retorne um JSON válido com os campos abaixo. Use null para campos não mencionados.",
        "",
        "Campos a extrair:",
    ])

    for field, description in LEAD_DATA_FIELDS.items():
        # Skip if already collected
        if current_data.get(field):
            continue
        prompt_parts.append(f"- {field}: {description}")

    prompt_parts.extend([
        "",
        "Formato esperado (JSON válido):",
        "{",
        '  "name": "string ou null",',
        '  "company": "string ou null",',
        '  "city": "string ou null",',
        '  "uf": "string ou null (2 letras maiúsculas)",',
        '  "product": "string ou null",',
        '  "volume": "string ou null",',
        '  "urgency": "string ou null",',
        '  "knows_seleto": "string ou null (sim/não/desconhecido)"',
        "}",
        "",
        "IMPORTANTE:",
        "- Retorne APENAS o JSON, sem texto adicional",
        "- Use null para campos não mencionados",
        "- Se a mensagem não contém informações novas, retorne um objeto vazio {}",
        "- Normalize UF para 2 letras maiúsculas (ex: SP, RJ, MG)",
    ])

    return "\n".join(prompt_parts)


async def extract_lead_data(
    message: str,
    current_data: Optional[Dict[str, Optional[str]]] = None,
) -> Dict[str, Optional[str]]:
    """
    Extract structured lead data from a user message.

    Args:
        message: The user's message text
        current_data: Currently collected data (to avoid duplicates)

    Returns:
        Dictionary with extracted data fields (only new information)
    """
    if current_data is None:
        current_data = {}

    if not settings.OPENAI_API_KEY:
        logger.warning("OpenAI API key not configured, cannot extract data")
        return {}

    try:
        # Create extraction prompt
        prompt = create_extraction_prompt(current_data, message)

        # Use OpenAI to extract data
        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        response = await client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": "Você é um assistente especializado em extrair informações estruturadas de conversas. Retorne APENAS JSON válido, sem texto adicional.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,  # Low temperature for consistent extraction
            max_tokens=500,
        )

        # Extract response text
        response_text = ""
        if response.choices and len(response.choices) > 0:
            response_text = response.choices[0].message.content or ""

        # Parse JSON response
        # Try to extract JSON from response (in case there's extra text)
        response_text = response_text.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            # Extract content between ```json and ```
            lines = response_text.split("\n")
            json_lines = []
            in_json = False
            for line in lines:
                if line.strip().startswith("```"):
                    if "json" in line.lower() or in_json:
                        in_json = not in_json
                    continue
                if in_json:
                    json_lines.append(line)
            response_text = "\n".join(json_lines)
        elif response_text.startswith("```json"):
            response_text = response_text[7:]  # Remove ```json
            if response_text.endswith("```"):
                response_text = response_text[:-3]  # Remove closing ```

        response_text = response_text.strip()

        # Parse JSON
        try:
            extracted_data = json.loads(response_text)
        except json.JSONDecodeError:
            logger.warning(
                "Failed to parse JSON from extraction response",
                extra={
                    "response_text": response_text[:200],  # First 200 chars
                },
            )
            return {}

        # Validate and normalize extracted data
        normalized_data = {}
        for field in LEAD_DATA_FIELDS.keys():
            value = extracted_data.get(field)
            if value and isinstance(value, str) and value.strip():
                # Normalize values
                if field == "uf":
                    # Normalize UF to uppercase, 2 letters
                    value = value.strip().upper()[:2]
                elif field == "urgency":
                    # Normalize urgency values
                    value_lower = value.lower()
                    if "alta" in value_lower or "urgente" in value_lower:
                        value = "alta"
                    elif "média" in value_lower or "media" in value_lower:
                        value = "média"
                    elif "baixa" in value_lower:
                        value = "baixa"
                    elif "sem" in value_lower or "nenhuma" in value_lower:
                        value = "sem urgência"
                    else:
                        value = value.strip()
                elif field == "knows_seleto":
                    # Normalize knows_seleto
                    value_lower = value.lower()
                    if "sim" in value_lower or "já" in value_lower or "yes" in value_lower:
                        value = "sim"
                    elif "não" in value_lower or "nao" in value_lower or "nunca" in value_lower or "no" in value_lower:
                        value = "não"
                    else:
                        value = "desconhecido"
                else:
                    value = value.strip()

                normalized_data[field] = value

        logger.info(
            "Lead data extracted from message",
            extra={
                "extracted_fields": list(normalized_data.keys()),
                "message_length": len(message),
            },
        )

        return normalized_data

    except Exception as e:
        logger.error(
            "Failed to extract lead data from message",
            extra={
                "error": str(e),
                "message_length": len(message),
            },
            exc_info=True,
        )
        return {}

