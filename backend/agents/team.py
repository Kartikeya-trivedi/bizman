"""
BizMind AI — Agent Team Orchestrator
Wires Planner → Executor → Validator in sequence.
This is the main entry point called by the chat API.
"""
from dataclasses import dataclass

from backend.agents.planner import classify_intent
from backend.agents.executor import execute
from backend.agents.validator import validate_response
from backend.core.errors import LLM_FALLBACK
from backend.core.logging import get_logger
from backend.core.tracing import log_trace

logger = get_logger("agent_team")


@dataclass
class TeamResult:
    answer: str
    intent: str
    sources: list[str]
    similarity_scores: list[float]
    hallucination_flagged: bool


async def run_agent_team(
    message: str,
    images: list[str],
    history: list[dict],
    user_memory: str,
    user_id: str,
    conversation_id: str,
) -> TeamResult:
    """
    Orchestrate the Planner → Executor → Validator pipeline.

    1. Planner: classify intent
    2. Executor: execute the task
    3. Validator: check grounding (for RAG intents)
    Returns a structured TeamResult.
    """
    # ── Step 1: Plan ──────────────────────────────────────────────────────────
    try:
        plan = await classify_intent(message, history, images)
    except Exception as exc:
        logger.error("Planner failed", error=str(exc))
        return TeamResult(
            answer=LLM_FALLBACK,
            intent="general",
            sources=[],
            similarity_scores=[],
            hallucination_flagged=False,
        )

    # ── Step 2: Execute ───────────────────────────────────────────────────────
    try:
        exec_result = await execute(
            message=message,
            planner_result=plan,
            history=history,
            user_memory=user_memory,
            user_id=user_id,
            conversation_id=conversation_id,
            images=images,
        )
    except Exception as exc:
        logger.error("Executor failed", error=str(exc), intent=plan.intent)
        return TeamResult(
            answer=LLM_FALLBACK,
            intent=plan.intent,
            sources=[],
            similarity_scores=[],
            hallucination_flagged=False,
        )

    answer = exec_result.get("answer", LLM_FALLBACK)
    sources = exec_result.get("sources", [])
    similarity_scores = exec_result.get("similarity_scores", [])
    rag_context = exec_result.get("rag_context", "")

    # ── Step 3: Validate (only for RAG responses) ─────────────────────────────
    hallucination_flagged = False
    try:
        validation = await validate_response(
            user_message=message,
            assistant_response=answer,
            context=rag_context,
        )
        answer = validation.final_answer
        hallucination_flagged = not validation.is_faithful
        if hallucination_flagged:
            logger.warning(
                "Hallucination flagged",
                claims=validation.flagged_claims,
                user_id=user_id,
            )
    except Exception as exc:
        logger.warning("Validator failed, using raw answer", error=str(exc))

    logger.info(
        "Agent team complete",
        intent=plan.intent,
        sources_count=len(sources),
        hallucination_flagged=hallucination_flagged,
    )

    log_trace(
        user_id=user_id,
        conversation_id=conversation_id,
        user_message=message,
        intent=plan.intent,
        planner_confidence=plan.confidence,
        executor_sources=sources,
        validator_is_faithful=not hallucination_flagged,
        validator_flagged_claims=[],
        final_answer=answer,
    )

    return TeamResult(
        answer=answer,
        intent=plan.intent,
        sources=sources,
        similarity_scores=similarity_scores,
        hallucination_flagged=hallucination_flagged,
    )


async def run_agent_team_stream(
    message: str,
    images: list[str],
    history: list[dict],
    user_memory: str,
    user_id: str,
    conversation_id: str,
):
    """
    Orchestrate the team but yield chunks for the answer.
    """
    try:
        plan = await classify_intent(message, history, images)
    except Exception as exc:
        logger.error("Planner failed", error=str(exc))
        yield {"type": "done", "result": TeamResult(
            answer=LLM_FALLBACK, intent="general", sources=[], similarity_scores=[], hallucination_flagged=False
        )}
        return

    try:
        # We pass stream=True to executor
        exec_stream = await execute(
            message=message,
            planner_result=plan,
            history=history,
            user_memory=user_memory,
            user_id=user_id,
            conversation_id=conversation_id,
            images=images,
            stream=True,
        )
    except Exception as exc:
        logger.error("Executor failed", error=str(exc), intent=plan.intent)
        yield {"type": "done", "result": TeamResult(
            answer=LLM_FALLBACK, intent=plan.intent, sources=[], similarity_scores=[], hallucination_flagged=False
        )}
        return

    full_answer = ""
    # If the executor returned a generator, we yield chunks
    import types
    if isinstance(exec_stream, types.AsyncGeneratorType):
        async for chunk in exec_stream:
            if chunk["type"] == "chunk":
                full_answer += chunk["content"]
                yield chunk
            elif chunk["type"] == "done":
                # Finalize
                answer = chunk["result"].get("answer", LLM_FALLBACK)
                sources = chunk["result"].get("sources", [])
                similarity_scores = chunk["result"].get("similarity_scores", [])
                rag_context = chunk["result"].get("rag_context", "")

                hallucination_flagged = False
                if plan.intent == "rag":
                    try:
                        validation = await validate_response(message, answer, rag_context)
                        answer = validation.final_answer
                        hallucination_flagged = not validation.is_faithful
                    except Exception as exc:
                        pass
                
                log_trace(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    user_message=message,
                    intent=plan.intent,
                    planner_confidence=plan.confidence,
                    executor_sources=sources,
                    validator_is_faithful=not hallucination_flagged,
                    validator_flagged_claims=[],
                    final_answer=answer,
                )
                
                yield {"type": "done", "result": TeamResult(
                    answer=answer,
                    intent=plan.intent,
                    sources=sources,
                    similarity_scores=similarity_scores,
                    hallucination_flagged=hallucination_flagged,
                )}
    else:
        # Not a generator (e.g. lead_capture or workflow or rag wasn't streaming)
        answer = exec_stream.get("answer", LLM_FALLBACK)
        # Yield the whole chunk
        yield {"type": "chunk", "content": answer}
        
        sources = exec_stream.get("sources", [])
        similarity_scores = exec_stream.get("similarity_scores", [])
        rag_context = exec_stream.get("rag_context", "")

        hallucination_flagged = False
        if plan.intent == "rag":
            try:
                validation = await validate_response(message, answer, rag_context)
                answer = validation.final_answer
                hallucination_flagged = not validation.is_faithful
            except Exception as exc:
                pass

        log_trace(
            user_id=user_id,
            conversation_id=conversation_id,
            user_message=message,
            intent=plan.intent,
            planner_confidence=plan.confidence,
            executor_sources=sources,
            validator_is_faithful=not hallucination_flagged,
            validator_flagged_claims=[],
            final_answer=answer,
        )

        yield {"type": "done", "result": TeamResult(
            answer=answer,
            intent=plan.intent,
            sources=sources,
            similarity_scores=similarity_scores,
            hallucination_flagged=hallucination_flagged,
        )}
