"""
Configurações do microserviço via variáveis de ambiente.
Carregadas do arquivo .env em desenvolvimento.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # ── Supabase ──────────────────────────────────────────────────────────────
    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str          # service_role key — nunca expor no frontend
    SUPABASE_ANON_KEY: str                  # anon key — para verificar JWT dos usuários
    SUPABASE_JWT_SECRET: str = ""           # JWT secret legado HS256 (opcional — usado como fallback)

    # ── Storage ───────────────────────────────────────────────────────────────
    STORAGE_BUCKET: str = "proposals"       # Nome do bucket no Supabase Storage
    STORAGE_PUBLIC: bool = True             # Se o bucket é público (True = URLs diretas)

    # ── Serviço ───────────────────────────────────────────────────────────────
    SERVICE_NAME: str = "proposal-service"
    SERVICE_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # ── LibreOffice ───────────────────────────────────────────────────────────
    LIBREOFFICE_PATH: str = "libreoffice"   # ou /usr/bin/libreoffice no Docker

    # ── CORS ──────────────────────────────────────────────────────────────────
    # Lista de origens separadas por vírgula: "https://app.com,https://staging.app.com"
    CORS_ORIGINS: str = "*"

    @property
    def cors_origins_list(self) -> list[str]:
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return [o.strip() for o in self.CORS_ORIGINS.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()