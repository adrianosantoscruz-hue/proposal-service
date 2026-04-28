"""
Rotas da API de propostas.

Endpoints:
  POST /generate-proposal   → Gera DOCX + PDF, salva no Storage, retorna URLs
  GET  /proposals           → Lista propostas do usuário (paginado)
  GET  /proposals/{id}      → Detalhe de uma proposta
"""
import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status

from app.api.deps import CurrentUser
from app.models.schemas import (
    ErrorResponse,
    PropostaListItem,
    PropostaRequest,
    PropostaResponse,
)
from app.services.proposal_service import (
    create_proposal,
    get_proposal,
    list_proposals,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Proposals"])


@router.post(
    "/generate-proposal",
    response_model=PropostaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Gera uma nova proposta técnica de orçamento",
    responses={
        400: {"model": ErrorResponse, "description": "Dados inválidos"},
        401: {"model": ErrorResponse, "description": "Token JWT inválido"},
        500: {"model": ErrorResponse, "description": "Erro interno"},
    },
)
async def generate_proposal(
    body: PropostaRequest,
    user: CurrentUser,
):
    """
    Recebe os dados da proposta, gera `.docx` e `.pdf`,
    faz upload no Supabase Storage e salva o registro no banco.

    **Requer**: `Authorization: Bearer <supabase_jwt>` no header.
    """
    logger.info(
        "Gerando proposta para user_id=%s, cliente=%s",
        user.user_id,
        body.cliente_condominio,
    )

    try:
        result = await create_proposal(user_id=user.user_id, data=body)
        logger.info(
            "Proposta %s gerada com sucesso para user_id=%s",
            result.numero_proposta,
            user.user_id,
        )
        return result

    except FileNotFoundError as e:
        logger.error("Template não encontrado: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Template Word não encontrado no servidor: {e}",
        )
    except RuntimeError as e:
        logger.error("Erro na geração/conversão: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    except Exception as e:
        logger.exception("Erro inesperado ao gerar proposta")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao gerar proposta. Verifique os logs.",
        )


@router.get(
    "/proposals",
    response_model=list[PropostaListItem],
    summary="Lista as propostas do usuário autenticado",
)
async def list_user_proposals(
    user: CurrentUser,
    page: int = Query(default=1, ge=1, description="Página"),
    per_page: int = Query(default=20, ge=1, le=100, description="Itens por página"),
):
    """Retorna as propostas criadas pelo usuário, ordenadas por data decrescente."""
    return await list_proposals(user_id=user.user_id, page=page, per_page=per_page)


@router.get(
    "/proposals/{proposal_id}",
    summary="Detalhe de uma proposta específica",
    responses={
        404: {"model": ErrorResponse, "description": "Proposta não encontrada"},
    },
)
async def get_proposal_detail(
    proposal_id: UUID,
    user: CurrentUser,
):
    """
    Retorna todos os campos de uma proposta.
    Garante que a proposta pertence ao usuário autenticado.
    """
    proposal = await get_proposal(
        proposal_id=str(proposal_id),
        user_id=user.user_id,
    )
    if not proposal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proposta não encontrada.",
        )
    return proposal
