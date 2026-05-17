"""
BizMind AI — Email Summary Workflow
Summarizes raw email text into structured output using Agno Agent (Gemini).
"""
import time

from agno.agent import Agent

from backend.core.errors import retry
from backend.core.gemini import get_gemini_model
from backend.core.logging import get_logger
from backend.models.schemas import EmailSummaryResponse
from backend.workflows._log_helper import log_workflow

logger = get_logger("email_summary")

EMAIL_SUMMARY_PROMPT = """You are an email analyzer for business professionals.
Analyze the provided email and extract the following:
- subject: inferred or actual email subject
- key_points: list of key points from the email
- action_items: list of action items
- priority: "low", "medium", "high", or "urgent"

Priority guide:
- urgent: deadlines < 24h, crisis, legal/financial alerts
- high: important decisions, meetings within 48h, client escalations
- medium: regular business matters, follow-ups within a week
- low: newsletters, FYI, informational
"""


@retry(max_attempts=3, base_delay=1.0)
async def summarize_email(text: str, user_id: str) -> EmailSummaryResponse:
    start = time.monotonic()

    agent = Agent(
        name="BizMind Email Summarizer",
        model=get_gemini_model(temperature=0.2, max_tokens=512),
        instructions=EMAIL_SUMMARY_PROMPT,
        output_schema=EmailSummaryResponse,
        markdown=False,
    )

    try:
        response = await agent.arun(text)
        result: EmailSummaryResponse = response.content

        duration_ms = int((time.monotonic() - start) * 1000)
        await log_workflow("email_summary", "success", duration_ms, user_id)
        logger.info("Email summary complete", user_id=user_id, priority=result.priority)
        return result

    except Exception as exc:
        duration_ms = int((time.monotonic() - start) * 1000)
        await log_workflow("email_summary", "failed", duration_ms, user_id)
        logger.error("Email summary failed", error=str(exc))
        raise
