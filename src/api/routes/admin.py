"""
Admin Panel API Routes

This module provides endpoints for the admin panel to control and monitor
the SDR agent system. All endpoints require JWT authentication.
"""

from datetime import UTC, datetime
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from src.config.settings import settings
from src.services.agent_pause import (
    _pause_cache,
    clear_cache,
    pause_agent,
    resume_agent,
)
from src.services.business_hours import (
    _load_config,
    get_current_schedule_status,
    reload_config,
)
from src.services.conversation_persistence import get_supabase_client
from src.services.lead_persistence import get_lead_by_phone
from src.services.prompt_loader import get_system_prompt_path, load_system_prompt_from_xml
from src.utils.logging import get_logger
from src.utils.validation import normalize_phone

logger = get_logger(__name__)

router = APIRouter(prefix="/api/admin", tags=["Admin"])


# --- Response Models ---


class StatusResponse(BaseModel):
    """Overall system status."""

    timestamp: str
    agent_status: str
    integrations: dict


class IntegrationStatus(BaseModel):
    """Status of a single integration."""

    status: str
    latency_ms: Optional[int] = None
    error: Optional[str] = None


class AgentStatusResponse(BaseModel):
    """Agent status response."""

    status: str
    paused_phones: list[str]
    total_paused: int


class PauseResumeRequest(BaseModel):
    """Request to pause/resume agent."""

    phone: Optional[str] = None


class PauseResumeResponse(BaseModel):
    """Response for pause/resume operations."""

    success: bool
    message: str
    phone: Optional[str] = None


class BusinessHoursResponse(BaseModel):
    """Business hours configuration."""

    timezone: str
    schedule: dict
    current_status: dict


class BusinessHoursUpdateRequest(BaseModel):
    """Request to update business hours."""

    timezone: Optional[str] = None
    schedule: Optional[dict] = None


class ReloadPromptResponse(BaseModel):
    """Response for prompt reload."""

    success: bool
    message: str


# --- Leads Types ---


class LeadResponse(BaseModel):
    """Lead data response."""

    id: str
    phone: str
    name: Optional[str] = None
    email: Optional[str] = None
    city: Optional[str] = None
    uf: Optional[str] = None
    product: Optional[str] = None
    volume: Optional[str] = None
    urgency: Optional[str] = None
    knows_seleto: Optional[bool] = None
    temperature: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class LeadsListResponse(BaseModel):
    """Paginated leads list response."""

    items: list[LeadResponse]
    total: int
    page: int
    limit: int


class ConversationMessageResponse(BaseModel):
    """Single conversation message."""

    id: str
    role: str
    content: str
    timestamp: str


class ConversationResponse(BaseModel):
    """Conversation history response."""

    messages: list[ConversationMessageResponse]
    total: int


# --- Status Endpoints ---


@router.get("/status", response_model=StatusResponse)
async def get_system_status():
    """
    Get overall system status including all integrations.

    This endpoint checks the health of all external integrations
    (WhatsApp, Supabase, OpenAI, PipeRun, Chatwoot) and returns
    their status.
    """
    integrations = {}

    # Check Supabase
    try:
        from src.services.conversation_persistence import get_supabase_client

        client = get_supabase_client()
        if client:
            integrations["supabase"] = {"status": "ok"}
        else:
            integrations["supabase"] = {"status": "error", "error": "Client not configured"}
    except Exception as e:
        integrations["supabase"] = {"status": "error", "error": str(e)}

    # Check OpenAI (via settings)
    if settings.OPENAI_API_KEY:
        integrations["openai"] = {"status": "ok"}
    else:
        integrations["openai"] = {"status": "error", "error": "API key not configured"}

    # Check Z-API (WhatsApp)
    if settings.ZAPI_INSTANCE_ID and settings.ZAPI_INSTANCE_TOKEN:
        integrations["whatsapp"] = {"status": "ok"}
    else:
        integrations["whatsapp"] = {"status": "error", "error": "Not configured"}

    # Check PipeRun
    if settings.PIPERUN_API_TOKEN:
        integrations["piperun"] = {"status": "ok"}
    else:
        integrations["piperun"] = {"status": "warning", "error": "Not configured"}

    # Check Chatwoot
    if settings.CHATWOOT_API_URL and settings.CHATWOOT_API_TOKEN:
        integrations["chatwoot"] = {"status": "ok"}
    else:
        integrations["chatwoot"] = {"status": "warning", "error": "Not configured"}

    # Determine overall status
    has_error = any(i.get("status") == "error" for i in integrations.values())
    agent_status = "error" if has_error else "active"

    return StatusResponse(
        timestamp=datetime.now(UTC).isoformat(),
        agent_status=agent_status,
        integrations=integrations,
    )


