"""
Health check endpoint — usado por Docker, load balancers e monitoramento.
Não requer autenticação.
"""
import subprocess

from fastapi import APIRouter

from app.config import get_settings

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Health check do serviço")
async def health_check():
    settings = get_settings()

    # Verifica se LibreOffice está disponível
    try:
        result = subprocess.run(
            [settings.LIBREOFFICE_PATH, "--version"],
            capture_output=True, text=True, timeout=5
        )
        lo_version = result.stdout.strip() if result.returncode == 0 else "unavailable"
    except (FileNotFoundError, subprocess.TimeoutExpired):
        lo_version = "unavailable"

    return {
        "status": "ok",
        "service": settings.SERVICE_NAME,
        "version": settings.SERVICE_VERSION,
        "libreoffice": lo_version,
    }
