"""
Empresa persistence service for saving and retrieving empresa data.

This service provides CRUD operations for empresa table (TECH-014):
- create_empresa: Create new empresa with CNPJ deduplication
- get_empresa_by_cnpj: Retrieve empresa by normalized CNPJ
- update_empresa: Update empresa fields (partial updates)
"""

from datetime import datetime
from typing import Dict, Optional, Any

from src.services.conversation_persistence import get_supabase_client
from src.utils.logging import get_logger
from src.utils.validation import normalize_cnpj

logger = get_logger(__name__)


def create_empresa(data: Dict[str, Optional[Any]]) -> Optional[Dict[str, Any]]:
    """
    Create a new empresa in Supabase with CNPJ deduplication.

    This function:
    1. Normalizes CNPJ using normalize_cnpj before operation
    2. Validates that CNPJ has 14 digits after normalization
    3. Checks if empresa already exists by CNPJ (if CNPJ provided) - deduplication
    4. Creates empresa with fields: nome, cidade, uf, cnpj, site, email, telefone, contato
    5. Returns the created empresa with id

    Args:
        data: Dictionary with empresa data fields
              - nome: Company name
              - cidade: City
              - uf: State code (2 letters)
              - cnpj: CNPJ (will be normalized to 14 digits)
              - site: Website URL
              - email: Email address
              - telefone: Phone number
              - contato: Lead ID (UUID) - foreign key to leads table

    Returns:
        Dictionary with empresa data (including id, created_at, updated_at) or None on error

    Examples:
        >>> # Create empresa with CNPJ
        >>> empresa = create_empresa({
        ...     "nome": "Empresa Teste LTDA",
        ...     "cidade": "São Paulo",
        ...     "uf": "SP",
        ...     "cnpj": "12.345.678/0001-90",
        ...     "email": "contato@example.com"
        ... })
        >>> # CNPJ will be normalized to "12345678000190"
    """
    try:
        client = get_supabase_client()
    except Exception as e:
        logger.error(
            "Failed to get Supabase client",
            extra={"error": str(e), "operation": "create_empresa"},
        )
        return None

    if not client:
        logger.debug(
            "Supabase not available - empresa not persisted",
            extra={"operation": "create_empresa"},
        )
        return None

    try:
        # Normalize CNPJ if provided
        cnpj = data.get("cnpj")
        normalized_cnpj = None

        # If CNPJ key is provided, validate it (even if empty/invalid)
        if "cnpj" in data and data["cnpj"] is not None:
            if not cnpj or not cnpj.strip():
                logger.warning(
                    "Invalid CNPJ format - empty CNPJ provided",
                    extra={
                        "cnpj": cnpj,
                        "operation": "create_empresa",
                    },
                )
                return None

            normalized_cnpj = normalize_cnpj(cnpj)

            # Validate CNPJ has 14 digits
            if len(normalized_cnpj) != 14:
                logger.warning(
                    "Invalid CNPJ format - must have 14 digits after normalization",
                    extra={
                        "cnpj": cnpj,
                        "normalized_cnpj": normalized_cnpj,
                        "operation": "create_empresa",
                    },
                )
                return None

        if normalized_cnpj:
            # Check if empresa already exists by CNPJ (deduplication)
            existing = (
                client.table("empresa")
                .select("id")
                .eq("cnpj", normalized_cnpj)
                .execute()
            )

            if existing.data and len(existing.data) > 0:
                logger.warning(
                    "Empresa with CNPJ already exists",
                    extra={
                        "cnpj": normalized_cnpj,
                        "existing_empresa_id": existing.data[0].get("id"),
                        "operation": "create_empresa",
                    },
                )
                return None

        # Filter out None/null values
        filtered_data = {k: v for k, v in data.items() if v is not None}

        # Replace CNPJ with normalized version if it was provided
        if normalized_cnpj:
            filtered_data["cnpj"] = normalized_cnpj

        # Prepare insert payload
        insert_payload = filtered_data

        # Insert empresa
        response = (
            client.table("empresa")
            .insert(insert_payload)
            .execute()
        )

        if response.data and len(response.data) > 0:
            empresa = response.data[0]
            logger.info(
                "Empresa created successfully",
                extra={
                    "empresa_id": empresa.get("id"),
                    "cnpj": normalized_cnpj,
                    "fields": list(filtered_data.keys()),
                    "operation": "create_empresa",
                },
            )
            return empresa
        else:
            logger.warning(
                "No data returned from Supabase insert",
                extra={"operation": "create_empresa"},
            )
            return None

    except Exception as e:
        logger.error(
            "Failed to create empresa",
            extra={
                "error": str(e),
                "operation": "create_empresa",
            },
            exc_info=True,
        )
        return None


