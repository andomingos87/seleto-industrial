"""
Admin Panel API Routes

This module provides endpoints for the admin panel to control and monitor
the SDR agent system. All endpoints require JWT authentication.

Phase 3 additions:
- Knowledge Base: Products CRUD, Technical Questions queue
- Audit Logs: Query and view audit trail
- Prompts: Edit system prompts with backup/restore
"""

import shutil
from datetime import UTC, datetime
from pathlib import Path
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
from src.services.audit_trail import (
    AuditAction,
    EntityType,
    get_audit_logs,
    log_entity_create,
    log_entity_delete,
    log_entity_update,
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

# Paths for prompts
PROMPTS_DIR = Path(__file__).parent.parent.parent.parent / "prompts" / "system_prompt"
BACKUPS_DIR = PROMPTS_DIR / "backups"


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


# --- Knowledge Base Types ---


class ProductResponse(BaseModel):
    """Product data response."""

    id: str
    name: str
    category: str
    description: str
    specifications: list[str]
    productivity: Optional[str] = None
    is_available: bool
    created_at: str
    updated_at: str


class ProductCreateRequest(BaseModel):
    """Request to create a product."""

    name: str
    category: str
    description: str
    specifications: list[str] = []
    productivity: Optional[str] = None
    is_available: bool = True


class ProductUpdateRequest(BaseModel):
    """Request to update a product."""

    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    specifications: Optional[list[str]] = None
    productivity: Optional[str] = None
    is_available: Optional[bool] = None


class ProductsListResponse(BaseModel):
    """Paginated products list response."""

    items: list[ProductResponse]
    total: int
    page: int
    limit: int


class TechnicalQuestionResponse(BaseModel):
    """Technical question data response."""

    id: str
    phone: str
    question: str
    context: Optional[str] = None
    timestamp: str
    answered: bool
    answered_at: Optional[str] = None
    answer: Optional[str] = None


class TechnicalQuestionsListResponse(BaseModel):
    """Paginated technical questions list response."""

    items: list[TechnicalQuestionResponse]
    total: int
    page: int
    limit: int


class MarkAnsweredRequest(BaseModel):
    """Request to mark a question as answered."""

    answer: Optional[str] = None


# --- Audit Log Types ---


class AuditLogResponse(BaseModel):
    """Audit log entry response."""

    id: str
    timestamp: str
    action: str
    entity_type: str
    entity_id: Optional[str] = None
    user_id: str
    changes: Optional[dict] = None
    metadata: Optional[dict] = None
    ip_address: Optional[str] = None


class AuditLogsListResponse(BaseModel):
    """Paginated audit logs list response."""

    items: list[AuditLogResponse]
    total: int
    page: int
    limit: int


# --- Prompt Types ---


class PromptResponse(BaseModel):
    """Prompt data response."""

    name: str
    content: str
    path: str
    last_modified: str
    size_bytes: int


class PromptListResponse(BaseModel):
    """List of available prompts."""

    prompts: list[str]


class PromptSaveRequest(BaseModel):
    """Request to save a prompt."""

    content: str


class PromptBackupResponse(BaseModel):
    """Backup info response."""

    name: str
    timestamp: str
    size_bytes: int


class PromptBackupsListResponse(BaseModel):
    """List of backups for a prompt."""

    backups: list[PromptBackupResponse]


class RestoreBackupRequest(BaseModel):
    """Request to restore a backup."""

    backup_name: str


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


# --- Knowledge Base: Products Endpoints ---

VALID_CATEGORIES = {"formadora", "cortadora", "ensacadeira", "misturador", "linha_automatica"}


@router.get("/knowledge/products", response_model=ProductsListResponse)
async def list_products(
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search by name"),
    is_available: Optional[bool] = Query(None, description="Filter by availability"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
):
    """
    List products with pagination and filters.

    Supports filtering by category, availability, and searching by name.
    """
    client = get_supabase_client()
    if not client:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        # Build query
        query = client.table("products").select("*", count="exact")

        # Apply filters
        if category:
            if category not in VALID_CATEGORIES:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid category. Must be one of: {', '.join(VALID_CATEGORIES)}",
                )
            query = query.eq("category", category)

        if is_available is not None:
            query = query.eq("is_available", is_available)

        if search:
            query = query.ilike("name", f"%{search}%")

        # Order by name
        query = query.order("name", desc=False)

        # Apply pagination
        offset = (page - 1) * limit
        query = query.range(offset, offset + limit - 1)

        # Execute query
        response = query.execute()

        # Get total count
        total = response.count if response.count is not None else len(response.data)

        # Convert to response format
        items = []
        for product in response.data:
            specs = product.get("specifications", [])
            if isinstance(specs, str):
                import json
                specs = json.loads(specs)
            items.append(
                ProductResponse(
                    id=str(product.get("id", "")),
                    name=product.get("name", ""),
                    category=product.get("category", ""),
                    description=product.get("description", ""),
                    specifications=specs if isinstance(specs, list) else [],
                    productivity=product.get("productivity"),
                    is_available=product.get("is_available", True),
                    created_at=product.get("created_at", ""),
                    updated_at=product.get("updated_at", ""),
                )
            )

        return ProductsListResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to list products",
            extra={"error": str(e)},
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=f"Failed to list products: {str(e)}")


