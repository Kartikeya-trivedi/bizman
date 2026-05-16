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
    Log a hot lead notification.
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

    # STUB: In production → SendGrid / Slack
    logger.info(
        "Lead notification STUB (production: send email/Slack)",
        lead_id=lead_id,
        lead_name=lead.get("name"),
        lead_status=lead.get("status"),
        user_id=user_id,
    )

    duration_ms = int((time.monotonic() - start) * 1000)
    await log_workflow("lead_notify", "success", duration_ms, user_id)

    return LeadNotifyResponse(
        status="notified",
        timestamp=timestamp,
        lead_id=lead_id,
    )