# --- Agent Control Endpoints ---


@router.get("/agent/status", response_model=AgentStatusResponse)
async def get_agent_status():
    """
    Get agent status including list of paused conversations.

    Returns the current operational status and a list of phone numbers
    for which the agent is currently paused.
    """
    paused_phones = [
        phone for phone, state in _pause_cache.items() if state.get("paused", False)
    ]

    return AgentStatusResponse(
        status="active",
        paused_phones=paused_phones,
        total_paused=len(paused_phones),
    )


@router.post("/agent/pause", response_model=PauseResumeResponse)
async def pause_agent_endpoint(request: PauseResumeRequest):
    """
    Pause the agent globally or for a specific phone number.

    If phone is not provided, this is a global pause (not yet implemented).
    If phone is provided, pauses the agent for that specific conversation.
    """
    if not request.phone:
        # Global pause not implemented yet
        return PauseResumeResponse(
            success=False,
            message="Global pause not implemented. Please provide a phone number.",
            phone=None,
        )

    success = pause_agent(
        request.phone, reason="admin_panel", sender_name="Admin Panel"
    )

    if success:
        logger.info(
            "Agent paused via admin panel",
            extra={"phone": request.phone},
        )
        return PauseResumeResponse(
            success=True,
            message=f"Agent paused for {request.phone}",
            phone=request.phone,
        )
    else:
        return PauseResumeResponse(
            success=False,
            message="Failed to pause agent",
            phone=request.phone,
        )


@router.post("/agent/resume", response_model=PauseResumeResponse)
async def resume_agent_endpoint(request: PauseResumeRequest):
    """
    Resume the agent globally or for a specific phone number.

    If phone is not provided, this is a global resume (not yet implemented).
    If phone is provided, resumes the agent for that specific conversation.
    """
    if not request.phone:
        # Global resume not implemented yet
        return PauseResumeResponse(
            success=False,
            message="Global resume not implemented. Please provide a phone number.",
            phone=None,
        )

    success = resume_agent(
        request.phone, reason="admin_panel", resumed_by="Admin Panel"
    )

    if success:
        logger.info(
            "Agent resumed via admin panel",
            extra={"phone": request.phone},
        )
        return PauseResumeResponse(
            success=True,
            message=f"Agent resumed for {request.phone}",
            phone=request.phone,
        )
    else:
        return PauseResumeResponse(
            success=False,
            message="Failed to resume agent",
            phone=request.phone,
        )


@router.post("/agent/reload-prompt", response_model=ReloadPromptResponse)
async def reload_agent_prompt():
    """
    Reload the system prompt from the XML file.

    This allows updating the agent's behavior without restarting the server.
    Note: This reloads the prompt file but doesn't update running agents.
    """
    try:
        prompt_path = get_system_prompt_path()
        prompt = load_system_prompt_from_xml(prompt_path)
        if prompt:
            logger.info("System prompt reloaded via admin panel")
            return ReloadPromptResponse(
                success=True,
                message="System prompt reloaded successfully",
            )
        else:
            return ReloadPromptResponse(
                success=False,
                message="Failed to load system prompt",
            )
    except Exception as e:
        logger.error(
            "Failed to reload system prompt",
            extra={"error": str(e)},
            exc_info=True,
        )
        return ReloadPromptResponse(
            success=False,
            message=f"Error reloading prompt: {str(e)}",
        )


# --- Configuration Endpoints ---


@router.get("/config/business-hours", response_model=BusinessHoursResponse)
async def get_business_hours():
    """
    Get current business hours configuration.

    Returns the timezone, schedule for each day, and current status.
    """
    config = _load_config()
    current_status = get_current_schedule_status()

    return BusinessHoursResponse(
        timezone=config.get("timezone", "America/Sao_Paulo"),
        schedule=config.get("schedule", {}),
        current_status=current_status,
    )


@router.put("/config/business-hours", response_model=BusinessHoursResponse)
async def update_business_hours(request: BusinessHoursUpdateRequest):
    """
    Update business hours configuration.

    Note: This currently only reloads the config from file.
    Full persistence is not yet implemented.
    """
    # For now, just reload the config
    # TODO: Implement full persistence to file/database
    reload_config()
    config = _load_config()
    current_status = get_current_schedule_status()

    logger.info("Business hours config reloaded via admin panel")

    return BusinessHoursResponse(
        timezone=config.get("timezone", "America/Sao_Paulo"),
        schedule=config.get("schedule", {}),
        current_status=current_status,
    )


# --- Cache Management ---


