"""
Testes do microserviço de propostas.

Para rodar:
    pip install pytest pytest-asyncio httpx
    pytest tests/ -v

Os testes de integração requerem um .env válido.
Os testes unitários (docx_service) são isolados.
"""
import os
from decimal import Decimal
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.schemas import ItemServico, OpcaoPagamento, PropostaRequest
from app.services.docx_service import generate_docx, _format_currency, _format_date_pt
from datetime import date


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def sample_request() -> PropostaRequest:
    return PropostaRequest(
        cliente_tratamento="Sr.",
        cliente_condominio="Condomínio do Edifício Solar dos Ipês",
        cliente_contato="Carlos Mendes",
        cliente_endereco="Av. Atlântica, 500. Copacabana. Rio de Janeiro – RJ.",
        cliente_telefone="(21) 9.9999-9999",
        cliente_email="sindico@solar.com.br",
        cliente_cnpj="12.345.678/0001-99",
        cliente_cargo="Síndico",
        descricao_servico="Modernização e reforma do agrupamento de PC com aumento de carga",
        data_proposta=date(2026, 4, 27),
        itens=[
            ItemServico(
                descricao="Instalação de quadro CPG",
                unidade="un",
                quantidade=Decimal("1"),
                valor_unitario=Decimal("15000.00"),
            )
        ],
        opcoes_pagamento=[
            OpcaoPagamento(
                descricao="Pagamento por Medição (Boleto Bancário)",
                n_parcelas=1,
                valor_total=Decimal("322000.00"),
                valor_unidade_excedente="(R$2.250,00) VALOR ACIMA DE 30 UNIDADES",
            ),
            OpcaoPagamento(
                descricao="Parcelado em 12x",
                n_parcelas=12,
                valor_total=Decimal("350400.00"),
                valor_unidade_excedente="(R$2.550,00) A CIMA DE 30 UNIDADES",
            ),
            OpcaoPagamento(
                descricao="Parcelado em 24x",
                n_parcelas=24,
                valor_total=Decimal("422400.00"),
                valor_unidade_excedente="(R$3.250,00) A CIMA DE 30 UNIDADES",
            ),
        ],
        validade_proposta="20 (vinte) dias",
        prazo_conclusao="90 (noventa) dias úteis",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Testes unitários
# ─────────────────────────────────────────────────────────────────────────────

class TestFormatters:
    def test_format_currency(self):
        assert _format_currency(Decimal("322000.00")) == "R$322.000,00"
        assert _format_currency(Decimal("1500.50")) == "R$1.500,50"
        assert _format_currency(Decimal("100")) == "R$100,00"

    def test_format_date_pt(self):
        d = date(2026, 3, 2)
        result = _format_date_pt(d)
        assert "março" in result
        assert "2026" in result
        assert "segunda" in result

    def test_format_date_pt_monday(self):
        d = date(2026, 4, 27)
        result = _format_date_pt(d)
        assert "abril" in result
        assert "27" in result


class TestDocxGeneration:
    def test_generate_docx_returns_bytes(self, sample_request):
        """Verifica que a geração retorna bytes de um arquivo DOCX válido."""
        result = generate_docx(sample_request, "0001/2026")

        # Deve retornar bytes
        assert isinstance(result, bytes)
        assert len(result) > 0

        # DOCX é um ZIP — começa com PK
        assert result[:2] == b"PK"

    def test_generate_docx_numero_proposta(self, sample_request):
        """Número da proposta deve estar no documento gerado."""
        import zipfile
        import io

        result = generate_docx(sample_request, "0099/2026")

        with zipfile.ZipFile(io.BytesIO(result)) as z:
            with z.open("word/document.xml") as f:
                xml_content = f.read().decode("utf-8")

        assert "0099/2026" in xml_content

    def test_generate_docx_cliente_nome(self, sample_request):
        """Nome do cliente deve estar no documento gerado."""
        import zipfile
        import io

        result = generate_docx(sample_request, "0001/2026")

        with zipfile.ZipFile(io.BytesIO(result)) as z:
            with z.open("word/document.xml") as f:
                xml_content = f.read().decode("utf-8")

        assert "Solar dos Ipês" in xml_content

    def test_item_valor_total(self):
        item = ItemServico(
            descricao="Serviço X",
            unidade="un",
            quantidade=Decimal("3"),
            valor_unitario=Decimal("1000.00"),
        )
        assert item.valor_total == Decimal("3000.00")

    def test_opcao_valor_parcela(self):
        opcao = OpcaoPagamento(
            descricao="12x",
            n_parcelas=12,
            valor_total=Decimal("350400.00"),
        )
        assert opcao.valor_parcela == Decimal("29200.00")


class TestPropostaRequestValidation:
    def test_requires_opcoes_pagamento(self):
        with pytest.raises(Exception):
            PropostaRequest(
                cliente_condominio="Test",
                cliente_contato="Test",
                cliente_endereco="Test",
                cliente_telefone="Test",
                cliente_email="test@test.com",
                descricao_servico="Test",
                opcoes_pagamento=[],  # Deve falhar — min_length=1
            )

    def test_default_data_proposta_is_today(self):
        from datetime import date
        req = PropostaRequest(
            cliente_condominio="Test",
            cliente_contato="Test",
            cliente_endereco="Test",
            cliente_telefone="Test",
            cliente_email="test@test.com",
            descricao_servico="Test",
            opcoes_pagamento=[
                OpcaoPagamento(
                    descricao="Teste",
                    n_parcelas=1,
                    valor_total=Decimal("1000"),
                )
            ],
        )
        assert req.data_proposta == date.today()
