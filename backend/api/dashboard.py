"""
BizMind AI — Dashboard API
GET /dashboard/stats, /conversation-logs, /workflow-logs, /ai-usage
"""
from fastapi import APIRouter, Depends

from backend.api.auth import get_current_user
from backend.core.logging import get_logger
from backend.core.supabase import get_supabase_admin
from backend.models.schemas import (
    AIUsageEntry,
    ConversationLog,
    DashboardStats,
    WorkflowLog,
)

router = APIRouter()
logger = get_logger("dashboard")


@router.get("/stats", response_model=DashboardStats)
async def get_stats(user: dict = Depends(get_current_user)):
    """Aggregate stats for the authenticated user's dashboard."""
    sb = get_supabase_admin()
    uid = user["id"]

    leads = sb.table("leads").select("status").eq("user_id", uid).execute()
    lead_rows = leads.data or []
    total_leads = len(lead_rows)
    hot_leads = sum(1 for r in lead_rows if r.get("status") == "hot")

    convos = sb.table("conversations").select("id").eq("user_id", uid).execute()
    total_conversations = len(convos.data or [])

    wf = sb.table("workflow_logs").select("id").eq("user_id", uid).execute()
    workflows_run = len(wf.data or [])

    docs = sb.table("documents").select("id").eq("user_id", uid).execute()
    documents_uploaded = len(docs.data or [])

    usage = sb.table("ai_usage").select("similarity_score").eq("user_id", uid).execute()
    scores = [r["similarity_score"] for r in (usage.data or []) if r.get("similarity_score")]
    avg_similarity = round(sum(scores) / len(scores), 4) if scores else 0.0

    return DashboardStats(
        total_leads=total_leads,
        hot_leads=hot_leads,
        total_conversations=total_conversations,
        workflows_run=workflows_run,
        documents_uploaded=documents_uploaded,
        avg_similarity_score=avg_similarity,
    )


@router.get("/conversation-logs", response_model=list[ConversationLog])
async def get_conversation_logs(user: dict = Depends(get_current_user)):
    sb = get_supabase_admin()
    resp = (
        sb.table("conversations")
        .select("*")
        .eq("user_id", user["id"])
        .order("created_at", desc=True)
        .limit(50)
        .execute()
    )
    return [ConversationLog(**r) for r in (resp.data or [])]


@router.get("/workflow-logs", response_model=list[WorkflowLog])
async def get_workflow_logs(user: dict = Depends(get_current_user)):
    sb = get_supabase_admin()
    resp = (
        sb.table("workflow_logs")
        .select("*")
        .eq("user_id", user["id"])
        .order("created_at", desc=True)
        .limit(50)
        .execute()
    )
    return [WorkflowLog(**r) for r in (resp.data or [])]


@router.get("/ai-usage", response_model=list[AIUsageEntry])
async def get_ai_usage(user: dict = Depends(get_current_user)):
    """Daily aggregated AI usage stats for the last 30 days."""
    sb = get_supabase_admin()
    resp = (
        sb.table("ai_usage")
        .select("*")
        .eq("user_id", user["id"])
        .order("created_at", desc=True)
        .limit(500)
        .execute()
    )
    rows = resp.data or []

    # Aggregate by date
    daily: dict[str, dict] = {}
    for row in rows:
        date = row.get("created_at", "")[:10]
        if date not in daily:
            daily[date] = {"tokens_used": 0, "rag_hits": 0, "total_queries": 0}
        daily[date]["tokens_used"] += row.get("tokens_used", 0)
        daily[date]["rag_hits"] += 1 if row.get("rag_hit") else 0
        daily[date]["total_queries"] += 1

    return [
        AIUsageEntry(date=date, **stats)
        for date, stats in sorted(daily.items(), reverse=True)
    ]
