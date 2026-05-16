"""
BizMind AI — Workflows API
POST /workflows/email-summary, /lead-notify, /crm-export
"""
from fastapi import APIRouter, Depends

from backend.api.auth import get_current_user
from backend.core.logging import get_logger
from backend.models.schemas import (
    CRMExportResponse,
    EmailSummaryRequest,
    EmailSummaryResponse,
    LeadNotifyRequest,
    LeadNotifyResponse,
)
from backend.workflows.email_summary import summarize_email
from backend.workflows.lead_notify import notify_lead
from backend.workflows.crm_export import export_crm

router = APIRouter()
logger = get_logger("workflows")


@router.post("/email-summary", response_model=EmailSummaryResponse)
async def email_summary(
    payload: EmailSummaryRequest,
    user: dict = Depends(get_current_user),
):
    """Summarize a raw email into structured key points and action items."""
    logger.info("Email summary requested", user_id=user["id"])
    return await summarize_email(payload.text, user_id=user["id"])


@router.post("/lead-notify", response_model=LeadNotifyResponse)
async def lead_notify(
    payload: LeadNotifyRequest,
    user: dict = Depends(get_current_user),
):
    """Log a hot lead notification event."""
    logger.info("Lead notify requested", lead_id=payload.lead_id, user_id=user["id"])
    return await notify_lead(payload.lead_id, user_id=user["id"])


@router.post("/crm-export", response_model=CRMExportResponse)
async def crm_export(user: dict = Depends(get_current_user)):
    """Export all leads to a local JSON file."""
    logger.info("CRM export requested", user_id=user["id"])
    return await export_crm(user_id=user["id"])
