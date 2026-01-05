"""
Piperun CRM client for API integration.

This module provides a reusable HTTP client for Piperun CRM operations
with authentication, retry logic, and structured logging.

TECH-015: Implements HTTP client with:
- Token-based authentication via header
- Retry with exponential backoff (up to 3 attempts)
- Configurable timeout (default 10s)
- Secure logging (no token exposure)
"""

import asyncio
import time
from typing import Any

import httpx

from src.config.settings import settings
from src.utils.logging import get_logger, log_api_call
from src.utils.validation import normalize_cnpj, normalize_phone, normalize_uf

logger = get_logger(__name__)


class PiperunError(Exception):
    """Base exception for Piperun client errors."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        response_data: dict | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data


class PiperunAuthError(PiperunError):
    """Authentication error (401/403)."""
    pass


class PiperunNotFoundError(PiperunError):
    """Resource not found (404)."""
    pass


class PiperunValidationError(PiperunError):
    """Validation error (400/422)."""
    pass


class PiperunRateLimitError(PiperunError):
    """Rate limit exceeded (429)."""
    pass


class PiperunClient:
    """
    HTTP client for Piperun CRM API operations.

    This client provides methods to interact with Piperun CRM API with:
    - Token-based authentication
    - Retry with exponential backoff
    - Configurable timeout
    - Structured logging (without exposing tokens)

    Usage:
        client = PiperunClient()
        city_id = await client.get_city_id("São Paulo", "SP")
        company_id = await client.create_company(name="Empresa", city_id=123)
    """

    # Sentinel value to distinguish "not provided" from "explicitly None"
    _NOT_PROVIDED = object()

    def __init__(
        self,
        api_url: str | None = _NOT_PROVIDED,
        api_token: str | None = _NOT_PROVIDED,
        pipeline_id: int | None = _NOT_PROVIDED,
        stage_id: int | None = _NOT_PROVIDED,
        origin_id: int | None = _NOT_PROVIDED,
        timeout: float = 10.0,
        max_retries: int = 3,
        initial_backoff: float = 1.0,
    ):
        """
        Initialize Piperun client.

        Args:
            api_url: Piperun API base URL (default from settings)
            api_token: API token for authentication (default from settings)
            pipeline_id: Default pipeline ID for deals (default from settings)
            stage_id: Default stage ID for deals (default from settings)
            origin_id: Default origin ID for deals (default from settings)
            timeout: Request timeout in seconds (default 10s)
            max_retries: Maximum retry attempts (default 3)
            initial_backoff: Initial backoff delay in seconds (default 1s)
        """
        # Use settings defaults only if not explicitly provided
        if api_url is self._NOT_PROVIDED:
            self.api_url = settings.PIPERUN_API_URL.rstrip("/") if settings.PIPERUN_API_URL else None
        else:
            self.api_url = api_url.rstrip("/") if api_url else None

        if api_token is self._NOT_PROVIDED:
            self.api_token = settings.PIPERUN_API_TOKEN
        else:
            self.api_token = api_token

        if pipeline_id is self._NOT_PROVIDED:
            self.pipeline_id = settings.PIPERUN_PIPELINE_ID
        else:
            self.pipeline_id = pipeline_id

        if stage_id is self._NOT_PROVIDED:
            self.stage_id = settings.PIPERUN_STAGE_ID
        else:
            self.stage_id = stage_id

        if origin_id is self._NOT_PROVIDED:
            self.origin_id = settings.PIPERUN_ORIGIN_ID
        else:
            self.origin_id = origin_id

        self.timeout = httpx.Timeout(timeout, connect=5.0)
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff

        # City cache for performance optimization (TECH-016)
        self._city_cache: dict[str, int | None] = {}
        self._city_cache_enabled = True

    def is_configured(self) -> bool:
        """Check if client is properly configured with required credentials."""
        return bool(self.api_url and self.api_token)

    def _get_headers(self) -> dict[str, str]:
        """Get request headers with authentication token."""
        return {
            "Token": self.api_token,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        retry_on_rate_limit: bool = True,
    ) -> dict[str, Any] | None:
        """
        Make HTTP request to Piperun API with retry logic.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (e.g., "/cities", "/companies")
            params: Query parameters
            json_data: JSON body data
            retry_on_rate_limit: Whether to retry on 429 errors

        Returns:
            Response data as dictionary or None

        Raises:
            PiperunError: For API errors
            ValueError: If client is not configured
        """
        if not self.is_configured():
            missing = []
            if not self.api_url:
                missing.append("PIPERUN_API_URL")
            if not self.api_token:
                missing.append("PIPERUN_API_TOKEN")
            raise ValueError(
                f"Piperun client not configured. Missing: {', '.join(missing)}"
            )

        url = f"{self.api_url}{endpoint}"
        headers = self._get_headers()
        last_error: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                start_time = time.perf_counter()

                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.request(
                        method=method,
                        url=url,
                        headers=headers,
                        params=params,
                        json=json_data,
                    )

                duration_ms = (time.perf_counter() - start_time) * 1000

                # Log API call (without exposing token)
                log_api_call(
                    logger,
                    service="piperun",
                    method=method,
                    endpoint=endpoint,
                    status_code=response.status_code,
                    duration_ms=duration_ms,
                )

                # Handle rate limiting (429)
                if response.status_code == 429:
                    if retry_on_rate_limit and attempt < self.max_retries - 1:
                        retry_after = int(
                            response.headers.get(
                                "Retry-After", self.initial_backoff * (2**attempt)
                            )
                        )
                        logger.warning(
                            f"Piperun rate limited, waiting {retry_after}s before retry",
                            extra={
                                "endpoint": endpoint,
                                "attempt": attempt + 1,
                                "retry_after": retry_after,
                            },
                        )
                        await asyncio.sleep(retry_after)
                        continue
                    raise PiperunRateLimitError(
                        "Rate limit exceeded",
                        status_code=429,
                    )

                # Success responses (200, 201)
                if response.status_code in (200, 201):
                    try:
                        data = response.json()
                        logger.debug(
                            f"Piperun API success: {method} {endpoint}",
                            extra={
                                "status_code": response.status_code,
                                "attempt": attempt + 1,
                            },
                        )
                        return data
                    except Exception:
                        # Response might be empty or not JSON
                        return {}

                # No content (204)
                if response.status_code == 204:
                    return {}

                # Client errors (4xx) - don't retry
                if response.status_code == 401:
                    raise PiperunAuthError(
                        "Authentication failed - check API token",
                        status_code=401,
                    )

                if response.status_code == 403:
                    raise PiperunAuthError(
                        "Access forbidden - check permissions",
                        status_code=403,
                    )

                if response.status_code == 404:
                    raise PiperunNotFoundError(
                        f"Resource not found: {endpoint}",
                        status_code=404,
                    )

                if response.status_code in (400, 422):
                    try:
                        error_data = response.json()
                    except Exception:
                        error_data = {"error": response.text}
                    raise PiperunValidationError(
                        f"Validation error: {error_data}",
                        status_code=response.status_code,
                        response_data=error_data,
                    )

                # Other 4xx errors - don't retry
                if 400 <= response.status_code < 500:
                    try:
                        error_data = response.json()
                    except Exception:
                        error_data = {"error": response.text}
                    raise PiperunError(
                        f"Client error: {response.status_code}",
                        status_code=response.status_code,
                        response_data=error_data,
                    )

                # Server errors (5xx) - retry
                if response.status_code >= 500:
                    if attempt < self.max_retries - 1:
                        backoff = self.initial_backoff * (2**attempt)
                        logger.warning(
                            f"Piperun server error, retrying in {backoff}s",
                            extra={
                                "endpoint": endpoint,
                                "status_code": response.status_code,
                                "attempt": attempt + 1,
                                "backoff": backoff,
                            },
                        )
                        await asyncio.sleep(backoff)
                        continue
                    raise PiperunError(
                        f"Server error: {response.status_code}",
                        status_code=response.status_code,
                    )

            except httpx.TimeoutException as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    backoff = self.initial_backoff * (2**attempt)
                    logger.warning(
                        f"Piperun request timeout, retrying in {backoff}s",
                        extra={
                            "endpoint": endpoint,
                            "attempt": attempt + 1,
                            "backoff": backoff,
                        },
                    )
                    await asyncio.sleep(backoff)
                    continue

            except httpx.RequestError as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    backoff = self.initial_backoff * (2**attempt)
                    logger.warning(
                        f"Piperun request error, retrying in {backoff}s",
                        extra={
                            "endpoint": endpoint,
                            "attempt": attempt + 1,
                            "backoff": backoff,
                            "error": str(e),
                        },
                    )
                    await asyncio.sleep(backoff)
                    continue

            except (PiperunAuthError, PiperunNotFoundError, PiperunValidationError):
                # Don't retry these errors
                raise

            except PiperunError:
                # Re-raise PiperunError as-is
                raise

            except Exception as e:
                last_error = e
                logger.error(
                    "Unexpected error in Piperun API call",
                    extra={
                        "endpoint": endpoint,
                        "attempt": attempt + 1,
                        "error": str(e),
                    },
                    exc_info=True,
                )
                if attempt < self.max_retries - 1:
                    backoff = self.initial_backoff * (2**attempt)
                    await asyncio.sleep(backoff)
                    continue

        # All retries exhausted
        logger.error(
            f"Piperun API call failed after {self.max_retries} attempts",
            extra={
                "endpoint": endpoint,
                "max_retries": self.max_retries,
                "last_error": str(last_error) if last_error else None,
            },
        )
        raise PiperunError(
            f"Request failed after {self.max_retries} attempts: {endpoint}",
        )

    # ==================== TECH-016: City ID Lookup ====================

    async def get_city_id(
        self,
        city_name: str,
        uf: str,
        use_cache: bool = True,
    ) -> int | None:
        """
        Get city ID from Piperun by name and UF.

        TECH-016: Implements city lookup with optional caching.

        Args:
            city_name: City name (will be normalized)
            uf: State code (will be normalized to 2 uppercase letters)
            use_cache: Whether to use city cache (default True)

        Returns:
            City ID (int) if found, None if not found
        """
        if not city_name or not uf:
            logger.warning(
                "Invalid city_name or uf for get_city_id",
                extra={"city_name": city_name, "uf": uf},
            )
            return None

        # Normalize inputs
        city_normalized = city_name.strip().title()
        uf_normalized = normalize_uf(uf)

        if not uf_normalized or len(uf_normalized) != 2:
            logger.warning(
                "Invalid UF format for get_city_id",
                extra={"uf": uf, "normalized_uf": uf_normalized},
            )
            return None

        # Check cache
        cache_key = f"{city_normalized}:{uf_normalized}"
        if use_cache and self._city_cache_enabled and cache_key in self._city_cache:
            logger.debug(
                f"City cache hit: {cache_key}",
                extra={"city": city_normalized, "uf": uf_normalized},
            )
            return self._city_cache[cache_key]

        try:
            response = await self._make_request(
                method="GET",
                endpoint="/cities",
                params={"name": city_normalized, "uf": uf_normalized},
            )

            if response and "data" in response:
                cities = response.get("data", [])
                if cities and len(cities) > 0:
                    city_id = cities[0].get("id")

                    # Update cache
                    if use_cache and self._city_cache_enabled:
                        self._city_cache[cache_key] = city_id

                    logger.debug(
                        f"City found: {city_normalized}/{uf_normalized} -> {city_id}",
                        extra={
                            "city": city_normalized,
                            "uf": uf_normalized,
                            "city_id": city_id,
                        },
                    )
                    return city_id

            # City not found
            logger.warning(
                f"City not found: {city_normalized}/{uf_normalized}",
                extra={"city": city_normalized, "uf": uf_normalized},
            )

            # Cache negative result
            if use_cache and self._city_cache_enabled:
                self._city_cache[cache_key] = None

            return None

        except PiperunNotFoundError:
            return None
        except PiperunError as e:
            logger.error(
                f"Error looking up city: {city_normalized}/{uf_normalized}",
                extra={"error": str(e)},
            )
            return None

    # ==================== TECH-017: Company by CNPJ ====================

    async def get_company_by_cnpj(self, cnpj: str) -> dict[str, Any] | None:
        """
        Get company from Piperun by CNPJ.

        TECH-017: Implements company lookup by CNPJ for deduplication.

        Args:
            cnpj: CNPJ (will be normalized to 14 digits)

        Returns:
            Company data dict if found, None if not found
        """
        if not cnpj:
            logger.warning("Empty CNPJ for get_company_by_cnpj")
            return None

        # Normalize CNPJ
        cnpj_normalized = normalize_cnpj(cnpj)

        if not cnpj_normalized or len(cnpj_normalized) != 14:
            logger.warning(
                "Invalid CNPJ format for get_company_by_cnpj",
                extra={"cnpj": cnpj, "normalized": cnpj_normalized},
            )
            return None

        try:
            response = await self._make_request(
                method="GET",
                endpoint="/companies",
                params={"cnpj": cnpj_normalized},
            )

            if response and "data" in response:
                companies = response.get("data", [])
                if companies and len(companies) > 0:
                    company = companies[0]
                    logger.debug(
                        f"Company found by CNPJ: {cnpj_normalized}",
                        extra={
                            "cnpj": cnpj_normalized,
                            "company_id": company.get("id"),
                        },
                    )
                    return company

            logger.debug(
                f"Company not found by CNPJ: {cnpj_normalized}",
                extra={"cnpj": cnpj_normalized},
            )
            return None

        except PiperunNotFoundError:
            return None
        except PiperunError as e:
            logger.error(
                f"Error looking up company by CNPJ: {cnpj_normalized}",
                extra={"error": str(e)},
            )
            return None

    # ==================== TECH-018: Create Company ====================

    async def create_company(
        self,
        name: str,
        city_id: int | None = None,
        cnpj: str | None = None,
        website: str | None = None,
        email: str | None = None,
    ) -> int | None:
        """
        Create a company in Piperun CRM.

        TECH-018: Implements company creation.

        Args:
            name: Company name (required)
            city_id: City ID from get_city_id
            cnpj: CNPJ (will be normalized)
            website: Company website URL
            email: Company email for invoices (email_nf)

        Returns:
            Company ID (int) if created successfully, None on error
        """
        if not name:
            logger.warning("Company name is required for create_company")
            return None

        payload: dict[str, Any] = {
            "name": name.strip(),
        }

        if city_id:
            payload["city_id"] = city_id

        if cnpj:
            cnpj_normalized = normalize_cnpj(cnpj)
            if cnpj_normalized and len(cnpj_normalized) == 14:
                payload["cnpj"] = cnpj_normalized

        if website:
            payload["website"] = website.strip()

        if email:
            payload["email_nf"] = email.strip().lower()

        try:
            response = await self._make_request(
                method="POST",
                endpoint="/companies",
                json_data=payload,
            )

            if response and "data" in response:
                company_data = response.get("data", {})
                company_id = company_data.get("id")

                logger.info(
                    f"Company created successfully: {name}",
                    extra={
                        "company_id": company_id,
                        "company_name": name,
                        "cnpj": payload.get("cnpj"),
                    },
                )
                return company_id

            logger.warning(
                "No data returned from create_company",
                extra={"company_name": name},
            )
            return None

        except PiperunValidationError as e:
            logger.error(
                f"Validation error creating company: {name}",
                extra={"error": str(e), "response_data": e.response_data},
            )
            return None
        except PiperunError as e:
            logger.error(
                f"Error creating company: {name}",
                extra={"error": str(e)},
            )
            return None

    # ==================== TECH-019: Create Person ====================

    async def create_person(
        self,
        name: str,
        phones: list[str] | None = None,
        emails: list[str] | None = None,
        city_id: int | None = None,
        company_id: int | None = None,
    ) -> int | None:
        """
        Create a person (contact) in Piperun CRM.

        TECH-019: Implements person creation.

        Args:
            name: Person name (required)
            phones: List of phone numbers (will be normalized)
            emails: List of email addresses
            city_id: City ID from get_city_id
            company_id: Company ID to link person to

        Returns:
            Person ID (int) if created successfully, None on error
        """
        if not name:
            logger.warning("Person name is required for create_person")
            return None

        payload: dict[str, Any] = {
            "name": name.strip(),
        }

        # Normalize and add phones
        if phones:
            normalized_phones = []
            for phone in phones:
                normalized = normalize_phone(phone)
                if normalized and len(normalized) >= 10:
                    normalized_phones.append({"phone": normalized})
            if normalized_phones:
                payload["phones"] = normalized_phones

        # Add emails
        if emails:
            valid_emails = []
            for email in emails:
                if email and "@" in email:
                    valid_emails.append({"email": email.strip().lower()})
            if valid_emails:
                payload["emails"] = valid_emails

        if city_id:
            payload["city_id"] = city_id

        if company_id:
            payload["company_id"] = company_id

        try:
            response = await self._make_request(
                method="POST",
                endpoint="/persons",
                json_data=payload,
            )

            if response and "data" in response:
                person_data = response.get("data", {})
                person_id = person_data.get("id")

                logger.info(
                    f"Person created successfully: {name}",
                    extra={
                        "person_id": person_id,
                        "person_name": name,
                        "has_phones": bool(phones),
                        "has_emails": bool(emails),
                    },
                )
                return person_id

            logger.warning(
                "No data returned from create_person",
                extra={"person_name": name},
            )
            return None

        except PiperunValidationError as e:
            logger.error(
                f"Validation error creating person: {name}",
                extra={"error": str(e), "response_data": e.response_data},
            )
            return None
        except PiperunError as e:
            logger.error(
                f"Error creating person: {name}",
                extra={"error": str(e)},
            )
            return None

    # ==================== TECH-020: Create Deal ====================

    async def create_deal(
        self,
        title: str,
        person_id: int | None = None,
        company_id: int | None = None,
        pipeline_id: int | None = None,
        stage_id: int | None = None,
        origin_id: int | None = None,
    ) -> int | None:
        """
        Create a deal (opportunity) in Piperun CRM.

        TECH-020: Implements deal creation.

        Args:
            title: Deal title (format: "Lead - [Produto] - [Cidade/UF]")
            person_id: Person ID to link deal to
            company_id: Company ID to link deal to
            pipeline_id: Pipeline ID (default from settings)
            stage_id: Stage ID (default from settings)
            origin_id: Origin ID (default from settings)

        Returns:
            Deal ID (int) if created successfully, None on error
        """
        if not title:
            logger.warning("Deal title is required for create_deal")
            return None

        # Use provided IDs or defaults from settings
        _pipeline_id = pipeline_id or self.pipeline_id
        _stage_id = stage_id or self.stage_id
        _origin_id = origin_id or self.origin_id

        if not _pipeline_id or not _stage_id:
            logger.error(
                "Pipeline ID and Stage ID are required for create_deal",
                extra={
                    "pipeline_id": _pipeline_id,
                    "stage_id": _stage_id,
                },
            )
            return None

        payload: dict[str, Any] = {
            "title": title.strip(),
            "pipeline_id": _pipeline_id,
            "stage_id": _stage_id,
        }

        if _origin_id:
            payload["origin_id"] = _origin_id

        if person_id:
            payload["person_id"] = person_id

        if company_id:
            payload["company_id"] = company_id

        try:
            response = await self._make_request(
                method="POST",
                endpoint="/deals",
                json_data=payload,
            )

            if response and "data" in response:
                deal_data = response.get("data", {})
                deal_id = deal_data.get("id")

                logger.info(
                    f"Deal created successfully: {title}",
                    extra={
                        "deal_id": deal_id,
                        "title": title,
                        "pipeline_id": _pipeline_id,
                        "stage_id": _stage_id,
                    },
                )
                return deal_id

            logger.warning(
                "No data returned from create_deal",
                extra={"title": title},
            )
            return None

        except PiperunValidationError as e:
            logger.error(
                f"Validation error creating deal: {title}",
                extra={"error": str(e), "response_data": e.response_data},
            )
            return None
        except PiperunError as e:
            logger.error(
                f"Error creating deal: {title}",
                extra={"error": str(e)},
            )
            return None

    # ==================== TECH-021: Create Note ====================

    async def create_note(
        self,
        deal_id: int,
        content: str,
    ) -> int | None:
        """
        Create a note attached to a deal in Piperun CRM.

        TECH-021: Implements note creation.

        Args:
            deal_id: Deal ID to attach note to (required)
            content: Note content (required)

        Returns:
            Note ID (int) if created successfully, None on error
        """
        if not deal_id:
            logger.warning("Deal ID is required for create_note")
            return None

        if not content:
            logger.warning("Note content is required for create_note")
            return None

        payload: dict[str, Any] = {
            "deal_id": deal_id,
            "text": content.strip(),
        }

        try:
            response = await self._make_request(
                method="POST",
                endpoint="/notes",
                json_data=payload,
            )

            if response and "data" in response:
                note_data = response.get("data", {})
                note_id = note_data.get("id")

                logger.info(
                    f"Note created successfully for deal {deal_id}",
                    extra={
                        "note_id": note_id,
                        "deal_id": deal_id,
                    },
                )
                return note_id

            logger.warning(
                "No data returned from create_note",
                extra={"deal_id": deal_id},
            )
            return None

        except PiperunValidationError as e:
            logger.error(
                f"Validation error creating note for deal {deal_id}",
                extra={"error": str(e), "response_data": e.response_data},
            )
            return None
        except PiperunError as e:
            logger.error(
                f"Error creating note for deal {deal_id}",
                extra={"error": str(e)},
            )
            return None

    # ==================== Helper Methods ====================

    def clear_city_cache(self) -> None:
        """Clear the city ID cache."""
        self._city_cache.clear()
        logger.debug("City cache cleared")

    def disable_city_cache(self) -> None:
        """Disable city ID caching."""
        self._city_cache_enabled = False
        logger.debug("City cache disabled")

    def enable_city_cache(self) -> None:
        """Enable city ID caching."""
        self._city_cache_enabled = True
        logger.debug("City cache enabled")


# Global client instance
piperun_client = PiperunClient()


# ==================== Note Template Helper (TECH-021) ====================

def generate_note_template(
    resumo: str = "Não informado",
    empresa: str = "Não informado",
    contato: str = "Não informado",
    cidade: str = "Não informado",
    ddd: str = "XX",
    segmento: str = "Não informado",
    necessidade: str = "Não informado",
    equipamento: str = "Não informado",
    classificacao: str = "Não informado",
    proximo_passo: str = "Não informado",
) -> str:
    """
    Generate note content from PRD template (Appendix 20.3).

    All fields default to "Não informado" if not provided.

    Args:
        resumo: Brief summary of conversation and request
        empresa: Company name
        contato: Contact name
        cidade: City name
        ddd: Area code
        segmento: Market segment (e.g., Frigorífico, Laticínios)
        necessidade: Identified need/objective
        equipamento: Equipment of interest
        classificacao: Lead classification (Quente/Morno/Frio)
        proximo_passo: Next step

    Returns:
        Formatted note content string
    """
    template = f"""**Resumo do Atendimento:**
{resumo}

**Dados do Cliente:**
- Empresa: {empresa}
- Contato: {contato}
- Cidade / DDD: {cidade} / ({ddd})
- Segmento: {segmento}

**Necessidade Identificada:**
{necessidade}

**Equipamento de Interesse:**
{equipamento}

**Classificação do Lead:**
{classificacao}

**Próximo Passo:**
{proximo_passo}"""

    return template
