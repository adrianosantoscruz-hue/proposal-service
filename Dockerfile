# ─────────────────────────────────────────────────────────────────────────────
# Stage 1: Builder — instala dependências Python
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

# Instala dependências de compilação (necessário para algumas libs Python)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copia e instala dependências Python em modo "wheel" para reutilizar no stage final
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt


# ─────────────────────────────────────────────────────────────────────────────
# Stage 2: Final — imagem enxuta de produção
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.12-slim

# Variáveis de ambiente do Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Caminho do LibreOffice no container
    LIBREOFFICE_PATH=/usr/bin/libreoffice

WORKDIR /service

# ── LibreOffice headless (necessário para conversão DOCX → PDF) ───────────────
# libreoffice-writer e fonts são suficientes; libreoffice-common vem junto
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice-writer \
    libreoffice-java-common \
    fonts-liberation \
    fonts-dejavu \
    # Fontes usadas no template Asspontec (Bahnschrift não existe no Linux,
    # Liberation Sans é o fallback mais próximo e mantém o layout)
    fontconfig \
    && fc-cache -f \
    && rm -rf /var/lib/apt/lists/*

# ── Instala wheels do stage builder ─────────────────────────────────────────
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir --no-index --find-links=/wheels /wheels/*.whl \
    && rm -rf /wheels

# ── Copia o código da aplicação ──────────────────────────────────────────────
COPY app/ ./app/
COPY templates/ ./templates/

# ── Usuário não-root por segurança ──────────────────────────────────────────
RUN useradd -m -u 1001 appuser && chown -R appuser:appuser /service
USER appuser

# ── Porta exposta ────────────────────────────────────────────────────────────
EXPOSE 8000

# ── Healthcheck ──────────────────────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# ── Comando de inicialização ──────────────────────────────────────────────────
# workers=2 é seguro para geração de documentos (operação CPU-bound em thread pool)
# Aumente para 4 em VPS com 4+ cores
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "2", \
     "--log-level", "info"]
