"""
Conversao PDF — versao sem LibreOffice.

Nesta versao o servico retorna apenas o DOCX.
Para gerar o PDF: abra o .docx no Word e use Arquivo > Salvar como > PDF.
"""


async def convert_docx_to_pdf(docx_bytes: bytes) -> bytes:
    """
    Stub: retorna bytes vazios — PDF nao gerado nesta versao.
    O servico salva apenas o DOCX no Storage.
    """
    return b""
