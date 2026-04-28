"""
Conversão de .docx para .pdf usando LibreOffice headless.

Por que LibreOffice?
- Preserva 100% do layout do Word (fontes, imagens, tabelas, cabeçalhos)
- Gratuito e open-source
- Roda perfeitamente em Docker/Linux
- Alternativas como docx2pdf requerem Word instalado (só Windows/Mac)

Instalação no servidor/Docker:
    apt-get install -y libreoffice

Uso no código: pdf_bytes = convert_docx_to_pdf(docx_bytes)
"""
import asyncio
import subprocess
import tempfile
from pathlib import Path

from app.config import get_settings


async def convert_docx_to_pdf(docx_bytes: bytes) -> bytes:
    """
    Converte bytes de um .docx para bytes de um .pdf.

    Estratégia:
      1. Salva o .docx em arquivo temporário
      2. Chama LibreOffice headless --convert-to pdf
      3. Lê o PDF gerado e retorna como bytes
      4. Limpa os arquivos temporários

    Tudo é feito em asyncio.to_thread para não bloquear o event loop.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _convert_sync, docx_bytes)


def _convert_sync(docx_bytes: bytes) -> bytes:
    """Versão síncrona da conversão — executada em thread pool."""
    settings = get_settings()

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Salva o docx temporariamente
        docx_path = tmp_path / "proposta.docx"
        docx_path.write_bytes(docx_bytes)

        # Executa LibreOffice headless
        result = subprocess.run(
            [
                settings.LIBREOFFICE_PATH,
                "--headless",
                "--norestore",
                "--nofirststartwizard",
                "--convert-to", "pdf",
                "--outdir", str(tmp_path),
                str(docx_path),
            ],
            capture_output=True,
            text=True,
            timeout=60,  # 60s de timeout — mais que suficiente para qualquer proposta
        )

        if result.returncode != 0:
            raise RuntimeError(
                f"LibreOffice falhou ao converter DOCX para PDF.\n"
                f"stdout: {result.stdout}\n"
                f"stderr: {result.stderr}"
            )

        pdf_path = tmp_path / "proposta.pdf"
        if not pdf_path.exists():
            raise RuntimeError(
                f"LibreOffice não gerou o PDF esperado em {pdf_path}.\n"
                f"stdout: {result.stdout}"
            )

        return pdf_path.read_bytes()
