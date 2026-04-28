"""
Geração de número de proposta no formato 0001/2026.
Incremental por ano — baseado na contagem de registros no banco.
"""
from datetime import date

from app.utils.supabase_client import get_supabase


async def generate_proposal_number(user_id: str) -> str:
    """
    Gera o próximo número de proposta no formato NNNN/YYYY.

    A numeração é global (não por usuário) e reinicia a cada ano.
    Usa uma query COUNT para calcular o próximo número de forma segura.
    """
    year = date.today().year
    supabase = get_supabase()

    # Conta quantas propostas já foram criadas neste ano
    result = (
        supabase.table("proposals")
        .select("id", count="exact")
        .like("numero_proposta", f"%/{year}")
        .execute()
    )

    count = result.count if result.count is not None else 0
    next_number = count + 1

    return f"{next_number:04d}/{year}"