@router.post("/knowledge/products", response_model=ProductResponse)
async def create_product(request: ProductCreateRequest):
    """
    Create a new product.

    Validates category and creates the product in the database.
    """
    client = get_supabase_client()
    if not client:
        raise HTTPException(status_code=503, detail="Database not available")

    # Validate category
    if request.category not in VALID_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category. Must be one of: {', '.join(VALID_CATEGORIES)}",
        )

    try:
        # Insert product
        result = client.table("products").insert({
            "name": request.name,
            "category": request.category,
            "description": request.description,
            "specifications": request.specifications,
            "productivity": request.productivity,
            "is_available": request.is_available,
        }).execute()

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to create product")

        product = result.data[0]

        # Log audit
        await log_entity_create(
            entity_type=EntityType.LEAD,  # Using LEAD as placeholder, should add PRODUCT
            entity_id=str(product.get("id")),
            data={"name": request.name, "category": request.category},
            user_id="admin_panel",
        )

        logger.info(
            "Product created via admin panel",
            extra={"product_id": product.get("id"), "product_name": request.name},
        )

        specs = product.get("specifications", [])
        return ProductResponse(
            id=str(product.get("id", "")),
            name=product.get("name", ""),
            category=product.get("category", ""),
            description=product.get("description", ""),
            specifications=specs if isinstance(specs, list) else [],
            productivity=product.get("productivity"),
            is_available=product.get("is_available", True),
            created_at=product.get("created_at", ""),
            updated_at=product.get("updated_at", ""),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to create product",
            extra={"error": str(e)},
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=f"Failed to create product: {str(e)}")


@router.get("/knowledge/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: str):
    """
    Get a single product by ID.
    """
    client = get_supabase_client()
    if not client:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        result = client.table("products").select("*").eq("id", product_id).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Product not found")

        product = result.data[0]
        specs = product.get("specifications", [])

        return ProductResponse(
            id=str(product.get("id", "")),
            name=product.get("name", ""),
            category=product.get("category", ""),
            description=product.get("description", ""),
            specifications=specs if isinstance(specs, list) else [],
            productivity=product.get("productivity"),
            is_available=product.get("is_available", True),
            created_at=product.get("created_at", ""),
            updated_at=product.get("updated_at", ""),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get product",
            extra={"product_id": product_id, "error": str(e)},
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=f"Failed to get product: {str(e)}")


@router.put("/knowledge/products/{product_id}", response_model=ProductResponse)
async def update_product(product_id: str, request: ProductUpdateRequest):
    """
    Update an existing product.
    """
    client = get_supabase_client()
    if not client:
        raise HTTPException(status_code=503, detail="Database not available")

    # Validate category if provided
    if request.category and request.category not in VALID_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category. Must be one of: {', '.join(VALID_CATEGORIES)}",
        )

    try:
        # Get current product for audit
        current = client.table("products").select("*").eq("id", product_id).execute()
        if not current.data:
            raise HTTPException(status_code=404, detail="Product not found")

        old_data = current.data[0]

        # Build update data (only non-None fields)
        update_data = {}
        if request.name is not None:
            update_data["name"] = request.name
        if request.category is not None:
            update_data["category"] = request.category
        if request.description is not None:
            update_data["description"] = request.description
        if request.specifications is not None:
            update_data["specifications"] = request.specifications
        if request.productivity is not None:
            update_data["productivity"] = request.productivity
        if request.is_available is not None:
            update_data["is_available"] = request.is_available

        if not update_data:
            raise HTTPException(status_code=400, detail="No fields to update")

        # Update product
        result = client.table("products").update(update_data).eq("id", product_id).execute()

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to update product")

        product = result.data[0]

        # Log audit
        await log_entity_update(
            entity_type=EntityType.LEAD,  # Using LEAD as placeholder
            entity_id=str(product_id),
            old_data={"name": old_data.get("name"), "is_available": old_data.get("is_available")},
            new_data={"name": product.get("name"), "is_available": product.get("is_available")},
            user_id="admin_panel",
        )

        logger.info(
            "Product updated via admin panel",
            extra={"product_id": product_id},
        )

        specs = product.get("specifications", [])
        return ProductResponse(
            id=str(product.get("id", "")),
            name=product.get("name", ""),
            category=product.get("category", ""),
            description=product.get("description", ""),
            specifications=specs if isinstance(specs, list) else [],
            productivity=product.get("productivity"),
            is_available=product.get("is_available", True),
            created_at=product.get("created_at", ""),
            updated_at=product.get("updated_at", ""),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to update product",
            extra={"product_id": product_id, "error": str(e)},
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=f"Failed to update product: {str(e)}")


