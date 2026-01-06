"""
Audit Trail service for logging sensitive operations.

TECH-028: Implementar Audit Trail para Operacoes Sensiveis

This service provides:
- Logging of CRUD operations on leads, orcamentos, empresas
- Logging of API calls to external services (CRM, WhatsApp)
- Sensitive data masking (phone, email, CNPJ)
- Query interface for audit investigation
- Configurable retention

The audit trail is designed to NOT fail the main operation if logging fails.
"""

import re
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from src.config.settings import settings
from src.services.conversation_persistence import get_supabase_client
from src.utils.logging import get_logger

logger = get_logger(__name__)


# =============================================================================
# Constants and Enums
# =============================================================================


class AuditAction(str, Enum):
    """Types of auditable actions."""

    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    API_CALL = "API_CALL"


class EntityType(str, Enum):
    """Types of auditable entities."""

    LEAD = "lead"
    ORCAMENTO = "orcamento"
    EMPRESA = "empresa"
    API_CALL = "api_call"
    CONVERSATION = "conversation"


# Default retention period in days
DEFAULT_RETENTION_DAYS = 90

# Fields that should be masked in audit logs
SENSITIVE_FIELDS = frozenset([
    "phone",
    "telefone",
    "email",
    "e-mail",
    "cnpj",
    "cpf",
    "token",
    "api_key",
    "password",
    "senha",
    "secret",
])


# =============================================================================
# Sensitive Data Masking
# =============================================================================


def mask_phone(phone: str) -> str:
    """
    Mask phone number for audit logging.

    Args:
        phone: Phone number (any format)

    Returns:
        Masked phone (e.g., "5511***9999")

    Examples:
        >>> mask_phone("5511999999999")
        '5511***9999'
        >>> mask_phone("11999999999")
        '11***9999'
    """
    if not phone:
        return ""

    # Remove non-digits
    digits = re.sub(r"\D", "", phone)

    if len(digits) <= 6:
        return "***"

    # Show first 4 and last 4 digits
    return f"{digits[:4]}***{digits[-4:]}"


def mask_email(email: str) -> str:
    """
    Mask email for audit logging.

    Args:
        email: Email address

    Returns:
        Masked email (e.g., "u***@domain.com")

    Examples:
        >>> mask_email("user@example.com")
        'u***@example.com'
        >>> mask_email("ab@test.com")
        'a***@test.com'
    """
    if not email or "@" not in email:
        return "***"

    local, domain = email.rsplit("@", 1)

    if len(local) <= 1:
        return f"***@{domain}"

    return f"{local[0]}***@{domain}"


def mask_cnpj(cnpj: str) -> str:
    """
    Mask CNPJ for audit logging.

    Args:
        cnpj: CNPJ (any format)

    Returns:
        Masked CNPJ (e.g., "12.***.***/0001-90")

    Examples:
        >>> mask_cnpj("12345678000190")
        '12.***.***/0001-90'
    """
    if not cnpj:
        return ""

    # Remove non-digits
    digits = re.sub(r"\D", "", cnpj)

    if len(digits) != 14:
        return "***"

    # Format: XX.XXX.XXX/XXXX-XX -> XX.***.***/XXXX-XX
    return f"{digits[:2]}.***.***/{ digits[8:12]}-{digits[12:]}"


