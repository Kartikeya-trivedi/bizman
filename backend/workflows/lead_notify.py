"""
BizMind AI — Lead Notifier Workflow
Logs hot lead notification event to workflow_logs.
Stub: in production, this would trigger SendGrid email or Slack webhook.
"""
import time
from datetime import datetime, timezone

from backend.core.logging import get_logger
from backend.core.supabase import get_supabase_admin
from backend.models.schemas import LeadNotifyResponse
from backend.workflows._log_helper import log_workflow

logger = get_logger("lead_notify")


async def notify_lead(lead_id: str, user_id: str) -> LeadNotifyResponse:
    """
    Log a hot lead notification and generate a follow-up message.
    Production: would trigger email/Slack webhook via SendGrid or similar.
    """
    start = time.monotonic()
    sb = get_supabase_admin()

    # Verify lead exists
    resp = (
        sb.table("leads")
        .select("id, name, email, status")
        .eq("id", lead_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not resp.data:
        duration_ms = int((time.monotonic() - start) * 1000)
        await log_workflow("lead_notify", "failed", duration_ms, user_id)
        raise ValueError(f"Lead {lead_id} not found.")

    lead = resp.data[0]
    timestamp = datetime.now(timezone.utc).isoformat()

    # Generate a follow-up email using Gemini
    from agno.agent import Agent
    from backend.core.gemini import get_gemini_model
    
    agent = Agent(
        name="BizMind Lead Follow-up",
        model=get_gemini_model(temperature=0.7, max_tokens=300),
        instructions="You are a professional business assistant. Generate a short, polite follow-up email to a lead. Do not include subject line, just the body.",
    )
    prompt = f"Lead Name: {lead.get('name')}\nStatus: {lead.get('status')}\nPlease write a brief follow-up email to this person."
    try:
        response = await agent.arun(prompt)
        follow_up_message = response.content.strip() if isinstance(response.content, str) else str(response.content).strip()
    except Exception as exc:
        logger.error("Failed to generate follow-up message", error=str(exc))
        follow_up_message = f"Hi {lead.get('name')},\n\nWe wanted to follow up regarding your recent inquiry. Please let us know if you need any assistance.\n\nBest regards,\nThe Team"

    # STUB: In production → SendGrid / Slack
    logger.info(
        "Lead notification STUB (production: send email/Slack)",
        lead_id=lead_id,
        lead_name=lead.get("name"),
        lead_status=lead.get("status"),
        user_id=user_id,
        follow_up_message=follow_up_message,
    )

    duration_ms = int((time.monotonic() - start) * 1000)
    await log_workflow("lead_notify", "success", duration_ms, user_id)

    return LeadNotifyResponse(
        status="notified",
        timestamp=timestamp,
        lead_id=lead_id,
    )
