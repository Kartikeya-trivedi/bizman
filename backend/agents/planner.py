"""
BizMind AI — Planner Agent
Classifies user intent into: rag | lead_capture | general | workflow
Uses Agno Agent with structured output (PlannerResult).
"""
from agno.agent import Agent
from agno.media import Image as AgnoImage

from backend.core.config import get_settings
from backend.core.errors import retry, LLM_FALLBACK
from backend.core.gemini import get_gemini_model
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
- If the user explicitly asks to "summarize the document" or "summarize this document", ALWAYS output "rag". Do this even if the conversation history says no document exists.
- If asking about a specific document, policy, report, or "what does the document say" → rag
- If the user mentions their name, email, or company in context of getting help → lead_capture
- If asking about pricing, demo, trial → lead_capture (hot)
- If asking to summarize an email, export data, notify → workflow
- Otherwise → general
"""


@retry(max_attempts=3, base_delay=1.0)
async def classify_intent(message: str, history: list[dict], images: list[str] = None) -> PlannerResult:
    """
    Use Agno Agent with Gemini to classify the user's intent.
    Returns PlannerResult with intent and optional workflow_name.
    """
    agent = Agent(
        name="BizMind Planner",
        model=get_gemini_model(temperature=0.1, max_tokens=200),
        instructions=PLANNER_SYSTEM_PROMPT,
        output_schema=PlannerResult,
        markdown=False,
    )

    # Build recent history context (last 3 turns for planner)
    context_turns = history[-6:] if len(history) > 6 else history
    context = "\n".join(
        f"{m['role'].upper()}: {m['content']}" for m in context_turns
    )
    prompt = f"Recent conversation:\n{context}\n\nNew message: {message}"

    try:
        agno_images = [AgnoImage(url=img) for img in images] if images else None
        response = await agent.arun(prompt, images=agno_images)
        result: PlannerResult = response.content

        logger.info(
            "Intent classified",
            intent=result.intent,
            confidence=result.confidence,
            workflow_name=result.workflow_name,
        )
        return result

    except Exception as exc:
        logger.warning("Planner classification failed, defaulting to general", error=str(exc))
        return PlannerResult(intent="general", confidence=0.5)
