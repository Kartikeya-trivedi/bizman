"""
BizMind AI — Planner Agent
Classifies user intent into: rag | lead_capture | general | workflow
Returns JSON only.
"""
import json
import re

from google import genai
from google.genai import types

from backend.core.config import get_settings
from backend.core.errors import retry, LLM_FALLBACK
from backend.core.logging import get_logger
from backend.models.schemas import PlannerResult

logger = get_logger("planner")

PLANNER_SYSTEM_PROMPT = """You are an intent classifier for an AI Business Assistant.

Given a user message, classify it into exactly ONE of these intents:
- "rag": User is asking a question that should be answered from uploaded documents
- "lead_capture": User is providing contact information, asking for pricing, demo, or expressing specific interest in a product/service
- "workflow": User is explicitly asking to run a workflow (email summary, export leads, notify lead)
- "general": General conversation, questions about capabilities, or anything else

Rules:
- If the user mentions their name, email, or company in context of getting help → lead_capture
- If asking about pricing, demo, trial → lead_capture (hot)
- If asking about a specific document, policy, report, or "what does the document say" → rag
- If asking to summarize an email, export data, notify → workflow
- Otherwise → general

Respond ONLY with valid JSON in this exact format:
{
  "intent": "rag|lead_capture|general|workflow",
  "workflow_name": null or "email_summary|lead_notify|crm_export",
  "confidence": 0.0-1.0
}
"""


@retry(max_attempts=3, base_delay=1.0)
async def classify_intent(message: str, history: list[dict]) -> PlannerResult:
    """
    Use Gemini to classify the user's intent.
    Returns PlannerResult with intent and optional workflow_name.
    """
    settings = get_settings()
    client = genai.Client(api_key=settings.google_api_key)

    # Build recent history context (last 3 turns for planner)
    context_turns = history[-6:] if len(history) > 6 else history
    context = "\n".join(
        f"{m['role'].upper()}: {m['content']}" for m in context_turns
    )
    prompt = f"Recent conversation:\n{context}\n\nNew message: {message}"

    try:
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=PLANNER_SYSTEM_PROMPT,
                temperature=0.1,
                max_output_tokens=200,
            ),
        )
        text = response.text.strip()

        # Strip markdown code fences if present
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
        text = re.sub(r"\s*```$", "", text, flags=re.MULTILINE)

        data = json.loads(text)
        result = PlannerResult(
            intent=data.get("intent", "general"),
            workflow_name=data.get("workflow_name"),
            confidence=float(data.get("confidence", 1.0)),
        )
        logger.info(
            "Intent classified",
            intent=result.intent,
            confidence=result.confidence,
            workflow_name=result.workflow_name,
        )
        return result

    except (json.JSONDecodeError, KeyError, Exception) as exc:
        logger.warning("Planner classification failed, defaulting to general", error=str(exc))
        return PlannerResult(intent="general", confidence=0.5)