@router.post("/cache/clear")
async def clear_pause_cache(phone: Optional[str] = Query(None)):
    """
    Clear the pause state cache.

    If phone is provided, clears only that phone's cache.
    Otherwise, clears the entire cache.
    """
    clear_cache(phone)

    if phone:
        logger.info("Cache cleared for phone via admin panel", extra={"phone": phone})
        return {"success": True, "message": f"Cache cleared for {phone}"}
    else:
        logger.info("Full cache cleared via admin panel")
        return {"success": True, "message": "Full cache cleared"}


# --- Leads Endpoints ---


@router.get("/leads", response_model=LeadsListResponse)
async def list_leads(
    temperature: Optional[str] = Query(None, description="Filter by temperature (frio/morno/quente)"),
    search: Optional[str] = Query(None, description="Search by name, phone, or city"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    sort_by: str = Query("updated_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
):
    """
    List leads with pagination and filters.

    Supports filtering by temperature, searching by name/phone/city,
    and sorting by various fields.
    """
    client = get_supabase_client()
    if not client:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        # Build query
        query = client.table("leads").select("*", count="exact")

        # Apply temperature filter
        if temperature:
            query = query.eq("temperature", temperature)

        # Apply search filter (ilike for case-insensitive search)
        if search:
            # Search in name, phone, or city
            query = query.or_(
                f"name.ilike.%{search}%,phone.ilike.%{search}%,city.ilike.%{search}%"
            )

        # Apply sorting
        if sort_order.lower() == "desc":
            query = query.order(sort_by, desc=True)
        else:
            query = query.order(sort_by, desc=False)

        # Apply pagination
        offset = (page - 1) * limit
        query = query.range(offset, offset + limit - 1)

        # Execute query
        response = query.execute()

        # Get total count
        total = response.count if response.count is not None else len(response.data)

        # Convert to response format
        items = []
        for lead in response.data:
            items.append(
                LeadResponse(
                    id=str(lead.get("id", "")),
                    phone=lead.get("phone", ""),
                    name=lead.get("name"),
                    email=lead.get("email"),
                    city=lead.get("city"),
                    uf=lead.get("uf"),
                    product=lead.get("product"),
                    volume=lead.get("volume"),
                    urgency=lead.get("urgency"),
                    knows_seleto=lead.get("knows_seleto"),
                    temperature=lead.get("temperature"),
                    created_at=lead.get("created_at"),
                    updated_at=lead.get("updated_at"),
                )
            )

        return LeadsListResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
        )

    except Exception as e:
        logger.error(
            "Failed to list leads",
            extra={"error": str(e)},
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=f"Failed to list leads: {str(e)}")


@router.get("/leads/{phone}", response_model=LeadResponse)
async def get_lead(phone: str):
    """
    Get a single lead by phone number.

    Returns detailed lead information including all fields.
    """
    normalized_phone = normalize_phone(phone)
    if not normalized_phone:
        raise HTTPException(status_code=400, detail="Invalid phone number format")

    lead = get_lead_by_phone(normalized_phone)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    return LeadResponse(
        id=str(lead.get("id", "")),
        phone=lead.get("phone", ""),
        name=lead.get("name"),
        email=lead.get("email"),
        city=lead.get("city"),
        uf=lead.get("uf"),
        product=lead.get("product"),
        volume=lead.get("volume"),
        urgency=lead.get("urgency"),
        knows_seleto=lead.get("knows_seleto"),
        temperature=lead.get("temperature"),
        created_at=lead.get("created_at"),
        updated_at=lead.get("updated_at"),
    )


@router.get("/leads/{phone}/conversation", response_model=ConversationResponse)
async def get_lead_conversation(
    phone: str,
    limit: int = Query(100, ge=1, le=500, description="Max messages to return"),
):
    """
    Get conversation history for a lead.

    Returns all messages exchanged with the lead, ordered by timestamp.
    """
    normalized_phone = normalize_phone(phone)
    if not normalized_phone:
        raise HTTPException(status_code=400, detail="Invalid phone number format")

    client = get_supabase_client()
    if not client:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        # Query conversations table
        response = (
            client.table("conversations")
            .select("*")
            .eq("lead_phone", normalized_phone)
            .order("timestamp", desc=False)
            .limit(limit)
            .execute()
        )

        messages = []
        for msg in response.data:
            messages.append(
                ConversationMessageResponse(
                    id=str(msg.get("id", "")),
                    role=msg.get("role", "user"),
                    content=msg.get("content", ""),
                    timestamp=msg.get("timestamp", ""),
                )
            )

        return ConversationResponse(
            messages=messages,
            total=len(messages),
        )

    except Exception as e:
        logger.error(
            "Failed to get conversation",
            extra={"phone": normalized_phone, "error": str(e)},
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=f"Failed to get conversation: {str(e)}")
