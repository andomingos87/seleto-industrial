"""
Piperun CRM synchronization service.

US-007: Integrates lead qualification flow with Piperun CRM.
Handles automatic creation of companies, persons, deals, and notes
when leads are qualified.

This module provides:
- sync_lead_to_piperun: Main function to sync qualified leads to CRM
- get_or_create_company: Deduplicated company creation by CNPJ
- build_deal_title: Generate deal title from lead data
- Idempotency: Checks for existing opportunity before creating new one
"""

from typing import Any

from src.services.lead_persistence import get_lead_by_phone
from src.services.orcamento_persistence import (
    get_orcamentos_by_lead,
    update_orcamento,
)
from src.services.piperun_client import (
    PiperunClient,
    PiperunError,
    generate_note_template,
    piperun_client,
)
from src.utils.logging import get_logger
from src.utils.validation import normalize_phone, normalize_uf

logger = get_logger(__name__)


class PiperunSyncError(Exception):
    """Error during Piperun synchronization."""

    def __init__(
        self,
        message: str,
        lead_id: str | None = None,
        step: str | None = None,
    ):
        super().__init__(message)
        self.lead_id = lead_id
        self.step = step


def build_deal_title(
    product: str | None = None,
    city: str | None = None,
    uf: str | None = None,
) -> str:
    """
    Build deal title from lead data.

    Format: "Lead - [Produto] - [Cidade/UF]"

    Args:
        product: Product of interest
        city: City name
        uf: State code (2 letters)

    Returns:
        Formatted deal title
    """
    parts = ["Lead"]

    if product:
        parts.append(product.strip())
    else:
        parts.append("Interesse")

    location = ""
    if city:
        location = city.strip()
    if uf:
        uf_normalized = normalize_uf(uf)
        if location:
            location = f"{location}/{uf_normalized}"
        else:
            location = uf_normalized or ""

    if location:
        parts.append(location)
    else:
        parts.append("Brasil")

    return " - ".join(parts)


def extract_ddd_from_phone(phone: str) -> str:
    """
    Extract DDD (area code) from phone number.

    Args:
        phone: Normalized phone number (E.164 format without +)

    Returns:
        DDD (2 digits) or "XX" if not extractable
    """
    if not phone:
        return "XX"

    # Remove country code (55 for Brazil)
    phone_digits = normalize_phone(phone)
    if not phone_digits:
        return "XX"

    # Brazilian format: 55 + DDD (2) + number (8-9)
    if len(phone_digits) >= 12 and phone_digits.startswith("55"):
        return phone_digits[2:4]
    elif len(phone_digits) >= 10:
        # Assume local format with DDD
        return phone_digits[:2]

    return "XX"


