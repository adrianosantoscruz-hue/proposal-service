from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, Field, field_validator


class ItemServico(BaseModel):
    descricao: str
    unidade: str = "un"
    quantidade: Decimal = Field(..., gt=0)
    valor_unitario: Decimal = Field(..., ge=0)

    @property
    def valor_total(self) -> Decimal:
        return self.quantidade * self.valor_unitario


class OpcaoPagamento(BaseModel):
    descricao: str
    n_parcelas: int = Field(default=1, ge=1)
    valor_total: Decimal = Field(..., ge=0)
    valor_unidade_excedente: Optional[str] = None
    cronograma_pagamento: Optional[list] = None

    @property
    def valor_parcela(self) -> Decimal:
        if self.n_parcelas <= 1:
            return self.valor_total
        return (self.valor_total / self.n_parcelas).quantize(Decimal("0.01"))


class PropostaRequest(BaseModel):
    cliente_tratamento: str = "Sr."
    cliente_condominio: str
    cliente_contato: str
    cliente_endereco: str
    cliente_telefone: str
    cliente_email: str
    cliente_cnpj: str = ""
    cliente_cargo: str = "Sindico(a)"
    descricao_servico: str
    data_proposta: date = Field(default_factory=date.today)
    itens: list[ItemServico] = []
    opcoes_pagamento: list[OpcaoPagamento] = Field(..., min_length=1, max_length=3)
    validade_proposta: str = "20 (vinte) dias"
    prazo_conclusao: str = "90 (noventa) dias uteis"

    @field_validator("data_proposta", mode="before")
    @classmethod
    def parse_date(cls, v):
        if isinstance(v, str):
            return date.fromisoformat(v)
        return v


class PropostaResponse(BaseModel):
    id: UUID
    numero_proposta: str
    cliente_nome: str
    data: date
    valor: Decimal
    url_docx: str
    url_pdf: str
    created_at: datetime


class PropostaListItem(BaseModel):
    id: UUID
    numero_proposta: str
    cliente_nome: str
    data: date
    valor: Decimal
    url_pdf: str
    created_at: datetime


class ErrorResponse(BaseModel):
    detail: str
