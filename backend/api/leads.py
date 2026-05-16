"""
BizMind AI — Leads API
GET /leads, POST /leads, PATCH /leads/{id}
"""
import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Header, Query

from backend.api.auth import get_current_user
from backend.core.logging import get_logger
from backend.core.supabase import get_supabase_admin
from backend.models.schemas import LeadCreate, LeadResponse, LeadUpdate

router = APIRouter(prefix="/leads")
logger = get_logger("leads")


@router.get("", response_model=list[LeadResponse])
async def list_leads(
    status: str | None = Query(None, description="Filter by status: hot|warm|cold"),
    user: dict = Depends(get_current_user),
):
    """Return all leads for the authenticated user."""
    sb = get_supabase_admin()
    query = sb.table("leads").select("*").eq("user_id", user["id"]).order("created_at", desc=True)
    if status:
        query = query.eq("status", status)
    resp = query.execute()
    return [LeadResponse(**row) for row in (resp.data or [])]


@router.post("", response_model=LeadResponse, status_code=201)
async def create_lead(
    payload: LeadCreate,
    user: dict = Depends(get_current_user),
):
    """Manually create a new lead."""
    sb = get_supabase_admin()
    now = datetime.now(timezone.utc).isoformat()
    row = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "name": payload.name,
        "email": payload.email,
        "company": payload.company,
        "need": payload.need,
        "status": payload.status,
        "created_at": now,
        "updated_at": now,
    }
    resp = sb.table("leads").insert(row).execute()
    if not resp.data:
        raise HTTPException(status_code=500, detail="Failed to create lead.")
    logger.info("Lead created", lead_id=row["id"], user_id=user["id"])
    return LeadResponse(**resp.data[0])


@router.patch("/{lead_id}", response_model=LeadResponse)
async def update_lead(
    lead_id: str,
    payload: LeadUpdate,
    user: dict = Depends(get_current_user),
):
    """Update a lead (partial update)."""
    sb = get_supabase_admin()
    updates = payload.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=422, detail="No fields to update.")
    updates["updated_at"] = datetime.now(timezone.utc).isoformat()
    resp = (
        sb.table("leads")
        .update(updates)
        .eq("id", lead_id)
        .eq("user_id", user["id"])
        .execute()
    )
    if not resp.data:
        raise HTTPException(status_code=404, detail="Lead not found.")
    logger.info("Lead updated", lead_id=lead_id)
    return LeadResponse(**resp.data[0])
