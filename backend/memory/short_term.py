"""
BizMind AI — Short-Term Memory
In-memory conversation history per session_id.
Stores last N turns (default 10 = 20 messages).
"""
from collections import deque
from threading import Lock

from backend.core.config import get_settings
from backend.core.logging import get_logger

logger = get_logger("short_term_memory")

# Thread-safe in-memory store: session_id → deque of messages
_sessions: dict[str, deque] = {}
_lock = Lock()


def _get_session(session_id: str) -> deque:
    with _lock:
        if session_id not in _sessions:
            settings = get_settings()
            _sessions[session_id] = deque(maxlen=settings.short_term_max_turns * 2)
        return _sessions[session_id]


def get_history(session_id: str) -> list[dict]:
    """Return conversation history for a session as a list of {role, content} dicts."""
    return list(_get_session(session_id))


def add_message(session_id: str, role: str, content: str) -> None:
    """Append a message to the session history."""
    session = _get_session(session_id)
    with _lock:
        session.append({"role": role, "content": content})
    logger.debug("Message added to short-term memory", session_id=session_id, role=role)


def clear_session(session_id: str) -> None:
    """Clear all history for a session."""
    with _lock:
        if session_id in _sessions:
            del _sessions[session_id]
    logger.info("Session cleared", session_id=session_id)


def get_all_sessions() -> list[str]:
    """Return all active session IDs (for debugging)."""
    with _lock:
        return list(_sessions.keys())
