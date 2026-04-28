"""
Entrypoint do microserviço de propostas Asspontec.

Para iniciar em desenvolvimento:
    uvicorn app.main:app --reload --port 8000

Para iniciar em produção (via Docker):
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
"""
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, proposals
from app.config import get_settings

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── App ───────────────────────────────────────────────────────────────────────
settings = get_settings()

app = FastAPI(
    title="Asspontec — Proposal Service",
    description=(
        "Microserviço de geração automática de propostas técnicas de orçamento.\n\n"
        "**Autenticação**: todos os endpoints de proposta requerem o JWT do Supabase "
        "no header `Authorization: Bearer <token>`."
    ),
    version=settings.SERVICE_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Rotas ─────────────────────────────────────────────────────────────────────
app.include_router(health.router)
app.include_router(proposals.router)


@app.on_event("startup")
async def startup_event():
    logger.info(
        "🚀 %s v%s iniciado | debug=%s",
        settings.SERVICE_NAME,
        settings.SERVICE_VERSION,
        settings.DEBUG,
    )
