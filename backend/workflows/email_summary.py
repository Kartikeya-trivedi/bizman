"""
BizMind AI — Email Summary Workflow
Summarizes raw email text into structured JSON using Gemini.
"""
import json
import re
import time

from google import genai
from google.genai import types

from backend.core.config import get_settings
from backend.core.errors import retry
from backend.core.logging import get_logger
from backend.models.schemas import EmailSummaryResponse
from backend.workflows._log_helper import log_workflow

logger = get_logger("email_summary")

EMAIL_SUMMARY_PROMPT = """You are an email analyzer for business professionals.
Analyze the provided email and extract the following in JSON format ONLY:
{
  "subject": "inferred or actual email subject",
  "key_points": ["point 1", "point 2", ...],
  "action_items": ["action 1", "action 2", ...],
  "priority": "low|medium|high|urgent"
}

Priority guide:
- urgent: deadlines < 24h, crisis, legal/financial alerts
- high: important decisions, meetings within 48h, client escalations
- medium: regular business matters, follow-ups within a week
- low: newsletters, FYI, informational

Return ONLY the JSON object, no markdown, no extra text.
"""


@retry(max_attempts=3, base_delay=1.0)
async def summarize_email(text: str, user_id: str) -> EmailSummaryResponse:
    start = time.monotonic()
    settings = get_settings()
    client = genai.Client(api_key=settings.google_api_key)

    try:
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=text,
            config=types.GenerateContentConfig(
                system_instruction=EMAIL_SUMMARY_PROMPT,
                temperature=0.2,
                max_output_tokens=512,
            ),
        )
        raw = response.text.strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
        raw = re.sub(r"\s*```$", "", raw, flags=re.MULTILINE)
        data = json.loads(raw)

        result = EmailSummaryResponse(
            subject=data.get("subject", "No subject"),
            key_points=data.get("key_points", []),
            action_items=data.get("action_items", []),
            priority=data.get("priority", "medium"),
        )
        duration_ms = int((time.monotonic() - start) * 1000)
        await log_workflow("email_summary", "success", duration_ms, user_id)
        logger.info("Email summary complete", user_id=user_id, priority=result.priority)
        return result

    except Exception as exc:
        duration_ms = int((time.monotonic() - start) * 1000)
        await log_workflow("email_summary", "failed", duration_ms, user_id)
        logger.error("Email summary failed", error=str(exc))
        raise
