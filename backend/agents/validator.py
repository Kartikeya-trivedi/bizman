"""
BizMind AI — Validator Agent
Checks if the response is grounded in the retrieved context.
Flags hallucinations and can re-route to executor.
"""
import json
import re

from google import genai
from google.genai import types

from backend.core.config import get_settings
from backend.core.errors import retry, LLM_FALLBACK
from backend.core.logging import get_logger
from backend.models.schemas import ValidatorResult

logger = get_logger("validator")

VALIDATOR_PROMPT = """You are a factual grounding validator for an AI system.

Your job:
1. Check if the RESPONSE makes claims that are NOT supported by the CONTEXT.
2. If the response is a general answer (no context provided), skip grounding check and mark as faithful.
3. Identify any specific facts, numbers, names, or dates in the response that cannot be traced to the context.

Respond ONLY with valid JSON:
{
  "is_faithful": true|false,
  "flagged_claims": ["claim that is not in context", ...],
  "reasoning": "brief explanation"
}
"""


@retry(max_attempts=2, base_delay=1.0)
async def validate_response(
    user_message: str,
    assistant_response: str,
    context: str = "",
) -> ValidatorResult:
    """
    Validate if the response is grounded in the retrieved context.
    If no context (general intent), always marks as faithful.
    """
    if not context.strip():
        return ValidatorResult(
            is_faithful=True,
            flagged_claims=[],
            final_answer=assistant_response,
        )

    settings = get_settings()
    client = genai.Client(api_key=settings.google_api_key)

    prompt = f"""CONTEXT:
{context}

USER QUESTION:
{user_message}

RESPONSE TO VALIDATE:
{assistant_response}"""

    try:
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=VALIDATOR_PROMPT,
                temperature=0.0,
                max_output_tokens=400,
            ),
        )
        text = response.text.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
        text = re.sub(r"\s*```$", "", text, flags=re.MULTILINE)

        data = json.loads(text)
        is_faithful = bool(data.get("is_faithful", True))
        flagged = data.get("flagged_claims", [])

        if not is_faithful and flagged:
            warning = (
                "\n\n⚠️ *Note: Some parts of this answer could not be fully verified "
                "against uploaded documents. Please double-check critical information.*"
            )
            final_answer = assistant_response + warning
        else:
            final_answer = assistant_response

        logger.info("Validation complete", is_faithful=is_faithful, flagged_count=len(flagged))
        return ValidatorResult(is_faithful=is_faithful, flagged_claims=flagged, final_answer=final_answer)

    except Exception as exc:
        logger.warning("Validator failed, passing through", error=str(exc))
        return ValidatorResult(is_faithful=True, flagged_claims=[], final_answer=assistant_response)