def mask_sensitive_data(data: dict[str, Any]) -> dict[str, Any]:
    """
    Mask sensitive fields in a dictionary for audit logging.

    This function recursively processes dictionaries and masks:
    - phone/telefone fields
    - email fields
    - cnpj/cpf fields
    - token/api_key/password/secret fields (completely hidden)

    Args:
        data: Dictionary that may contain sensitive data

    Returns:
        New dictionary with sensitive data masked

    Examples:
        >>> mask_sensitive_data({"phone": "5511999999999", "name": "Test"})
        {'phone': '5511***9999', 'name': 'Test'}
    """
    if not data:
        return {}

    masked = {}

    for key, value in data.items():
        key_lower = key.lower()

        # Recursively handle nested dicts
        if isinstance(value, dict):
            masked[key] = mask_sensitive_data(value)
            continue

        # Skip None values
        if value is None:
            masked[key] = None
            continue

        # Convert to string for masking
        str_value = str(value)

        # Completely hide tokens and secrets
        if any(s in key_lower for s in ["token", "api_key", "password", "senha", "secret"]):
            masked[key] = "[REDACTED]"
        # Mask phone numbers
        elif key_lower in ("phone", "telefone", "celular", "whatsapp"):
            masked[key] = mask_phone(str_value)
        # Mask emails
        elif key_lower in ("email", "e-mail", "e_mail"):
            masked[key] = mask_email(str_value)
        # Mask CNPJ
        elif key_lower in ("cnpj",):
            masked[key] = mask_cnpj(str_value)
        # Mask CPF (similar to CNPJ but 11 digits)
        elif key_lower in ("cpf",):
            digits = re.sub(r"\D", "", str_value)
            masked[key] = f"{digits[:3]}.***.***-{digits[-2:]}" if len(digits) == 11 else "***"
        # Keep other fields as-is
        else:
            masked[key] = value

    return masked


def compute_changes(
    old_data: dict[str, Any] | None,
    new_data: dict[str, Any],
) -> dict[str, Any]:
    """
    Compute the difference between old and new data for UPDATE operations.

    Args:
        old_data: Previous state (None for CREATE)
        new_data: New state

    Returns:
        Dictionary with 'before' and 'after' keys showing changed fields only
    """
    if old_data is None:
        # CREATE operation - just show new data (masked)
        return {"after": mask_sensitive_data(new_data)}

    before = {}
    after = {}

    # Find changed fields
    all_keys = set(old_data.keys()) | set(new_data.keys())

    for key in all_keys:
        old_val = old_data.get(key)
        new_val = new_data.get(key)

        if old_val != new_val:
            before[key] = old_val
            after[key] = new_val

    return {
        "before": mask_sensitive_data(before),
        "after": mask_sensitive_data(after),
    }


# =============================================================================
# Audit Logging Functions
# =============================================================================


async def log_audit(
    action: AuditAction,
    entity_type: EntityType,
    entity_id: str | None = None,
    changes: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
    user_id: str = "system",
    ip_address: str | None = None,
) -> bool:
    """
    Log an audit event to the database.

    This function is designed to NOT fail the main operation.
    If audit logging fails, it logs an error but returns False.

    Args:
        action: Type of action (CREATE, UPDATE, DELETE, API_CALL)
        entity_type: Type of entity being audited
        entity_id: ID of the entity (UUID or external ID)
        changes: Dictionary with before/after values (will be masked)
        metadata: Additional context (will be masked)
        user_id: User or system that performed the action
        ip_address: Client IP address if available

    Returns:
        True if audit log was saved, False otherwise
    """
    try:
        client = get_supabase_client()

        if client is None:
            logger.debug(
                "Audit log skipped - Supabase not configured",
                extra={
                    "action": action.value if isinstance(action, AuditAction) else action,
                    "entity_type": entity_type.value if isinstance(entity_type, EntityType) else entity_type,
                    "entity_id": entity_id,
                },
            )
            return False

        # Prepare audit record
        audit_record = {
            "action": action.value if isinstance(action, AuditAction) else action,
            "entity_type": entity_type.value if isinstance(entity_type, EntityType) else entity_type,
            "entity_id": entity_id,
            "user_id": user_id,
            "changes": mask_sensitive_data(changes) if changes else None,
            "metadata": mask_sensitive_data(metadata) if metadata else None,
            "ip_address": ip_address,
        }

        # Insert audit log
        result = client.table("audit_logs").insert(audit_record).execute()

        if result.data:
            logger.debug(
                "Audit log created",
                extra={
                    "audit_id": result.data[0].get("id") if result.data else None,
                    "action": audit_record["action"],
                    "entity_type": audit_record["entity_type"],
                    "entity_id": entity_id,
                },
            )
            return True
        else:
            logger.warning(
                "Audit log insert returned no data",
                extra={"audit_record": audit_record},
            )
            return False

    except Exception as e:
        # Log error but don't fail the main operation
        logger.error(
            "Failed to create audit log",
            extra={
                "action": action.value if isinstance(action, AuditAction) else action,
                "entity_type": entity_type.value if isinstance(entity_type, EntityType) else entity_type,
                "entity_id": entity_id,
                "error": str(e),
            },
            exc_info=True,
        )
        return False