def get_empresa_by_cnpj(cnpj: str) -> Optional[Dict[str, Any]]:
    """
    Get an empresa by CNPJ from Supabase.

    This function:
    1. Normalizes CNPJ to 14 digits before search
    2. Queries Supabase for empresa with matching CNPJ
    3. Returns empresa as dict or None if not found

    Args:
        cnpj: CNPJ (will be normalized to 14 digits)

    Returns:
        Dictionary with empresa data (including id, created_at, updated_at) or None if not found

    Examples:
        >>> # Get empresa by CNPJ
        >>> empresa = get_empresa_by_cnpj("12.345.678/0001-90")
        >>> if empresa:
        ...     print(empresa["nome"])
        >>> # Returns None if empresa doesn't exist
        >>> empresa = get_empresa_by_cnpj("12345678000190")
        >>> assert empresa is None
    """
    if not cnpj:
        logger.warning(
            "Invalid CNPJ for get_empresa_by_cnpj",
            extra={"cnpj": cnpj, "operation": "get_empresa_by_cnpj"},
        )
        return None

    normalized_cnpj = normalize_cnpj(cnpj)
    if not normalized_cnpj or len(normalized_cnpj) != 14:
        logger.warning(
            "Invalid CNPJ format - must have 14 digits after normalization",
            extra={
                "cnpj": cnpj,
                "normalized_cnpj": normalized_cnpj,
                "operation": "get_empresa_by_cnpj",
            },
        )
        return None

    try:
        client = get_supabase_client()
    except Exception as e:
        logger.error(
            "Failed to get Supabase client",
            extra={"error": str(e), "operation": "get_empresa_by_cnpj"},
        )
        return None

    if not client:
        logger.debug(
            "Supabase not available - returning None",
            extra={"cnpj": normalized_cnpj, "operation": "get_empresa_by_cnpj"},
        )
        return None

    try:
        response = (
            client.table("empresa")
            .select("*")
            .eq("cnpj", normalized_cnpj)
            .execute()
        )

        if response.data and len(response.data) > 0:
            empresa = response.data[0]
            logger.debug(
                "Empresa retrieved successfully",
                extra={
                    "cnpj": normalized_cnpj,
                    "empresa_id": empresa.get("id"),
                    "operation": "get_empresa_by_cnpj",
                },
            )
            return empresa
        else:
            logger.debug(
                "Empresa not found",
                extra={"cnpj": normalized_cnpj, "operation": "get_empresa_by_cnpj"},
            )
            return None

    except Exception as e:
        logger.error(
            "Failed to get empresa by CNPJ",
            extra={
                "cnpj": normalized_cnpj,
                "error": str(e),
                "operation": "get_empresa_by_cnpj",
            },
            exc_info=True,
        )
        return None


def update_empresa(empresa_id: str, data: Dict[str, Optional[Any]]) -> Optional[Dict[str, Any]]:
    """
    Update an empresa in Supabase.

    This function:
    1. Filters out None/null fields for partial updates
    2. If CNPJ is provided, normalizes it before updating
    3. Updates empresa with specified fields
    4. Updates updated_at field automatically
    5. Returns the updated empresa

    Args:
        empresa_id: UUID of the empresa to update
        data: Dictionary with fields to update
              Fields with None/null values are filtered out for partial updates
              If CNPJ is provided, it will be normalized to 14 digits

    Returns:
        Dictionary with updated empresa data or None on error

    Examples:
        >>> # Update empresa fields
        >>> empresa = update_empresa(empresa_id, {
        ...     "nome": "Empresa Atualizada",
        ...     "email": "novo@example.com"
        ... })
        >>> # Update CNPJ (will be normalized)
        >>> empresa = update_empresa(empresa_id, {
        ...     "cnpj": "12.345.678/0001-90"  # Will be normalized
        ... })
    """
    if not empresa_id:
        logger.warning(
            "Invalid empresa_id for update_empresa",
            extra={"empresa_id": empresa_id, "operation": "update_empresa"},
        )
        return None

    try:
        client = get_supabase_client()
    except Exception as e:
        logger.error(
            "Failed to get Supabase client",
            extra={"error": str(e), "operation": "update_empresa"},
        )
        return None

    if not client:
        logger.debug(
            "Supabase not available - empresa not updated",
            extra={"empresa_id": empresa_id, "operation": "update_empresa"},
        )
        return None

    try:
        # Filter out None/null values for partial updates
        filtered_data = {k: v for k, v in data.items() if v is not None}

        if not filtered_data:
            logger.warning(
                "No valid fields to update",
                extra={"empresa_id": empresa_id, "operation": "update_empresa"},
            )
            return None

        # Normalize CNPJ if provided
        if "cnpj" in filtered_data:
            normalized_cnpj = normalize_cnpj(str(filtered_data["cnpj"]))
            
            # Validate CNPJ has 14 digits
            if len(normalized_cnpj) != 14:
                logger.warning(
                    "Invalid CNPJ format - must have 14 digits after normalization",
                    extra={
                        "cnpj": filtered_data["cnpj"],
                        "normalized_cnpj": normalized_cnpj,
                        "operation": "update_empresa",
                    },
                )
                return None
            
            filtered_data["cnpj"] = normalized_cnpj

        # Add updated_at timestamp
        filtered_data["updated_at"] = datetime.utcnow().isoformat()

        # Update empresa
        response = (
            client.table("empresa")
            .update(filtered_data)
            .eq("id", empresa_id)
            .execute()
        )

        if response.data and len(response.data) > 0:
            empresa = response.data[0]
            logger.info(
                "Empresa updated successfully",
                extra={
                    "empresa_id": empresa_id,
                    "fields_updated": list(filtered_data.keys()),
                    "operation": "update_empresa",
                },
            )
            return empresa
        else:
            logger.warning(
                "Empresa not found or no data returned",
                extra={"empresa_id": empresa_id, "operation": "update_empresa"},
            )
            return None

    except Exception as e:
        logger.error(
            "Failed to update empresa",
            extra={
                "empresa_id": empresa_id,
                "error": str(e),
                "operation": "update_empresa",
            },
            exc_info=True,
        )
        return None

