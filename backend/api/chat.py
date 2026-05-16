"""
BizMind AI — Chat API
POST /chat — Main conversation endpoint wired to Agno agent team.
"""
import uuid
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, Header

from backend.api.auth import get_current_user
from backend.agents.team import run_agent_team
from backend.core.logging import get_logger
from backend.core.supabase import get_supabase_admin
from backend.memory.short_term import get_history, add_message
from backend.memory.long_term import load_user_memory, save_user_memory
from backend.models.schemas import ChatRequest, ChatResponse

router = APIRouter()
logger = get_logger("chat")


@router.post("", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    user: dict = Depends(get_current_user),
):
    """
    Main chat endpoint:
    1. Load short-term history + long-term user memory
    2. Run the Agno agent team (planner → executor → validator)
    3. Persist messages to Supabase
    4. Return structured response
    """
    sb = get_supabase_admin()
    user_id = user["id"]

    # ── Session & Conversation bookkeeping ───────────────────────────────────
    session_id = payload.session_id or str(uuid.uuid4())
    conversation_id = payload.conversation_id

    if not conversation_id:
        # Create new conversation record
        conversation_id = str(uuid.uuid4())
        sb.table("conversations").insert(
            {
                "id": conversation_id,
                "user_id": user_id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "message_count": 0,
            }
        ).execute()

    # ── Load context ─────────────────────────────────────────────────────────
    history = get_history(session_id)
    long_term_memory = await load_user_memory(user_id)

    # ── Run agent team ────────────────────────────────────────────────────────
    result = await run_agent_team(
        message=payload.message,
        history=history,
        user_memory=long_term_memory,
        user_id=user_id,
        conversation_id=conversation_id,
    )

    # ── Persist short-term history ────────────────────────────────────────────
    add_message(session_id, "user", payload.message)
    add_message(session_id, "assistant", result.answer)

    # ── Persist messages in Supabase ──────────────────────────────────────────
    now = datetime.now(timezone.utc).isoformat()
    sb.table("messages").insert(
        [
            {
                "id": str(uuid.uuid4()),
                "conversation_id": conversation_id,
                "role": "user",
                "content": payload.message,
                "created_at": now,
            },
            {
                "id": str(uuid.uuid4()),
                "conversation_id": conversation_id,
                "role": "assistant",
                "content": result.answer,
                "created_at": now,
            },
        ]
    ).execute()

    # Update message_count
    sb.rpc(
        "increment_message_count",
        {"conv_id": conversation_id, "delta": 2},
    ).execute()

    # ── Track AI usage ────────────────────────────────────────────────────────
    rag_hit = result.intent == "rag" and bool(result.sources)
    sb.table("ai_usage").insert(
        {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "conversation_id": conversation_id,
            "tokens_used": 0,  # Gemini SDK doesn't always expose token counts easily
            "rag_hit": rag_hit,
            "similarity_score": result.similarity_scores[0] if result.similarity_scores else None,
            "created_at": now,
        }
    ).execute()

    # ── Update long-term memory asynchronously ────────────────────────────────
    await save_user_memory(user_id, history + [{"role": "user", "content": payload.message}])

    logger.info(
        "Chat completed",
        user_id=user_id,
        intent=result.intent,
        conversation_id=conversation_id,
        hallucination_flagged=result.hallucination_flagged,
    )

    return ChatResponse(
        answer=result.answer,
        intent=result.intent,
        sources=result.sources,
        similarity_scores=result.similarity_scores,
        conversation_id=conversation_id,
        hallucination_flagged=result.hallucination_flagged,
    )
