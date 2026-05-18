"""
BizMind AI — Shared Gemini Model Factory
Returns a configured agno.models.google.Gemini instance.
"""
from agno.models.google import Gemini

from backend.core.config import get_settings


def get_gemini_model(
    temperature: float | None = None,
    max_tokens: int | None = None,
) -> Gemini:
    """
    Create a Gemini model instance configured from application settings.
    Accepts optional temperature and max_tokens overrides.
    """
    settings = get_settings()
    return Gemini(
        id=settings.gemini_model,
        api_key=settings.google_api_key,
        temperature=temperature,
        max_output_tokens=max_tokens,
    )