@router.delete("/knowledge/products/{product_id}")
async def delete_product(product_id: str):
    """
    Delete a product.
    """
    client = get_supabase_client()
    if not client:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        # Get current product for audit
        current = client.table("products").select("*").eq("id", product_id).execute()
        if not current.data:
            raise HTTPException(status_code=404, detail="Product not found")

        old_data = current.data[0]

        # Delete product
        client.table("products").delete().eq("id", product_id).execute()

        # Log audit
        await log_entity_delete(
            entity_type=EntityType.LEAD,  # Using LEAD as placeholder
            entity_id=str(product_id),
            data={"name": old_data.get("name"), "category": old_data.get("category")},
            user_id="admin_panel",
        )

        logger.info(
            "Product deleted via admin panel",
            extra={"product_id": product_id, "product_name": old_data.get("name")},
        )

        return {"success": True, "message": f"Product '{old_data.get('name')}' deleted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to delete product",
            extra={"product_id": product_id, "error": str(e)},
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=f"Failed to delete product: {str(e)}")


# --- Knowledge Base: Technical Questions Endpoints ---


@router.get("/knowledge/questions", response_model=TechnicalQuestionsListResponse)
async def list_technical_questions(
    answered: Optional[bool] = Query(None, description="Filter by answered status"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
):
    """
    List technical questions with pagination and filters.
    """
    client = get_supabase_client()
    if not client:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        # Build query
        query = client.table("technical_questions").select("*", count="exact")

        # Apply filters
        if answered is not None:
            query = query.eq("answered", answered)

        # Order by timestamp descending (newest first)
        query = query.order("timestamp", desc=True)

        # Apply pagination
        offset = (page - 1) * limit
        query = query.range(offset, offset + limit - 1)

        # Execute query
        response = query.execute()

        # Get total count
        total = response.count if response.count is not None else len(response.data)

        # Convert to response format
        items = []
        for question in response.data:
            items.append(
                TechnicalQuestionResponse(
                    id=str(question.get("id", "")),
                    phone=question.get("phone", ""),
                    question=question.get("question", ""),
                    context=question.get("context"),
                    timestamp=question.get("timestamp", ""),
                    answered=question.get("answered", False),
                    answered_at=question.get("answered_at"),
                    answer=question.get("answer"),
                )
            )

        return TechnicalQuestionsListResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
        )

    except Exception as e:
        logger.error(
            "Failed to list technical questions",
            extra={"error": str(e)},
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=f"Failed to list technical questions: {str(e)}")


