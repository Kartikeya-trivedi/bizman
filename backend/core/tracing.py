"""
BizMind AI — Agent Tracing
Logs and retrieves step-by-step traces of agent workflows.
"""
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

from backend.core.config import get_settings

def log_trace(
    user_id: str,
    conversation_id: str,
    user_message: str,
    intent: str,
    planner_confidence: float,
    executor_sources: list[str],
    validator_is_faithful: bool,
    validator_flagged_claims: list[str],
    final_answer: str,
):
    settings = get_settings()
    trace_file = Path(settings.logs_dir) / "agent_traces.jsonl"
    
    trace_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user_id": user_id,
        "conversation_id": conversation_id,
        "message": user_message,
        "steps": [
            {
                "agent": "Planner",
                "action": "Classify Intent",
                "output": {"intent": intent, "confidence": planner_confidence}
            },
            {
                "agent": "Executor",
                "action": "Run Pipeline",
                "output": {"sources_used": len(executor_sources), "sources": executor_sources}
            },
            {
                "agent": "Validator",
                "action": "Check Factual Grounding",
                "output": {
                    "is_faithful": validator_is_faithful,
                    "flagged_claims": validator_flagged_claims
                }
            }
        ],
        "final_answer": final_answer,
    }
    
    try:
        with open(trace_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(trace_data) + "\n")
    except Exception as e:
        from backend.core.logging import get_logger
        get_logger("agent_traces").error("Failed to write trace", error=str(e))

def get_traces(limit: int = 50) -> list[dict[str, Any]]:
    settings = get_settings()
    trace_file = Path(settings.logs_dir) / "agent_traces.jsonl"
    
    if not trace_file.exists():
        return []
        
    traces = []
    try:
        with open(trace_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    traces.append(json.loads(line))
    except Exception:
        pass
        
    # Return newest first
    return sorted(traces, key=lambda x: x["timestamp"], reverse=True)[:limit]
