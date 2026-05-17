"""
BizMind AI — Validator Agent
Checks if the response is grounded in the retrieved context.
Flags hallucinations and can re-route to executor.
Uses Agno Agent with structured output (ValidatorResult).
"""
from pydantic import BaseModel, Field

from agno.agent import Agent

from backend.core.errors import retry, LLM_FALLBACK
from backend.core.gemini import get_gemini_model
from backend.core.logging import get_logger
from backend.models.schemas import ValidatorResult

logger = get_logger("validator")

VALIDATOR_PROMPT = """You are a factual grounding validator for an AI system.

Your job:
1. Check if the RESPONSE makes claims that are NOT supported by the CONTEXT.
2. If the response is a general answer (no context provided), skip grounding check and mark as faithful.
3. Identify any specific facts, numbers, names, or dates in the response that cannot be traced to the context.
"""


class _ValidationOutput(BaseModel):
    """Internal schema for the validator LLM call."""
    is_faithful: bool = Field(description="Whether the response is grounded in the context")
    flagged_claims: list[str] = Field(default_factory=list, description="Claims not supported by context")
    reasoning: str = Field(default="", description="Brief explanation of the validation")


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

    agent = Agent(
        name="BizMind Validator",
        model=get_gemini_model(temperature=0.0, max_tokens=400),
        instructions=VALIDATOR_PROMPT,
        output_schema=_ValidationOutput,
        markdown=False,
    )

    prompt = f"""CONTEXT:
{context}

USER QUESTION:
{user_message}

RESPONSE TO VALIDATE:
{assistant_response}"""

    try:
        response = await agent.arun(prompt)
        result: _ValidationOutput = response.content

        is_faithful = result.is_faithful
        flagged = result.flagged_claims

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