async def sync_lead_to_piperun(
    phone: str,
    lead_data: dict[str, Any] | None = None,
    orcamento_id: str | None = None,
    conversation_summary: str | None = None,
    force_create: bool = False,
    client: PiperunClient | None = None,
) -> int | None:
    """
    Synchronize a qualified lead to Piperun CRM.

    US-007: Main integration function that:
    1. Checks for existing opportunity (idempotency)
    2. Gets or creates company (by CNPJ if available)
    3. Creates person (contact)
    4. Creates deal (opportunity)
    5. Attaches note with lead data
    6. Updates local database with Piperun IDs

    Args:
        phone: Lead phone number (required)
        lead_data: Lead data dictionary (optional, will fetch from DB if not provided)
        orcamento_id: Specific orcamento ID to update (optional)
        conversation_summary: Summary of conversation for note (optional)
        force_create: If True, create even if opportunity already exists
        client: PiperunClient instance (optional, uses global client if not provided)

    Returns:
        Deal ID (int) if created/existing, None on error

    Raises:
        PiperunSyncError: If sync fails at any step
    """
    _client = client or piperun_client

    if not _client.is_configured():
        logger.warning(
            "Piperun client not configured, skipping sync",
            extra={"phone": phone},
        )
        return None

    # Normalize phone
    normalized_phone = normalize_phone(phone)
    if not normalized_phone:
        logger.error(
            "Invalid phone for Piperun sync",
            extra={"phone": phone},
        )
        raise PiperunSyncError(f"Invalid phone: {phone}", step="validation")

    logger.info(
        "Starting Piperun sync for lead",
        extra={"phone": normalized_phone, "has_lead_data": bool(lead_data)},
    )

    try:
        # Step 1: Get lead data from database if not provided
        if not lead_data:
            # get_lead_by_phone is synchronous
            lead_data = get_lead_by_phone(normalized_phone)
            if not lead_data:
                logger.warning(
                    "Lead not found in database for Piperun sync",
                    extra={"phone": normalized_phone},
                )
                lead_data = {}

        # Step 2: Check for existing opportunity (idempotency)
        orcamento = None
        # Get most recent orcamento for this lead
        lead_id = lead_data.get("id")
        if lead_id:
            # get_orcamentos_by_lead is synchronous
            orcamentos = get_orcamentos_by_lead(lead_id)
            if orcamentos:
                orcamento = orcamentos[0]  # Most recent

        if orcamento and orcamento.get("oportunidade_pipe_id") and not force_create:
            existing_deal_id = int(orcamento["oportunidade_pipe_id"])
            logger.info(
                "Opportunity already exists in Piperun, skipping creation",
                extra={
                    "phone": normalized_phone,
                    "deal_id": existing_deal_id,
                    "orcamento_id": orcamento.get("id"),
                },
            )
            return existing_deal_id

        # Step 3: Get or create city ID
        city_id = None
        city = lead_data.get("city") or lead_data.get("cidade")
        uf = lead_data.get("uf")

        if city and uf:
            city_id = await _client.get_city_id(city, uf)
            if city_id:
                logger.debug(
                    "City ID obtained",
                    extra={"city": city, "uf": uf, "city_id": city_id},
                )
            else:
                logger.warning(
                    "City not found in Piperun",
                    extra={"city": city, "uf": uf},
                )

        # Step 4: Get or create company (by CNPJ if available)
        company_id = None
        cnpj = lead_data.get("cnpj")
        company_name = lead_data.get("empresa") or lead_data.get("company_name")

        if cnpj:
            # Check if company exists by CNPJ
            existing_company = await _client.get_company_by_cnpj(cnpj)
            if existing_company:
                company_id = existing_company.get("id")
                logger.info(
                    "Found existing company by CNPJ",
                    extra={"cnpj": cnpj, "company_id": company_id},
                )
            elif company_name:
                # Create new company
                company_id = await _client.create_company(
                    name=company_name,
                    city_id=city_id,
                    cnpj=cnpj,
                    email=lead_data.get("email"),
                    website=lead_data.get("site"),
                )
                if company_id:
                    logger.info(
                        "Created company in Piperun",
                        extra={
                            "company_name": company_name,
                            "company_id": company_id,
                        },
                    )
        elif company_name:
            # Create company without CNPJ
            company_id = await _client.create_company(
                name=company_name,
                city_id=city_id,
                email=lead_data.get("email"),
                website=lead_data.get("site"),
            )
            if company_id:
                logger.info(
                    "Created company in Piperun (without CNPJ)",
                    extra={"company_name": company_name, "company_id": company_id},
                )

        # Step 5: Create person (contact)
        person_id = None
        contact_name = lead_data.get("name") or lead_data.get("nome")
        if not contact_name:
            contact_name = lead_data.get("senderName") or "Lead WhatsApp"

        phones = [normalized_phone]
        emails = []
        if lead_data.get("email"):
            emails.append(lead_data["email"])

        person_id = await _client.create_person(
            name=contact_name,
            phones=phones,
            emails=emails if emails else None,
            city_id=city_id,
            company_id=company_id,
        )

        if person_id:
            logger.info(
                "Created person in Piperun",
                extra={"contact_name": contact_name, "person_id": person_id},
            )
        else:
            logger.warning(
                "Failed to create person in Piperun",
                extra={"contact_name": contact_name},
            )

        # Step 6: Create deal (opportunity)
        product = (
            lead_data.get("produto_interesse")
            or lead_data.get("produto")
            or lead_data.get("product")
        )
        deal_title = build_deal_title(
            product=product,
            city=city,
            uf=uf,
        )

        deal_id = await _client.create_deal(
            title=deal_title,
            person_id=person_id,
            company_id=company_id,
        )

        if not deal_id:
            logger.error(
                "Failed to create deal in Piperun",
                extra={"phone": normalized_phone, "title": deal_title},
            )
            raise PiperunSyncError(
                "Failed to create deal in Piperun",
                lead_id=lead_data.get("id"),
                step="create_deal",
            )

        logger.info(
            "Created deal in Piperun",
            extra={
                "phone": normalized_phone,
                "deal_id": deal_id,
                "title": deal_title,
            },
        )

        # Step 7: Create note with lead data (PRD template)
        temperature = (
            lead_data.get("temperature")
            or lead_data.get("temperatura")
            or "Não informado"
        )

        # Map temperature to Portuguese
        temp_map = {
            "hot": "Quente",
            "warm": "Morno",
            "cold": "Frio",
            "quente": "Quente",
            "morno": "Morno",
            "frio": "Frio",
        }
        temperature_display = temp_map.get(temperature.lower(), temperature)

        # Build note content
        note_content = generate_note_template(
            resumo=conversation_summary or "Atendimento via WhatsApp automatizado",
            empresa=company_name or "Não informado",
            contato=contact_name,
            cidade=city or "Não informado",
            ddd=extract_ddd_from_phone(normalized_phone),
            segmento=lead_data.get("segmento") or "Não informado",
            necessidade=lead_data.get("necessidade") or lead_data.get("produto_interesse") or "Não informado",
            equipamento=product or "Não informado",
            classificacao=temperature_display,
            proximo_passo=_get_next_step(temperature_display),
        )

        note_id = await _client.create_note(
            deal_id=deal_id,
            content=note_content,
        )

        if note_id:
            logger.info(
                "Created note in Piperun",
                extra={"deal_id": deal_id, "note_id": note_id},
            )
        else:
            logger.warning(
                "Failed to create note in Piperun",
                extra={"deal_id": deal_id},
            )

        # Step 8: Update local database with Piperun deal ID
        if orcamento:
            # update_orcamento is synchronous
            update_orcamento(
                orcamento_id=orcamento["id"],
                data={"oportunidade_pipe_id": str(deal_id)},
            )
            logger.info(
                "Updated orcamento with Piperun deal ID",
                extra={
                    "orcamento_id": orcamento["id"],
                    "deal_id": deal_id,
                },
            )

        logger.info(
            "Piperun sync completed successfully",
            extra={
                "phone": normalized_phone,
                "deal_id": deal_id,
                "company_id": company_id,
                "person_id": person_id,
            },
        )

        return deal_id

    except PiperunSyncError:
        # Re-raise PiperunSyncError as-is to preserve step info
        raise
    except PiperunError as e:
        logger.error(
            "Piperun API error during sync",
            extra={
                "phone": normalized_phone,
                "error": str(e),
                "status_code": e.status_code,
            },
        )
        raise PiperunSyncError(
            f"Piperun API error: {str(e)}",
            lead_id=lead_data.get("id") if lead_data else None,
            step="api_call",
        ) from e
    except Exception as e:
        logger.error(
            "Unexpected error during Piperun sync",
            extra={
                "phone": normalized_phone,
                "error": str(e),
            },
            exc_info=True,
        )
        raise PiperunSyncError(
            f"Unexpected error: {str(e)}",
            lead_id=lead_data.get("id") if lead_data else None,
            step="unknown",
        ) from e