@router.put("/knowledge/questions/{question_id}", response_model=TechnicalQuestionResponse)
async def mark_question_answered(question_id: str, request: MarkAnsweredRequest):
    """
    Mark a technical question as answered.
    """
    client = get_supabase_client()
    if not client:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        # Check if question exists
        current = client.table("technical_questions").select("*").eq("id", question_id).execute()
        if not current.data:
            raise HTTPException(status_code=404, detail="Question not found")

        # Update question
        update_data = {
            "answered": True,
            "answered_at": datetime.now(UTC).isoformat(),
        }
        if request.answer:
            update_data["answer"] = request.answer

        result = client.table("technical_questions").update(update_data).eq("id", question_id).execute()

        if not result.data:
            raise HTTPException(status_code=500, detail="Failed to update question")

        question = result.data[0]

        logger.info(
            "Technical question marked as answered via admin panel",
            extra={"question_id": question_id},
        )

        return TechnicalQuestionResponse(
            id=str(question.get("id", "")),
            phone=question.get("phone", ""),
            question=question.get("question", ""),
            context=question.get("context"),
            timestamp=question.get("timestamp", ""),
            answered=question.get("answered", False),
            answered_at=question.get("answered_at"),
            answer=question.get("answer"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to mark question as answered",
            extra={"question_id": question_id, "error": str(e)},
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=f"Failed to update question: {str(e)}")


# --- Audit Logs Endpoints ---


@router.get("/logs/audit", response_model=AuditLogsListResponse)
async def list_audit_logs(
    action: Optional[str] = Query(None, description="Filter by action (CREATE, UPDATE, DELETE, API_CALL)"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type (lead, orcamento, empresa, api_call)"),
    start_date: Optional[str] = Query(None, description="Filter logs after this date (ISO format)"),
    end_date: Optional[str] = Query(None, description="Filter logs before this date (ISO format)"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=200, description="Items per page"),
):
    """
    List audit logs with filters and pagination.
    """
    try:
        # Parse dates if provided
        start_dt = None
        end_dt = None
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

        # Convert string to enum if provided
        action_enum = None
        entity_enum = None
        if action:
            try:
                action_enum = AuditAction(action)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid action. Must be one of: {', '.join([a.value for a in AuditAction])}",
                )
        if entity_type:
            try:
                entity_enum = EntityType(entity_type)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid entity_type. Must be one of: {', '.join([e.value for e in EntityType])}",
                )

        offset = (page - 1) * limit

        # Get logs using existing service
        logs = await get_audit_logs(
            action=action_enum,
            entity_type=entity_enum,
            start_date=start_dt,
            end_date=end_dt,
            limit=limit,
            offset=offset,
        )

        # Get total count (separate query)
        client = get_supabase_client()
        total = 0
        if client:
            count_query = client.table("audit_logs").select("*", count="exact")
            if action_enum:
                count_query = count_query.eq("action", action_enum.value)
            if entity_enum:
                count_query = count_query.eq("entity_type", entity_enum.value)
            if start_dt:
                count_query = count_query.gte("timestamp", start_dt.isoformat())
            if end_dt:
                count_query = count_query.lte("timestamp", end_dt.isoformat())
            if user_id:
                count_query = count_query.eq("user_id", user_id)
            count_result = count_query.execute()
            total = count_result.count if count_result.count is not None else len(logs)

        # Convert to response format
        items = []
        for log in logs:
            items.append(
                AuditLogResponse(
                    id=str(log.get("id", "")),
                    timestamp=log.get("timestamp", ""),
                    action=log.get("action", ""),
                    entity_type=log.get("entity_type", ""),
                    entity_id=log.get("entity_id"),
                    user_id=log.get("user_id", ""),
                    changes=log.get("changes"),
                    metadata=log.get("metadata"),
                    ip_address=log.get("ip_address"),
                )
            )

        return AuditLogsListResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to list audit logs",
            extra={"error": str(e)},
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=f"Failed to list audit logs: {str(e)}")


@router.get("/logs/audit/{log_id}", response_model=AuditLogResponse)
async def get_audit_log(log_id: str):
    """
    Get a single audit log by ID.
    """
    client = get_supabase_client()
    if not client:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        result = client.table("audit_logs").select("*").eq("id", log_id).execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Audit log not found")

        log = result.data[0]

        return AuditLogResponse(
            id=str(log.get("id", "")),
            timestamp=log.get("timestamp", ""),
            action=log.get("action", ""),
            entity_type=log.get("entity_type", ""),
            entity_id=log.get("entity_id"),
            user_id=log.get("user_id", ""),
            changes=log.get("changes"),
            metadata=log.get("metadata"),
            ip_address=log.get("ip_address"),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get audit log",
            extra={"log_id": log_id, "error": str(e)},
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=f"Failed to get audit log: {str(e)}")


# --- Prompts Endpoints ---


@router.get("/config/prompts", response_model=PromptListResponse)
async def list_prompts():
    """
    List available prompts.
    """
    try:
        if not PROMPTS_DIR.exists():
            return PromptListResponse(prompts=[])

        prompts = []
        for f in sorted(PROMPTS_DIR.glob("*.xml")):
            prompts.append(f.stem)

        return PromptListResponse(prompts=prompts)

    except Exception as e:
        logger.error(
            "Failed to list prompts",
            extra={"error": str(e)},
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=f"Failed to list prompts: {str(e)}")


