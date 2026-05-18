"""
BizMind AI — Chat API
POST /chat — Main conversation endpoint wired to Agno agent team.
"""
import uuid
from datetime import datetime, timezone
from typing import Annotated
import json
import httpx
from fastapi import APIRouter, Depends, Header, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse

from backend.api.auth import get_current_user
from backend.agents.team import run_agent_team
from backend.core.logging import get_logger
from backend.core.supabase import get_supabase_admin
from backend.memory.short_term import get_history, add_message
from backend.memory.long_term import load_user_memory, save_user_memory
from backend.models.schemas import ChatRequest, ChatResponse

router = APIRouter()
logger = get_logger("chat")


@router.post("")
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

    if payload.stream:
        from backend.agents.team import run_agent_team_stream
        
        async def stream_generator():
            stream = run_agent_team_stream(
                message=payload.message,
                images=payload.images,
                history=history,
                user_memory=long_term_memory,
                user_id=user_id,
                conversation_id=conversation_id,
            )
            
            async for chunk in stream:
                if chunk["type"] == "chunk":
                    yield json.dumps({"type": "chunk", "content": chunk["content"]}) + "\n"
                elif chunk["type"] == "done":
                    result = chunk["result"]
                    # ── Persist short-term history ──
                    add_message(session_id, "user", payload.message)
                    add_message(session_id, "assistant", result.answer)

                    # ── Persist messages in Supabase ──
                    now = datetime.now(timezone.utc).isoformat()
                    sb.table("messages").insert(
                        [
                            {"id": str(uuid.uuid4()), "conversation_id": conversation_id, "role": "user", "content": payload.message, "created_at": now},
                            {"id": str(uuid.uuid4()), "conversation_id": conversation_id, "role": "assistant", "content": result.answer, "created_at": now},
                        ]
                    ).execute()

                    # Update message_count
                    sb.rpc("increment_message_count", {"conv_id": conversation_id, "delta": 2}).execute()

                    # ── Track AI usage ──
                    rag_hit = result.intent == "rag" and bool(result.sources)
                    estimated_tokens = (len(payload.message) + len(result.answer)) // 4
                    sb.table("ai_usage").insert(
                        {
                            "id": str(uuid.uuid4()), "user_id": user_id, "conversation_id": conversation_id,
                            "tokens_used": estimated_tokens, "rag_hit": rag_hit,
                            "similarity_score": result.similarity_scores[0] if result.similarity_scores else None, "created_at": now,
                        }
                    ).execute()

                    # ── Update long-term memory ──
                    await save_user_memory(user_id, history + [{"role": "user", "content": payload.message}])
                    
                    yield json.dumps({
                        "type": "done",
                        "answer": result.answer,
                        "intent": result.intent,
                        "sources": result.sources,
                        "similarity_scores": result.similarity_scores,
                        "conversation_id": conversation_id,
                        "hallucination_flagged": result.hallucination_flagged
                    }) + "\n"
                    
        return StreamingResponse(stream_generator(), media_type="application/x-ndjson")

    # ── Run agent team ────────────────────────────────────────────────────────
    result = await run_agent_team(
        message=payload.message,
        images=payload.images,
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
    
    # Approximate token count (1 token ≈ 4 chars)
    estimated_tokens = (len(payload.message) + len(result.answer)) // 4
    
    sb.table("ai_usage").insert(
        {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "conversation_id": conversation_id,
            "tokens_used": estimated_tokens,
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


@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    """
    Transcribe audio using Groq's Whisper API.
    """
    from backend.core.config import get_settings
    settings = get_settings()

    if not settings.groq_api_key:
        raise HTTPException(status_code=500, detail="GROQ_API_KEY is not configured.")

    try:
        content = await file.read()
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {settings.groq_api_key}"},
                files={
                    "file": (file.filename, content, file.content_type),
                },
                data={
                    "model": "whisper-large-v3",
                    "response_format": "json"
                }
            )
            
            response.raise_for_status()
            result = response.json()
            
            return {"text": result.get("text", "").strip()}
    except Exception as exc:
        logger.error("Audio transcription failed", error=str(exc))
        raise HTTPException(status_code=500, detail="Failed to transcribe audio.")

@router.get("/history")
async def get_chat_history(user: dict = Depends(get_current_user)):
    """Fetch the latest conversation history for the user."""
    sb = get_supabase_admin()
    user_id = user["id"]
    
    try:
        # Get the latest conversation ID for this user
        conv_res = sb.table("conversations").select("id").eq("user_id", user_id).order("created_at", desc=True).limit(1).execute()
        if not conv_res.data:
            return {"messages": [], "conversation_id": None}
            
        conv_id = conv_res.data[0]["id"]
        
        # Get messages for this conversation
        msg_res = sb.table("messages").select("*").eq("conversation_id", conv_id).order("created_at").execute()
        
        return {
            "messages": msg_res.data,
            "conversation_id": conv_id
        }
    except Exception as exc:
        logger.error("Failed to fetch chat history", error=str(exc))
        return {"messages": [], "conversation_id": None}

