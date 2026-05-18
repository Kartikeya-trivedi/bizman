"""
BizMind AI — Webhooks API
POST /webhooks/external
"""
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from backend.core.logging import get_logger
from backend.workflows.lead_notify import notify_lead
from backend.workflows.email_summary import summarize_email

router = APIRouter()
logger = get_logger("webhooks")


class WebhookPayload(BaseModel):
    event: str
    data: dict


@router.post("/external")
async def external_webhook(
    payload: WebhookPayload,
    x_webhook_token: str = Header(None, alias="X-Webhook-Token"),
):
    """
    Handle external webhook events (e.g., from Zapier, Typeform, etc.).
    Requires X-Webhook-Token header.
    """
    if x_webhook_token != "bizmind-secret":
        logger.warning("Webhook rejected: Invalid token")
        raise HTTPException(status_code=403, detail="Invalid webhook token")

    logger.info("Received webhook event", event=payload.event)

    if payload.event == "lead_created":
        lead_id = payload.data.get("lead_id")
        user_id = payload.data.get("user_id", "00000000-0000-0000-0000-000000000000")
        
        if not lead_id:
            raise HTTPException(status_code=400, detail="Missing lead_id in data")
            
        result = await notify_lead(lead_id=lead_id, user_id=user_id)
        return {"status": "success", "message": "Lead notification triggered", "result": result}
        
    elif payload.event == "email_received":
        text = payload.data.get("text")
        user_id = payload.data.get("user_id", "00000000-0000-0000-0000-000000000000")
        
        if not text:
            raise HTTPException(status_code=400, detail="Missing text in data")
            
        result = await summarize_email(text=text, user_id=user_id)
        return {"status": "success", "message": "Email summary generated", "result": result}
        
    logger.info("Webhook event ignored", event=payload.event)
    return {"status": "ignored", "message": f"Event {payload.event} not handled"}
