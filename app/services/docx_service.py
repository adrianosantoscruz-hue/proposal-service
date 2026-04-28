"""Geracao do arquivo .docx a partir do template Asspontec usando docxtpl."""
import io
from datetime import date
from decimal import Decimal
from pathlib import Path

from babel.dates import format_date
from docxtpl import DocxTemplate

from app.models.schemas import PropostaRequest

TEMPLATE_PATH = Path(__file__).parent.parent.parent / "templates" / "proposta_template.docx"


def _format_currency(value: Decimal) -> str:
    """Formata Decimal como moeda brasileira: R$322.000,00"""
    v = float(value)
    formatted = f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R${formatted}"


def _format_date_pt(d: date) -> str:
    """Formata date como 'Rio de Janeiro, segunda-feira, 2 de marco de 2026.'"""
    weekday = format_date(d, format="EEEE", locale="pt_BR")
    month = format_date(d, format="MMMM", locale="pt_BR")
    return f"Rio de Janeiro, {weekday}, {d.day} de {month} de {d.year}."


def generate_docx(data: PropostaRequest, numero_proposta: str) -> bytes:
    """
    Preenche o template Word com os dados da proposta.
    Retorna os bytes do .docx gerado em memoria.
    """
    if not TEMPLATE_PATH.exists():
        raise FileNotFoundError(f"Template nao encontrado: {TEMPLATE_PATH}")

    tpl = DocxTemplate(str(TEMPLATE_PATH))

    data_proposta = data.data_proposta
    data_cidade = _format_date_pt(data_proposta)

    # Calculo de valores das opcoes de pagamento
    opcoes = []
    for i, op in enumerate(data.opcoes_pagamento, start=1):
        valor_total_fmt = _format_currency(op.valor_total)
        if op.n_parcelas > 1:
            valor_parcela_fmt = _format_currency(op.valor_parcela)
        else:
            valor_parcela_fmt = valor_total_fmt

        opcoes.append({
            "numero": i,
            "descricao": op.descricao,
            "n_parcelas": op.n_parcelas,
            "valor_total_fmt": valor_total_fmt,
            "valor_parcela_fmt": valor_parcela_fmt,
            "valor_unidade_excedente": op.valor_unidade_excedente or "",
            "cronograma_pagamento": op.cronograma_pagamento or [],
        })

    # Itens formatados
    itens_fmt = []
    total_itens = Decimal("0")
    for item in data.itens:
        vt = item.valor_total
        total_itens += vt
        itens_fmt.append({
            "descricao": item.descricao,
            "unidade": item.unidade,
            "quantidade": str(item.quantidade),
            "valor_unitario": _format_currency(item.valor_unitario),
            "valor_total": _format_currency(vt),
        })

    context = {
        # Cabecalho
        "data_cidade": data_cidade,
        "numero_proposta": numero_proposta,
        # Cliente
        "cliente_tratamento": data.cliente_tratamento,
        "cliente_condominio": data.cliente_condominio,
        "cliente_contato": data.cliente_contato,
        "cliente_endereco": data.cliente_endereco,
        "cliente_telefone": data.cliente_telefone,
        "cliente_email": data.cliente_email,
        "cliente_cnpj": data.cliente_cnpj or "-",
        "cliente_cargo": data.cliente_cargo,
        # Servico
        "descricao_servico": data.descricao_servico,
        # Opcoes de pagamento (placeholders individuais no template)
        "valor_total_opcao1": opcoes[0]["valor_total_fmt"] if len(opcoes) > 0 else "",
        "valor_unidade_opcao1": opcoes[0]["valor_unidade_excedente"] if len(opcoes) > 0 else "",
        "n_parcelas_opcao2": str(opcoes[1]["n_parcelas"]) if len(opcoes) > 1 else "",
        "valor_parcela_opcao2": opcoes[1]["valor_parcela_fmt"] if len(opcoes) > 1 else "",
        "valor_unidade_opcao2": opcoes[1]["valor_unidade_excedente"] if len(opcoes) > 1 else "",
        "n_parcelas_opcao3": str(opcoes[2]["n_parcelas"]) if len(opcoes) > 2 else "",
        "valor_parcela_opcao3": opcoes[2]["valor_parcela_fmt"] if len(opcoes) > 2 else "",
        "valor_unidade_opcao3": opcoes[2]["valor_unidade_excedente"] if len(opcoes) > 2 else "",
        # Prazos
        "validade_proposta": data.validade_proposta,
        "prazo_conclusao": data.prazo_conclusao,
        # Itens
        "itens": itens_fmt,
        "total_itens": _format_currency(total_itens) if itens_fmt else "",
    }

    tpl.render(context)

    buffer = io.BytesIO()
    tpl.save(buffer)
    buffer.seek(0)
    return buffer.read()
