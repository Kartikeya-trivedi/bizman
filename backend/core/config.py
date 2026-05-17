"""
BizMind AI — Application Configuration
Loads all env vars via Pydantic BaseSettings.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_name: str = "BizMind AI"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"

    # Supabase
    supabase_url: str
    supabase_anon_key: str
    supabase_service_key: str  # Service role key for server-side ops

    # Gemini / Google AI
    google_api_key: str
    gemini_model: str = "gemini-2.0-flash"
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimensions: int = 384

    # Redis
    redis_url: str = "redis://localhost:6379"
    redis_cache_ttl: int = 3600  # 1 hour

    # RAG
    rag_chunk_size: int = 600       # tokens
    rag_chunk_overlap: int = 100    # tokens
    rag_top_k: int = 5
    rag_similarity_threshold: float = 0.35

    # Memory
    short_term_max_turns: int = 10

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # Exports
    exports_dir: str = "exports"
    logs_dir: str = "logs"


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