async def log_entity_create(
    entity_type: EntityType,
    entity_id: str,
    data: dict[str, Any],
    user_id: str = "system",
    ip_address: str | None = None,
) -> bool:
    """
    Log a CREATE operation for an entity.

    Args:
        entity_type: Type of entity (lead, orcamento, empresa)
        entity_id: ID of the created entity
        data: The created data (will be masked)
        user_id: User who created the entity
        ip_address: Client IP if available

    Returns:
        True if audit log was saved
    """
    return await log_audit(
        action=AuditAction.CREATE,
        entity_type=entity_type,
        entity_id=entity_id,
        changes={"after": data},
        user_id=user_id,
        ip_address=ip_address,
    )


async def log_entity_update(
    entity_type: EntityType,
    entity_id: str,
    old_data: dict[str, Any],
    new_data: dict[str, Any],
    user_id: str = "system",
    ip_address: str | None = None,
) -> bool:
    """
    Log an UPDATE operation for an entity.

    Args:
        entity_type: Type of entity (lead, orcamento, empresa)
        entity_id: ID of the updated entity
        old_data: Previous state
        new_data: New state
        user_id: User who updated the entity
        ip_address: Client IP if available

    Returns:
        True if audit log was saved
    """
    changes = compute_changes(old_data, new_data)

    return await log_audit(
        action=AuditAction.UPDATE,
        entity_type=entity_type,
        entity_id=entity_id,
        changes=changes,
        user_id=user_id,
        ip_address=ip_address,
    )


async def log_entity_delete(
    entity_type: EntityType,
    entity_id: str,
    data: dict[str, Any] | None = None,
    user_id: str = "system",
    ip_address: str | None = None,
) -> bool:
    """
    Log a DELETE operation for an entity.

    Args:
        entity_type: Type of entity (lead, orcamento, empresa)
        entity_id: ID of the deleted entity
        data: The deleted data (will be masked)
        user_id: User who deleted the entity
        ip_address: Client IP if available

    Returns:
        True if audit log was saved
    """
    return await log_audit(
        action=AuditAction.DELETE,
        entity_type=entity_type,
        entity_id=entity_id,
        changes={"before": data} if data else None,
        user_id=user_id,
        ip_address=ip_address,
    )


async def log_api_call(
    service: str,
    operation: str,
    entity_id: str | None = None,
    status: str = "success",
    metadata: dict[str, Any] | None = None,
) -> bool:
    """
    Log an external API call for audit purposes.

    This logs API calls to external services like Piperun, Z-API, Chatwoot.
    Does NOT log sensitive payloads, only operation metadata.

    Args:
        service: Name of the external service (e.g., "piperun", "zapi", "chatwoot")
        operation: Operation performed (e.g., "create_opportunity", "send_message")
        entity_id: Related entity ID if applicable
        status: Result status ("success", "error", "timeout")
        metadata: Additional context (status_code, error_message, duration_ms)

    Returns:
        True if audit log was saved
    """
    return await log_audit(
        action=AuditAction.API_CALL,
        entity_type=EntityType.API_CALL,
        entity_id=entity_id,
        metadata={
            "service": service,
            "operation": operation,
            "status": status,
            **(metadata or {}),
        },
    )


# =============================================================================
# Audit Query Functions
# =============================================================================


