"""
Orquestrador principal: gera DOCX, faz upload no Storage e salva no banco.
PDF nao e gerado automaticamente — o usuario baixa o DOCX e converte no Word.
"""
from datetime import date
from decimal import Decimal
from uuid import UUID

from app.models.schemas import PropostaRequest, PropostaResponse, PropostaListItem
from app.services.docx_service import generate_docx
from app.services.storage_service import upload_proposal_files
from app.utils.numbering import generate_proposal_number
from app.utils.supabase_client import get_supabase


async def create_proposal(user_id: str, data: PropostaRequest) -> PropostaResponse:
    """
    Pipeline de geracao de proposta:
    1. Gera numero incremental
    2. Renderiza o .docx via template
    3. Faz upload do DOCX no Supabase Storage
    4. Salva metadados no banco
    5. Retorna resposta com URL do DOCX
    """
    supabase = get_supabase()

    # 1 — Numero da proposta
    numero_proposta = await generate_proposal_number(user_id)

    # 2 — Gera DOCX em memoria
    docx_bytes = generate_docx(data, numero_proposta)

    # 3 — Upload no Storage (sem PDF)
    url_docx, url_pdf = await upload_proposal_files(
        user_id=user_id,
        numero_proposta=numero_proposta,
        docx_bytes=docx_bytes,
        pdf_bytes=b"",  # PDF nao gerado nesta versao
    )

    # 4 — Salva no banco
    valor = data.opcoes_pagamento[0].valor_total if data.opcoes_pagamento else Decimal("0")
    data_proposta = data.data_proposta or date.today()

    record = (
        supabase.table("proposals")
        .insert({
            "user_id": user_id,
            "cliente_nome": data.cliente_condominio,
            "cliente_contato": data.cliente_contato,
            "cliente_email": data.cliente_email,
            "numero_proposta": numero_proposta,
            "data": data_proposta.isoformat(),
            "valor": float(valor),
            "url_docx": url_docx,
            "url_pdf": url_docx,  # aponta para o DOCX enquanto nao ha PDF
        })
        .execute()
    )

    row = record.data[0]

    # 5 — Retorna resposta
    return PropostaResponse(
        id=UUID(row["id"]),
        numero_proposta=row["numero_proposta"],
        cliente_nome=row["cliente_nome"],
        data=date.fromisoformat(row["data"]),
        valor=Decimal(str(row["valor"])),
        url_docx=row["url_docx"],
        url_pdf=row["url_pdf"],
        created_at=row["created_at"],
    )


async def list_proposals(user_id: str, page: int = 1, per_page: int = 20) -> list[PropostaListItem]:
    """Lista as propostas do usuario com paginacao simples."""
    supabase = get_supabase()
    offset = (page - 1) * per_page

    result = (
        supabase.table("proposals")
        .select("id, numero_proposta, cliente_nome, data, valor, url_pdf, created_at")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .range(offset, offset + per_page - 1)
        .execute()
    )

    return [
        PropostaListItem(
            id=UUID(r["id"]),
            numero_proposta=r["numero_proposta"],
            cliente_nome=r["cliente_nome"],
            data=date.fromisoformat(r["data"]),
            valor=Decimal(str(r["valor"])),
            url_pdf=r["url_pdf"],
            created_at=r["created_at"],
        )
        for r in result.data
    ]


async def get_proposal(proposal_id: str, user_id: str) -> dict | None:
    """Retorna uma proposta especifica, garantindo que pertence ao usuario."""
    supabase = get_supabase()

    result = (
        supabase.table("proposals")
        .select("*")
        .eq("id", proposal_id)
        .eq("user_id", user_id)
        .single()
        .execute()
    )

    return result.data
