"""
BizMind AI — Supabase Client Singleton
Provides both anon (user-facing) and service role (server-side) clients.
"""
from functools import lru_cache

from supabase import Client, create_client

from backend.core.config import get_settings


@lru_cache
def get_supabase() -> Client:
    """Supabase client with anon key (for user-authenticated ops)."""
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_anon_key)


@lru_cache
def get_supabase_admin() -> Client:
    """Supabase client with service role key (bypasses RLS for server ops)."""
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_service_key)