def _get_next_step(temperature: str) -> str:
    """
    Determine next step based on lead temperature.

    Args:
        temperature: Lead classification (Quente/Morno/Frio)

    Returns:
        Next step recommendation
    """
    temp_lower = temperature.lower() if temperature else ""

    if temp_lower in ("quente", "hot"):
        return "Encaminhado para consultor para envio de orçamento."
    elif temp_lower in ("morno", "warm"):
        return "Agendado follow-up para esclarecimento de dúvidas."
    elif temp_lower in ("frio", "cold"):
        return "Registrado para nutrição. Enviar catálogo/materiais."
    else:
        return "Aguardando definição de próximos passos."


def should_sync_to_piperun(
    lead_data: dict[str, Any],
    temperature: str | None = None,
) -> bool:
    """
    Determine if lead should be synced to Piperun CRM.

    Criteria:
    - Lead is classified as "hot" (quente)
    - OR lead has minimum required fields (name + product interest)

    Args:
        lead_data: Lead data dictionary
        temperature: Lead temperature classification

    Returns:
        True if should sync, False otherwise
    """
    if not piperun_client.is_configured():
        return False

    # Always sync hot leads
    temp = temperature or lead_data.get("temperature") or lead_data.get("temperatura")
    if temp and temp.lower() in ("hot", "quente"):
        return True

    # Check minimum fields for other temperatures
    has_name = bool(lead_data.get("name") or lead_data.get("nome"))
    has_product = bool(
        lead_data.get("produto_interesse")
        or lead_data.get("produto")
        or lead_data.get("product")
    )

    # Sync if warm with good data
    if temp and temp.lower() in ("warm", "morno"):
        return has_name and has_product

    return False
