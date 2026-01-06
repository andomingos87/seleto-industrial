"""
LGPD (Lei Geral de Proteção de Dados) API endpoints (TECH-031).

This module provides endpoints for:
- Data export (portability) - GET /api/lgpd/data-export/{phone}
- Data correction - PUT /api/lgpd/data-correction/{phone}
- Data deletion/anonymization - DELETE /api/lgpd/data-deletion/{phone}
- Run retention jobs - POST /api/lgpd/run-retention-jobs

All endpoints require admin authentication.
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, EmailStr, Field

from src.jobs.data_retention_job import run_all_retention_jobs, run_daily_jobs, run_weekly_jobs
from src.services.audit_trail import log_api_call_sync
from src.services.conversation_persistence import get_supabase_client
from src.services.data_retention import (
    anonymize_context_data,
    anonymize_phone,
    anonymize_text,
    EMAIL_PLACEHOLDER,
    NAME_PLACEHOLDER,
)
from src.utils.logging import get_logger
from src.utils.validation import normalize_phone, validate_phone

logger = get_logger(__name__)

router = APIRouter(prefix="/api/lgpd", tags=["LGPD"])


# Request/Response models
class DataCorrectionRequest(BaseModel):
    """Request model for data correction."""

    name: str | None = Field(None, description="New name")
    email: EmailStr | None = Field(None, description="New email")
    city: str | None = Field(None, description="New city")
    uf: str | None = Field(None, max_length=2, description="New state code")
    company: str | None = Field(None, description="New company name")


class DataExportResponse(BaseModel):
    """Response model for data export."""

    phone: str
    lead: dict[str, Any] | None = None
    conversations: list[dict[str, Any]] = []
    context: dict[str, Any] | None = None
    empresas: list[dict[str, Any]] = []
    orcamentos: list[dict[str, Any]] = []
    exported_at: str


class RetentionJobResponse(BaseModel):
    """Response model for retention job execution."""

    status: str
    started_at: str
    completed_at: str
    results: dict[str, dict[str, int]]


class DeletionResponse(BaseModel):
    """Response model for data deletion."""

    status: str
    phone: str
    anonymized_at: str
    details: dict[str, Any]


@router.get("/data-export/{phone}", response_model=DataExportResponse)
async def export_data(
    phone: str,
    include_messages: bool = Query(True, description="Include conversation messages"),
    include_context: bool = Query(True, description="Include conversation context"),
):
    """
    Export all personal data for a phone number (LGPD right to access/portability).

    This endpoint returns all data associated with a phone number:
    - Lead information
    - Conversation messages
    - Conversation context
    - Associated empresas
    - Associated orcamentos

    Args:
        phone: Phone number to export data for
        include_messages: Whether to include conversation messages
        include_context: Whether to include conversation context

    Returns:
        DataExportResponse with all associated data
    """
    normalized_phone = normalize_phone(phone)
    if not normalized_phone or not validate_phone(normalized_phone):
        raise HTTPException(status_code=400, detail="Invalid phone number format")

    client = get_supabase_client()
    if not client:
        raise HTTPException(status_code=503, detail="Database unavailable")

    # Log the access request
    log_api_call_sync(
        service="lgpd",
        endpoint="/data-export",
        method="GET",
        status_code=200,
        request_data={"phone": normalized_phone},
    )

    try:
        result: dict[str, Any] = {
            "phone": normalized_phone,
            "lead": None,
            "conversations": [],
            "context": None,
            "empresas": [],
            "orcamentos": [],
            "exported_at": datetime.utcnow().isoformat(),
        }

        # Get lead data
        lead_response = (
            client.table("leads")
            .select("*")
            .eq("phone", normalized_phone)
            .execute()
        )
        if lead_response.data:
            result["lead"] = lead_response.data[0]
            lead_id = lead_response.data[0].get("id")

            # Get orcamentos for this lead
            if lead_id:
                orcamentos_response = (
                    client.table("orcamentos")
                    .select("*")
                    .eq("lead", lead_id)
                    .execute()
                )
                result["orcamentos"] = orcamentos_response.data or []

        # Get conversation messages
        if include_messages:
            messages_response = (
                client.table("conversation_messages")
                .select("*")
                .eq("lead_phone", normalized_phone)
                .order("timestamp", desc=False)
                .execute()
            )
            result["conversations"] = messages_response.data or []

        # Get conversation context
        if include_context:
            context_response = (
                client.table("conversation_context")
                .select("*")
                .eq("lead_phone", normalized_phone)
                .execute()
            )
            if context_response.data:
                result["context"] = context_response.data[0]

        # Get empresas associated with this phone/lead
        empresas_response = (
            client.table("empresas")
            .select("*")
            .eq("telefone", normalized_phone)
            .execute()
        )
        result["empresas"] = empresas_response.data or []

        logger.info(
            "Data exported for LGPD request",
            extra={
                "phone": normalized_phone,
                "has_lead": result["lead"] is not None,
                "message_count": len(result["conversations"]),
                "empresa_count": len(result["empresas"]),
                "orcamento_count": len(result["orcamentos"]),
            },
        )

        return DataExportResponse(**result)

    except Exception as e:
        logger.error(
            "Failed to export data",
            extra={"phone": normalized_phone, "error": str(e)},
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Failed to export data")


@router.put("/data-correction/{phone}")
async def correct_data(phone: str, correction: DataCorrectionRequest):
    """
    Correct personal data for a phone number (LGPD right to rectification).

    This endpoint allows updating personal data:
    - name
    - email
    - city
    - uf (state)
    - company

    Args:
        phone: Phone number to correct data for
        correction: DataCorrectionRequest with fields to update

    Returns:
        Updated lead data
    """
    normalized_phone = normalize_phone(phone)
    if not normalized_phone or not validate_phone(normalized_phone):
        raise HTTPException(status_code=400, detail="Invalid phone number format")

    client = get_supabase_client()
    if not client:
        raise HTTPException(status_code=503, detail="Database unavailable")

    # Build update payload (only non-None fields)
    update_data = {k: v for k, v in correction.model_dump().items() if v is not None}

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    # Log the correction request
    log_api_call_sync(
        service="lgpd",
        endpoint="/data-correction",
        method="PUT",
        status_code=200,
        request_data={"phone": normalized_phone, "fields": list(update_data.keys())},
    )

    try:
        # Update lead
        update_data["updated_at"] = datetime.utcnow().isoformat()

        response = (
            client.table("leads")
            .update(update_data)
            .eq("phone", normalized_phone)
            .execute()
        )

        if not response.data:
            raise HTTPException(status_code=404, detail="Lead not found")

        # Also update context if name/email changed
        context_updates = {}
        if correction.name:
            context_updates["name"] = correction.name
        if correction.email:
            context_updates["email"] = correction.email

        if context_updates:
            # Get current context
            ctx_response = (
                client.table("conversation_context")
                .select("context_data")
                .eq("lead_phone", normalized_phone)
                .execute()
            )

            if ctx_response.data:
                current_context = ctx_response.data[0].get("context_data", {})
                current_context.update(context_updates)

                client.table("conversation_context").update(
                    {"context_data": current_context}
                ).eq("lead_phone", normalized_phone).execute()

        logger.info(
            "Data corrected for LGPD request",
            extra={
                "phone": normalized_phone,
                "fields_updated": list(update_data.keys()),
            },
        )

        return {
            "status": "success",
            "phone": normalized_phone,
            "updated_fields": list(update_data.keys()),
            "updated_at": update_data["updated_at"],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to correct data",
            extra={"phone": normalized_phone, "error": str(e)},
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Failed to correct data")


@router.delete("/data-deletion/{phone}", response_model=DeletionResponse)
async def delete_data(
    phone: str,
    hard_delete: bool = Query(False, description="Permanently delete instead of anonymize"),
):
    """
    Delete/anonymize personal data for a phone number (LGPD right to erasure).

    By default, this endpoint anonymizes data (replaces personal info with placeholders).
    If hard_delete=True, data is permanently deleted (not recommended for audit purposes).

    Note: Audit logs are retained for legal compliance regardless of this request.

    Args:
        phone: Phone number to delete data for
        hard_delete: If True, permanently delete data. If False, anonymize.

    Returns:
        DeletionResponse with deletion status
    """
    normalized_phone = normalize_phone(phone)
    if not normalized_phone or not validate_phone(normalized_phone):
        raise HTTPException(status_code=400, detail="Invalid phone number format")

    client = get_supabase_client()
    if not client:
        raise HTTPException(status_code=503, detail="Database unavailable")

    # Log the deletion request
    log_api_call_sync(
        service="lgpd",
        endpoint="/data-deletion",
        method="DELETE",
        status_code=200,
        request_data={"phone": normalized_phone, "hard_delete": hard_delete},
    )

    try:
        details: dict[str, Any] = {
            "lead": False,
            "messages": 0,
            "context": False,
            "empresas": 0,
            "orcamentos": 0,
        }

        anonymized_phone = anonymize_phone(normalized_phone)

        if hard_delete:
            # Permanent deletion (not recommended)
            # Delete orcamentos first (FK constraint)
            lead_response = (
                client.table("leads")
                .select("id")
                .eq("phone", normalized_phone)
                .execute()
            )
            if lead_response.data:
                lead_id = lead_response.data[0].get("id")
                orc_response = (
                    client.table("orcamentos")
                    .delete()
                    .eq("lead", lead_id)
                    .execute()
                )
                details["orcamentos"] = len(orc_response.data or [])

            # Delete messages
            msg_response = (
                client.table("conversation_messages")
                .delete()
                .eq("lead_phone", normalized_phone)
                .execute()
            )
            details["messages"] = len(msg_response.data or [])

            # Delete context
            ctx_response = (
                client.table("conversation_context")
                .delete()
                .eq("lead_phone", normalized_phone)
                .execute()
            )
            details["context"] = bool(ctx_response.data)

            # Delete empresas by phone
            emp_response = (
                client.table("empresas")
                .delete()
                .eq("telefone", normalized_phone)
                .execute()
            )
            details["empresas"] = len(emp_response.data or [])

            # Delete lead
            lead_del_response = (
                client.table("leads")
                .delete()
                .eq("phone", normalized_phone)
                .execute()
            )
            details["lead"] = bool(lead_del_response.data)

        else:
            # Anonymization (recommended)
            # Anonymize lead
            lead_response = (
                client.table("leads")
                .update({
                    "phone": anonymized_phone,
                    "name": NAME_PLACEHOLDER,
                    "email": EMAIL_PLACEHOLDER,
                })
                .eq("phone", normalized_phone)
                .execute()
            )
            details["lead"] = bool(lead_response.data)

            # Anonymize messages
            msg_response = (
                client.table("conversation_messages")
                .select("id, content")
                .eq("lead_phone", normalized_phone)
                .execute()
            )
            if msg_response.data:
                for msg in msg_response.data:
                    anonymized_content = anonymize_text(msg.get("content", ""))
                    client.table("conversation_messages").update({
                        "content": anonymized_content,
                        "lead_phone": anonymized_phone,
                    }).eq("id", msg["id"]).execute()
                details["messages"] = len(msg_response.data)

            # Anonymize context
            ctx_response = (
                client.table("conversation_context")
                .select("id, context_data")
                .eq("lead_phone", normalized_phone)
                .execute()
            )
            if ctx_response.data:
                for ctx in ctx_response.data:
                    anonymized_ctx = anonymize_context_data(ctx.get("context_data", {}))
                    client.table("conversation_context").update({
                        "context_data": anonymized_ctx,
                        "lead_phone": anonymized_phone,
                    }).eq("id", ctx["id"]).execute()
                details["context"] = True

            # Anonymize empresas
            emp_response = (
                client.table("empresas")
                .select("id")
                .eq("telefone", normalized_phone)
                .execute()
            )
            if emp_response.data:
                for emp in emp_response.data:
                    client.table("empresas").update({
                        "telefone": anonymized_phone,
                        "email": EMAIL_PLACEHOLDER,
                    }).eq("id", emp["id"]).execute()
                details["empresas"] = len(emp_response.data)

        logger.info(
            "Data deleted/anonymized for LGPD request",
            extra={
                "phone": normalized_phone,
                "hard_delete": hard_delete,
                "details": details,
            },
        )

        return DeletionResponse(
            status="deleted" if hard_delete else "anonymized",
            phone=normalized_phone,
            anonymized_at=datetime.utcnow().isoformat(),
            details=details,
        )

    except Exception as e:
        logger.error(
            "Failed to delete/anonymize data",
            extra={"phone": normalized_phone, "error": str(e)},
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Failed to delete data")


@router.post("/run-retention-jobs", response_model=RetentionJobResponse)
async def run_retention_jobs_endpoint(
    job_type: str = Query("all", description="Job type: all, daily, or weekly"),
):
    """
    Manually trigger data retention jobs.

    This endpoint runs the data retention jobs:
    - all: Run all retention jobs
    - daily: Run daily jobs (message/context anonymization, operations cleanup)
    - weekly: Run weekly jobs (inactive lead anonymization)

    Args:
        job_type: Type of jobs to run (all, daily, weekly)

    Returns:
        RetentionJobResponse with job results
    """
    valid_types = ("all", "daily", "weekly")
    if job_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid job_type. Must be one of: {valid_types}",
        )

    # Log the job execution request
    log_api_call_sync(
        service="lgpd",
        endpoint="/run-retention-jobs",
        method="POST",
        status_code=200,
        request_data={"job_type": job_type},
    )

    try:
        started_at = datetime.utcnow().isoformat()

        if job_type == "daily":
            results = run_daily_jobs()
        elif job_type == "weekly":
            results = run_weekly_jobs()
        else:
            results = run_all_retention_jobs()

        completed_at = datetime.utcnow().isoformat()

        logger.info(
            "Retention jobs executed via API",
            extra={
                "job_type": job_type,
                "results": results,
            },
        )

        return RetentionJobResponse(
            status="completed",
            started_at=started_at,
            completed_at=completed_at,
            results=results,
        )

    except Exception as e:
        logger.error(
            "Failed to run retention jobs",
            extra={"job_type": job_type, "error": str(e)},
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail="Failed to run retention jobs")


@router.get("/retention-config")
async def get_retention_config():
    """
    Get current data retention configuration.

    Returns the current retention periods and settings.
    """
    from src.config.settings import settings

    return {
        "transcript_retention_days": settings.TRANSCRIPT_RETENTION_DAYS,
        "context_retention_days": settings.CONTEXT_RETENTION_DAYS,
        "lead_inactivity_days": settings.LEAD_INACTIVITY_DAYS,
        "pending_operations_retention_days": settings.PENDING_OPERATIONS_RETENTION_DAYS,
        "audit_retention_days": settings.AUDIT_RETENTION_DAYS,
    }
