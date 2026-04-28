"""
Singleton para o cliente Supabase.
Usa service_role key para operações de backend (DB + Storage).
"""
from functools import lru_cache

from supabase import Client, create_client

from app.config import get_settings


@lru_cache
def get_supabase() -> Client:
    """
    Retorna o cliente Supabase com service_role key.
    Singleton — instanciado uma vez por processo.
    """
    settings = get_settings()
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
