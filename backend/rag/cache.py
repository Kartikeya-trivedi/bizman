"""
BizMind AI — Redis Semantic Cache
MD5 hash → cached response lookup with 1-hour TTL.
Gracefully degrades if Redis is unavailable.
"""
import hashlib
import json
from typing import Any

from backend.core.config import get_settings
from backend.core.logging import get_logger

logger = get_logger("cache")

_redis_client = None


def _get_redis():
    """Lazy Redis connection with graceful fallback."""
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    try:
        import redis
        settings = get_settings()
        client = redis.Redis.from_url(
            settings.redis_url,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        client.ping()
        _redis_client = client
        logger.info("Redis cache connected", url=settings.redis_url)
        return client
    except Exception as exc:
        logger.warning("Redis unavailable, cache disabled", error=str(exc))
        return None


def _make_key(query: str, user_id: str) -> str:
    """Create a deterministic cache key from query + user_id."""
    raw = f"{user_id}::{query.strip().lower()}"
    return f"bizmind:rag:{hashlib.md5(raw.encode()).hexdigest()}"


async def cache_get(query: str, user_id: str) -> dict | None:
    """Return cached RAG result or None if miss/unavailable."""
    client = _get_redis()
    if client is None:
        return None
    try:
        key = _make_key(query, user_id)
        raw = client.get(key)
        if raw:
            data = json.loads(raw)
            logger.info("Cache HIT", key=key)
            return data
        logger.debug("Cache MISS", key=key)
        return None
    except Exception as exc:
        logger.warning("Cache GET error", error=str(exc))
        return None


async def cache_set(query: str, user_id: str, result: dict) -> None:
    """Store a RAG result in cache with TTL."""
    client = _get_redis()
    if client is None:
        return
    try:
        settings = get_settings()
        key = _make_key(query, user_id)
        client.setex(key, settings.redis_cache_ttl, json.dumps(result))
        logger.info("Cache SET", key=key, ttl=settings.redis_cache_ttl)
    except Exception as exc:
        logger.warning("Cache SET error", error=str(exc))


async def cache_invalidate_user(user_id: str) -> int:
    """Invalidate all cached entries for a user (called on doc delete)."""
    client = _get_redis()
    if client is None:
        return 0
    try:
        pattern = f"bizmind:rag:*"
        keys = client.keys(pattern)
        # We can't filter by user_id from key alone (hashed), so full pattern delete
        if keys:
            client.delete(*keys)
        return len(keys)
    except Exception as exc:
        logger.warning("Cache invalidation error", error=str(exc))
        return 0
