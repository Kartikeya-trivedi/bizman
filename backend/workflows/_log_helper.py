"""
BizMind AI — Workflow Logging Helper
Shared utility to log workflow events to the workflow_logs Supabase table.
"""
import uuid
from datetime import datetime, timezone

from backend.core.logging import get_logger
from backend.core.supabase import get_supabase_admin

logger = get_logger("workflow_log")


async def log_workflow(
    workflow_name: str,
    status: str,
    duration_ms: int,
    user_id: str,
) -> None:
    """Insert a workflow execution record into workflow_logs."""
    sb = get_supabase_admin()
    try:
        sb.table("workflow_logs").insert(
            {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "workflow_name": workflow_name,
                "status": status,
                "duration_ms": duration_ms,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        ).execute()
    except Exception as exc:
        logger.warning("Failed to log workflow", workflow=workflow_name, error=str(exc))
