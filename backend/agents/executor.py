"""
BizMind AI — Executor Agent
Routes tasks based on Planner intent and executes them.
Handles: rag | lead_capture | general | workflow
"""
import json
import re
import uuid
from datetime import datetime, timezone

from google import genai
from google.genai import types

from backend.core.config import get_settings
from backend.core.errors import retry, LLM_FALLBACK
from backend.core.logging import get_logger
from backend.core.supabase import get_supabase_admin
from backend.models.schemas import LeadExtraction, PlannerResult

logger = get_logger("executor")

GENERAL_SYSTEM_PROMPT = """You are BizMind AI, an intelligent business assistant for small and medium enterprises (SMEs).
You help with business strategy, customer management, document analysis, and general business questions.
Be professional, concise, and actionable. When relevant, structure your response with clear headings or bullet points.
"""

LEAD_EXTRACTION_PROMPT = """Extract lead information from the user's message. Return ONLY valid JSON.

Fields to extract:
- name: person's name (required if mentioned)
- email: email address (if present)
- company: company name (if mentioned)
- need: what they are looking for / their business need
- status: 
  * "hot" = asked about pricing, demo, trial, wants to buy, urgent need
  * "warm" = showed clear interest, asked specific questions
  * "cold" = general inquiry, just browsing

Return format:
{
  "name": "...",
  "email": "..." or null,
  "company": "..." or null,
  "need": "...",
  "status": "hot|warm|cold"
}
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
        return await _execute_lead_capture(message, user_id, settings)
    elif intent == "workflow":
        return await _execute_workflow(message, planner_result.workflow_name)
    else:
        return await _execute_general(message, history, user_memory, settings)


async def _execute_rag(message: str, user_id: str) -> dict:
    from backend.rag.pipeline import run_rag_pipeline
    result = await run_rag_pipeline(message, user_id)
    return {
        "answer": result.answer,
        "sources": result.sources,
        "similarity_scores": result.similarity_scores,
        "rag_context": "\n".join(result.sources),
    }


async def _execute_lead_capture(message: str, user_id: str, settings) -> dict:
    """Extract lead info from message, classify, and store in Supabase."""
    client = genai.Client(api_key=settings.google_api_key)
    try:
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=message,
            config=types.GenerateContentConfig(
                system_instruction=LEAD_EXTRACTION_PROMPT,
                temperature=0.1,
                max_output_tokens=300,
            ),
        )
        text = response.text.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
        text = re.sub(r"\s*```$", "", text, flags=re.MULTILINE)
        data = json.loads(text)
        lead = LeadExtraction(**data)
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
    settings,
) -> dict:
    """Direct Gemini response with conversation history and user memory."""
    memory_block = f"\n\nUser context from memory:\n{user_memory}" if user_memory else ""
    system = GENERAL_SYSTEM_PROMPT + memory_block

    client = genai.Client(api_key=settings.google_api_key)

    # Build content history for the new SDK
    contents = []
    for msg in history[-20:]:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(types.Content(role=role, parts=[types.Part(text=msg["content"])]))

    # Add the current user message
    contents.append(types.Content(role="user", parts=[types.Part(text=message)]))

    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=contents,
        config=types.GenerateContentConfig(
            system_instruction=system,
            temperature=0.7,
            max_output_tokens=1024,
        ),
    )
    return {
        "answer": response.text,
        "sources": [],
        "similarity_scores": [],
        "rag_context": "",
    }
