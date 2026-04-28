"""
Upload de arquivos para o Supabase Storage.

Estrutura de pastas no bucket:
    proposals/
        {user_id}/
            {numero_proposta}/
                proposta.docx

Retorna a URL publica do DOCX.
"""
from app.config import get_settings
from app.utils.supabase_client import get_supabase


def _sanitize_path(text: str) -> str:
    """Remove caracteres invalidos para paths de storage."""
    return text.replace("/", "-").replace(" ", "_").replace(".", "")


async def upload_proposal_files(
    user_id: str,
    numero_proposta: str,
    docx_bytes: bytes,
    pdf_bytes: bytes,  # ignorado nesta versao
) -> tuple[str, str]:
    """
    Faz upload do .docx no Supabase Storage.
    Retorna (url_docx, url_docx) — ambos apontam para o DOCX.
    """
    settings = get_settings()
    supabase = get_supabase()
    bucket = settings.STORAGE_BUCKET

    # Normaliza o numero da proposta para usar como nome de pasta
    # Ex: "0042/2026" -> "0042-2026"
    safe_number = _sanitize_path(numero_proposta)
    base_path = f"{user_id}/{safe_number}"

    docx_path = f"{base_path}/proposta.docx"

    # Upload DOCX
    supabase.storage.from_(bucket).upload(
        path=docx_path,
        file=docx_bytes,
        file_options={
            "content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "upsert": "true",
        },
    )

    # Gera URL publica
    if settings.STORAGE_PUBLIC:
        url_docx = supabase.storage.from_(bucket).get_public_url(docx_path)
    else:
        url_docx = supabase.storage.from_(bucket).create_signed_url(docx_path, 604800)["signedURL"]

    return url_docx, url_docx