async def get_audit_logs(
    entity_type: EntityType | None = None,
    entity_id: str | None = None,
    action: AuditAction | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """
    Query audit logs with optional filters.

    Args:
        entity_type: Filter by entity type
        entity_id: Filter by specific entity ID
        action: Filter by action type
        start_date: Filter logs after this date
        end_date: Filter logs before this date
        limit: Maximum number of results (default 100)
        offset: Number of results to skip (for pagination)

    Returns:
        List of audit log records
    """
    try:
        client = get_supabase_client()

        if client is None:
            logger.warning("Cannot query audit logs - Supabase not configured")
            return []

        # Build query
        query = client.table("audit_logs").select("*")

        # Apply filters
        if entity_type:
            query = query.eq(
                "entity_type",
                entity_type.value if isinstance(entity_type, EntityType) else entity_type,
            )

        if entity_id:
            query = query.eq("entity_id", entity_id)

        if action:
            query = query.eq(
                "action",
                action.value if isinstance(action, AuditAction) else action,
            )

        if start_date:
            query = query.gte("timestamp", start_date.isoformat())

        if end_date:
            query = query.lte("timestamp", end_date.isoformat())

        # Order by timestamp descending (most recent first)
        query = query.order("timestamp", desc=True)

        # Apply pagination
        query = query.range(offset, offset + limit - 1)

        result = query.execute()

        return result.data if result.data else []

    except Exception as e:
        logger.error(
            "Failed to query audit logs",
            extra={"error": str(e)},
            exc_info=True,
        )
        return []


async def get_entity_audit_history(
    entity_type: EntityType,
    entity_id: str,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """
    Get complete audit history for a specific entity.

    Args:
        entity_type: Type of entity
        entity_id: ID of the entity
        limit: Maximum number of records

    Returns:
        List of audit logs for the entity, ordered by timestamp desc
    """
    return await get_audit_logs(
        entity_type=entity_type,
        entity_id=entity_id,
        limit=limit,
    )


# =============================================================================
# Retention Management
# =============================================================================


def log_audit_sync(
    action: AuditAction,
    entity_type: EntityType,
    entity_id: str | None = None,
    changes: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
    user_id: str = "system",
    ip_address: str | None = None,
) -> bool:
    """
    Synchronous version of log_audit for use in sync functions.

    This function is designed to NOT fail the main operation.
    If audit logging fails, it logs an error but returns False.

    Args:
        action: Type of action (CREATE, UPDATE, DELETE, API_CALL)
        entity_type: Type of entity being audited
        entity_id: ID of the entity (UUID or external ID)
        changes: Dictionary with before/after values (will be masked)
        metadata: Additional context (will be masked)
        user_id: User or system that performed the action
        ip_address: Client IP address if available

    Returns:
        True if audit log was saved, False otherwise
    """
    try:
        client = get_supabase_client()

        if client is None:
            logger.debug(
                "Audit log skipped - Supabase not configured",
                extra={
                    "action": action.value if isinstance(action, AuditAction) else action,
                    "entity_type": entity_type.value if isinstance(entity_type, EntityType) else entity_type,
                    "entity_id": entity_id,
                },
            )
            return False

        # Prepare audit record
        audit_record = {
            "action": action.value if isinstance(action, AuditAction) else action,
            "entity_type": entity_type.value if isinstance(entity_type, EntityType) else entity_type,
            "entity_id": entity_id,
            "user_id": user_id,
            "changes": mask_sensitive_data(changes) if changes else None,
            "metadata": mask_sensitive_data(metadata) if metadata else None,
            "ip_address": ip_address,
        }

        # Insert audit log
        result = client.table("audit_logs").insert(audit_record).execute()

        if result.data:
            logger.debug(
                "Audit log created",
                extra={
                    "audit_id": result.data[0].get("id") if result.data else None,
                    "action": audit_record["action"],
                    "entity_type": audit_record["entity_type"],
                    "entity_id": entity_id,
                },
            )
            return True
        else:
            logger.warning(
                "Audit log insert returned no data",
                extra={"audit_record": audit_record},
            )
            return False

    except Exception as e:
        # Log error but don't fail the main operation
        logger.error(
            "Failed to create audit log",
            extra={
                "action": action.value if isinstance(action, AuditAction) else action,
                "entity_type": entity_type.value if isinstance(entity_type, EntityType) else entity_type,
                "entity_id": entity_id,
                "error": str(e),
            },
            exc_info=True,
        )
        return False


def log_entity_create_sync(
    entity_type: EntityType,
    entity_id: str,
    data: dict[str, Any],
    user_id: str = "system",
    ip_address: str | None = None,
) -> bool:
    """
    Synchronous version: Log a CREATE operation for an entity.

    Args:
        entity_type: Type of entity (lead, orcamento, empresa)
        entity_id: ID of the created entity
        data: The created data (will be masked)
        user_id: User who created the entity
        ip_address: Client IP if available

    Returns:
        True if audit log was saved
    """
    return log_audit_sync(
        action=AuditAction.CREATE,
        entity_type=entity_type,
        entity_id=entity_id,
        changes={"after": data},
        user_id=user_id,
        ip_address=ip_address,
    )


def log_entity_update_sync(
    entity_type: EntityType,
    entity_id: str,
    old_data: dict[str, Any],
    new_data: dict[str, Any],
    user_id: str = "system",
    ip_address: str | None = None,
) -> bool:
    """
    Synchronous version: Log an UPDATE operation for an entity.

    Args:
        entity_type: Type of entity (lead, orcamento, empresa)
        entity_id: ID of the updated entity
        old_data: Previous state
        new_data: New state
        user_id: User who updated the entity
        ip_address: Client IP if available

    Returns:
        True if audit log was saved
    """
    changes = compute_changes(old_data, new_data)

    return log_audit_sync(
        action=AuditAction.UPDATE,
        entity_type=entity_type,
        entity_id=entity_id,
        changes=changes,
        user_id=user_id,
        ip_address=ip_address,
    )


def log_api_call_sync(
    service: str,
    operation: str,
    entity_id: str | None = None,
    status: str = "success",
    metadata: dict[str, Any] | None = None,
) -> bool:
    """
    Synchronous version: Log an external API call for audit purposes.

    This logs API calls to external services like Piperun, Z-API, Chatwoot.
    Does NOT log sensitive payloads, only operation metadata.

    Args:
        service: Name of the external service (e.g., "piperun", "zapi", "chatwoot")
        operation: Operation performed (e.g., "create_opportunity", "send_message")
        entity_id: Related entity ID if applicable
        status: Result status ("success", "error", "timeout")
        metadata: Additional context (status_code, error_message, duration_ms)

    Returns:
        True if audit log was saved
    """
    return log_audit_sync(
        action=AuditAction.API_CALL,
        entity_type=EntityType.API_CALL,
        entity_id=entity_id,
        metadata={
            "service": service,
            "operation": operation,
            "status": status,
            **(metadata or {}),
        },
    )


async def cleanup_old_audit_logs(
    retention_days: int | None = None,
) -> int:
    """
    Delete audit logs older than the retention period.

    Args:
        retention_days: Number of days to retain logs.
                       Defaults to AUDIT_RETENTION_DAYS setting or 90 days.

    Returns:
        Number of deleted records
    """
    try:
        client = get_supabase_client()

        if client is None:
            logger.warning("Cannot cleanup audit logs - Supabase not configured")
            return 0

        # Use configured retention or default
        days = retention_days or getattr(settings, "AUDIT_RETENTION_DAYS", DEFAULT_RETENTION_DAYS)

        # Calculate cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Delete old records
        result = (
            client.table("audit_logs")
            .delete()
            .lt("timestamp", cutoff_date.isoformat())
            .execute()
        )

        deleted_count = len(result.data) if result.data else 0

        logger.info(
            "Audit logs cleanup completed",
            extra={
                "deleted_count": deleted_count,
                "retention_days": days,
                "cutoff_date": cutoff_date.isoformat(),
            },
        )

        return deleted_count

    except Exception as e:
        logger.error(
            "Failed to cleanup old audit logs",
            extra={"error": str(e)},
            exc_info=True,
        )
        return 0