@router.get("/config/prompts/{name}", response_model=PromptResponse)
async def get_prompt(name: str):
    """
    Get prompt content by name.
    """
    try:
        prompt_path = PROMPTS_DIR / f"{name}.xml"

        if not prompt_path.exists():
            raise HTTPException(status_code=404, detail=f"Prompt '{name}' not found")

        # Security: Validate path is within PROMPTS_DIR
        if not prompt_path.resolve().is_relative_to(PROMPTS_DIR.resolve()):
            raise HTTPException(status_code=400, detail="Invalid prompt name")

        content = prompt_path.read_text(encoding="utf-8")
        stat = prompt_path.stat()

        return PromptResponse(
            name=name,
            content=content,
            path=str(prompt_path.relative_to(PROMPTS_DIR.parent.parent)),
            last_modified=datetime.fromtimestamp(stat.st_mtime).isoformat(),
            size_bytes=stat.st_size,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to get prompt",
            extra={"name": name, "error": str(e)},
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=f"Failed to get prompt: {str(e)}")


@router.put("/config/prompts/{name}")
async def save_prompt(name: str, request: PromptSaveRequest):
    """
    Save prompt with automatic backup.
    """
    try:
        prompt_path = PROMPTS_DIR / f"{name}.xml"

        if not prompt_path.exists():
            raise HTTPException(status_code=404, detail=f"Prompt '{name}' not found")

        # Security: Validate path
        if not prompt_path.resolve().is_relative_to(PROMPTS_DIR.resolve()):
            raise HTTPException(status_code=400, detail="Invalid prompt name")

        # Validate XML content
        try:
            import xml.etree.ElementTree as ET
            ET.fromstring(request.content)
        except ET.ParseError as e:
            raise HTTPException(status_code=400, detail=f"Invalid XML: {str(e)}")

        # Create backup directory if needed
        BACKUPS_DIR.mkdir(exist_ok=True)

        # Create backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = BACKUPS_DIR / f"{name}_{timestamp}.xml"
        shutil.copy2(prompt_path, backup_path)

        # Save new content
        prompt_path.write_text(request.content, encoding="utf-8")

        logger.info(
            "Prompt saved via admin panel",
            extra={"name": name, "backup": str(backup_path)},
        )

        return {
            "success": True,
            "message": f"Prompt '{name}' saved successfully",
            "backup_path": str(backup_path.relative_to(PROMPTS_DIR.parent.parent)),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to save prompt",
            extra={"name": name, "error": str(e)},
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=f"Failed to save prompt: {str(e)}")


@router.get("/config/prompts/{name}/backups", response_model=PromptBackupsListResponse)
async def list_prompt_backups(name: str):
    """
    List available backups for a prompt.
    """
    try:
        if not BACKUPS_DIR.exists():
            return PromptBackupsListResponse(backups=[])

        backups = []
        for f in sorted(BACKUPS_DIR.glob(f"{name}_*.xml"), reverse=True):
            stat = f.stat()
            # Extract timestamp from filename
            timestamp_str = f.stem.replace(f"{name}_", "")
            backups.append(
                PromptBackupResponse(
                    name=f.name,
                    timestamp=timestamp_str,
                    size_bytes=stat.st_size,
                )
            )

        return PromptBackupsListResponse(backups=backups[:20])  # Limit to 20 most recent

    except Exception as e:
        logger.error(
            "Failed to list prompt backups",
            extra={"name": name, "error": str(e)},
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=f"Failed to list backups: {str(e)}")


@router.post("/config/prompts/{name}/restore")
async def restore_prompt_backup(name: str, request: RestoreBackupRequest):
    """
    Restore a prompt from backup.
    """
    try:
        backup_path = BACKUPS_DIR / request.backup_name
        prompt_path = PROMPTS_DIR / f"{name}.xml"

        if not backup_path.exists():
            raise HTTPException(status_code=404, detail="Backup not found")

        if not prompt_path.exists():
            raise HTTPException(status_code=404, detail=f"Prompt '{name}' not found")

        # Security: Validate paths
        if not backup_path.resolve().is_relative_to(BACKUPS_DIR.resolve()):
            raise HTTPException(status_code=400, detail="Invalid backup name")

        # Create backup of current before restoring
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pre_restore_backup = BACKUPS_DIR / f"{name}_pre_restore_{timestamp}.xml"
        shutil.copy2(prompt_path, pre_restore_backup)

        # Restore
        shutil.copy2(backup_path, prompt_path)

        logger.info(
            "Prompt restored from backup via admin panel",
            extra={"name": name, "backup": request.backup_name},
        )

        return {
            "success": True,
            "message": f"Prompt '{name}' restored from {request.backup_name}",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to restore prompt backup",
            extra={"name": name, "backup": request.backup_name, "error": str(e)},
            exc_info=True,
        )
        raise HTTPException(status_code=500, detail=f"Failed to restore backup: {str(e)}")
