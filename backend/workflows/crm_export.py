"""
BizMind AI — CRM Export Workflow
Exports all user leads to /exports/leads_export.json.
Production: would POST to CRM API (Salesforce, HubSpot, etc.)
"""
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from backend.core.config import get_settings
from backend.core.logging import get_logger
from backend.core.supabase import get_supabase_admin
from backend.models.schemas import CRMExportResponse
from backend.workflows._log_helper import log_workflow

logger = get_logger("crm_export")


async def export_crm(user_id: str) -> CRMExportResponse:
    """
    Fetch all leads for user and write to /exports/leads_export.json.
    Returns export metadata.
    """
    start = time.monotonic()
    settings = get_settings()
    sb = get_supabase_admin()

    try:
        resp = (
            sb.table("leads")
            .select("*")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        leads = resp.data or []

        # Ensure exports directory exists
        exports_path = Path(settings.exports_dir)
        exports_path.mkdir(parents=True, exist_ok=True)

        export_file = exports_path / "leads_export.json"
        export_data = {
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "user_id": user_id,
            "total": len(leads),
            "leads": leads,
        }

        with open(export_file, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, default=str)

        duration_ms = int((time.monotonic() - start) * 1000)
        await log_workflow("crm_export", "success", duration_ms, user_id)

        logger.info("CRM export complete", count=len(leads), file=str(export_file), user_id=user_id)
        return CRMExportResponse(
            status="exported",
            count=len(leads),
            file="leads_export.json",
        )

    except Exception as exc:
        duration_ms = int((time.monotonic() - start) * 1000)
        await log_workflow("crm_export", "failed", duration_ms, user_id)
        logger.error("CRM export failed", error=str(exc))
        raise
