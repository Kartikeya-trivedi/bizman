"""
BizMind AI — Long-Term Memory
Extracts key user facts via Gemini and persists in Supabase user_memory table.
"""
import json
import re
from datetime import datetime, timezone

from google import genai
from google.genai import types

from backend.core.config import get_settings
from backend.core.logging import get_logger
from backend.core.supabase import get_supabase_admin

logger = get_logger("long_term_memory")

MEMORY_EXTRACTION_PROMPT = """Extract key facts about the user from this conversation history.
Focus on: name, company, role, industry, preferences, past topics, pain points, goals.
Return ONLY a JSON object with string key-value pairs. Max 10 entries.
Example: {"name": "Alice", "company": "Acme Corp", "industry": "retail"}
If nothing meaningful, return: {}
"""


async def load_user_memory(user_id: str) -> str:
    sb = get_supabase_admin()
    try:
        resp = sb.table("user_memory").select("key, value").eq("user_id", user_id).execute()
        entries = resp.data or []
        if not entries:
            return ""
        return "\n".join(f"- {e['key']}: {e['value']}" for e in entries)
    except Exception as exc:
        logger.warning("Failed to load user memory", user_id=user_id, error=str(exc))
        return ""


async def save_user_memory(user_id: str, history: list[dict]) -> None:
    if len(history) < 2:
        return

    settings = get_settings()
    client = genai.Client(api_key=settings.google_api_key)

    history_text = "\n".join(
        f"{m['role'].upper()}: {m['content']}" for m in history[-10:]
    )

    try:
        response = client.models.generate_content(
            model=settings.gemini_model,
            contents=history_text,
            config=types.GenerateContentConfig(
                system_instruction=MEMORY_EXTRACTION_PROMPT,
                temperature=0.0,
                max_output_tokens=300,
            ),
        )
        text = response.text.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
        text = re.sub(r"\s*```$", "", text, flags=re.MULTILINE)

        facts: dict = json.loads(text)
        if not facts:
            return

        sb = get_supabase_admin()
        now = datetime.now(timezone.utc).isoformat()

        for key, value in facts.items():
            if not key or not value:
                continue
            sb.table("user_memory").upsert(
                {"user_id": user_id, "key": str(key), "value": str(value), "updated_at": now},
                on_conflict="user_id,key",
            ).execute()

        logger.info("User memory updated", user_id=user_id, facts_count=len(facts))
    except Exception as exc:
        logger.warning("Memory extraction/save failed", user_id=user_id, error=str(exc))
