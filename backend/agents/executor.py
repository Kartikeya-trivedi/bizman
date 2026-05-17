"""
BizMind AI — Executor Agent
Routes tasks based on Planner intent and executes them.
Handles: rag | lead_capture | general | workflow
Uses Agno Agent for LLM interactions.
"""
import uuid
from datetime import datetime, timezone

from agno.agent import Agent

from backend.core.config import get_settings
from backend.core.errors import retry, LLM_FALLBACK
from backend.core.gemini import get_gemini_model
from backend.core.logging import get_logger
from backend.core.supabase import get_supabase_admin
from backend.models.schemas import LeadExtraction, PlannerResult

logger = get_logger("executor")

GENERAL_SYSTEM_PROMPT = """You are BizMind AI, an intelligent business assistant for small and medium enterprises (SMEs).
You help with business strategy, customer management, document analysis, and general business questions.
Be professional, concise, and actionable. When relevant, structure your response with clear headings or bullet points.
"""

LEAD_EXTRACTION_PROMPT = """Extract lead information from the user's message.

Fields to extract:
- name: person's name (required if mentioned)
- email: email address (if present)
- company: company name (if mentioned)
- need: what they are looking for / their business need
- status: 
  * "hot" = asked about pricing, demo, trial, wants to buy, urgent need
  * "warm" = showed clear interest, asked specific questions
  * "cold" = general inquiry, just browsing
"""


@retry(max_attempts=3, base_delay=1.0)
async def execute(
    message: str,
    planner_result: PlannerResult,
    history: list[dict],
    user_memory: str,
    user_id: str,
    conversation_id: str,
) -> dict:
    """Execute the appropriate task based on planner intent."""
    settings = get_settings()
    intent = planner_result.intent

    if intent == "rag":
        return await _execute_rag(message, user_id)
    elif intent == "lead_capture":
        return await _execute_lead_capture(message, user_id)
    elif intent == "workflow":
        return await _execute_workflow(message, planner_result.workflow_name)
    else:
        return await _execute_general(message, history, user_memory)


async def _execute_rag(message: str, user_id: str) -> dict:
    from backend.rag.pipeline import run_rag_pipeline
    result = await run_rag_pipeline(message, user_id)
    return {
        "answer": result.answer,
        "sources": result.sources,
        "similarity_scores": result.similarity_scores,
        "rag_context": "\n".join(result.sources),
    }


async def _execute_lead_capture(message: str, user_id: str) -> dict:
    """Extract lead info from message using Agno Agent with structured output."""
    agent = Agent(
        name="BizMind Lead Extractor",
        model=get_gemini_model(temperature=0.1, max_tokens=300),
        instructions=LEAD_EXTRACTION_PROMPT,
        output_schema=LeadExtraction,
        markdown=False,
    )

    try:
        response = await agent.arun(message)
        lead: LeadExtraction = response.content
    except Exception as exc:
        logger.warning("Lead extraction parse failed", error=str(exc))
        lead = LeadExtraction(name="Unknown", need=message, status="cold")

    sb = get_supabase_admin()
    now = datetime.now(timezone.utc).isoformat()
    row = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "name": lead.name,
        "email": lead.email,
        "company": lead.company,
        "need": lead.need,
        "status": lead.status,
        "created_at": now,
        "updated_at": now,
    }
    try:
        sb.table("leads").insert(row).execute()
        logger.info("Lead captured", lead_status=lead.status, user_id=user_id)
    except Exception as exc:
        logger.error("Failed to store lead", error=str(exc))

    status_messages = {
        "hot": "I've noted that you're interested in getting started right away! Our team will reach out shortly to arrange a demo or discuss pricing.",
        "warm": "Thank you for your interest! I've logged your inquiry and someone will be in touch soon.",
        "cold": "Thanks for reaching out! I've captured your details. Feel free to ask any questions about our services.",
    }
    answer = status_messages.get(lead.status, status_messages["cold"])
    if lead.name and lead.name != "Unknown":
        answer = f"Hi {lead.name}! " + answer

    return {"answer": answer, "sources": [], "similarity_scores": [], "rag_context": ""}


async def _execute_workflow(message: str, workflow_name: str | None) -> dict:
    workflow_hints = {
        "email_summary": "To summarize an email, please use the **Email Summarizer** in the Workflows section.",
        "lead_notify": "To notify about a hot lead, use the **Lead Notifier** in the Workflows section.",
        "crm_export": "To export your leads, use the **CRM Export** button in the Workflows section.",
    }
    answer = workflow_hints.get(
        workflow_name or "",
        "I can help with workflows! Head to the Workflows section to run email summaries, lead notifications, or CRM exports.",
    )
    return {"answer": answer, "sources": [], "similarity_scores": [], "rag_context": ""}


async def _execute_general(
    message: str,
    history: list[dict],
    user_memory: str,
) -> dict:
    """Agno Agent response with conversation history and user memory."""
    memory_block = f"\n\nUser context from memory:\n{user_memory}" if user_memory else ""
    system = GENERAL_SYSTEM_PROMPT + memory_block

    agent = Agent(
        name="BizMind Assistant",
        model=get_gemini_model(temperature=0.7, max_tokens=1024),
        instructions=system,
        markdown=True,
    )

    # Build conversation context for the prompt
    history_lines = []
    for msg in history[-20:]:
        role = "USER" if msg["role"] == "user" else "ASSISTANT"
        history_lines.append(f"{role}: {msg['content']}")
    history_lines.append(f"USER: {message}")
    prompt = "\n".join(history_lines)

    response = await agent.arun(prompt)
    return {
        "answer": response.content,
        "sources": [],
        "similarity_scores": [],
        "rag_context": "",
    }
