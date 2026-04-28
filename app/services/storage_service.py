"""
Upload de arquivos para o Supabase Storage.

Estrutura de pastas no bucket:
    proposals/
        {user_id}/
            {numero_proposta}/
                proposta.docx
                proposta.pdf

Retorna a URL pública (ou signed URL se o bucket for privado).
"""
from app.config import get_settings
from app.utils.supabase_client import get_supabase


def _sanitize_path(text: str) -> str:
    """Remove caracteres inválidos para paths de storage."""
    return text.replace("/", "-").replace(" ", "_").replace(".", "")


async def upload_proposal_files(
    user_id: str,
    numero_proposta: str,
    docx_bytes: bytes,
    pdf_bytes: bytes,
) -> tuple[str, str]:
    """
    Faz upload do .docx e .pdf no Supabase Storage.

    Retorna (url_docx, url_pdf).
    """
    settings = get_settings()
    supabase = get_supabase()
    bucket = settings.STORAGE_BUCKET

    # Normaliza o número da proposta para usar como nome de pasta
    # Ex: "0042/2026" → "0042-2026"
    safe_number = _sanitize_path(numero_proposta)
    base_path = f"{user_id}/{safe_number}"

    docx_path = f"{base_path}/proposta.docx"
    pdf_path = f"{base_path}/proposta.pdf"

    # Upload DOCX
    supabase.storage.from_(bucket).upload(
        path=docx_path,
        file=docx_bytes,
        file_options={
            "content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "upsert": "true",
        },
    )

    # Upload PDF
    supabase.storage.from_(bucket).upload(
        path=pdf_path,
        file=pdf_bytes,
        file_options={
            "content-type": "application/pdf",
            "upsert": "true",
        },
    )

    # Gera URLs
    if settings.STORAGE_PUBLIC:
        url_docx = supabase.storage.from_(bucket).get_public_url(docx_path)
        url_pdf = supabase.storage.from_(bucket).get_public_url(pdf_path)
    else:
        # Signed URL com validade de 7 dias (ajuste conforme necessário)
        url_docx = supabase.storage.from_(bucket).create_signed_url(docx_path, 604800)["signedURL"]
        url_pdf = supabase.storage.from_(bucket).create_signed_url(pdf_path, 604800)["signedURL"]

    return url_docx, url_pdf
