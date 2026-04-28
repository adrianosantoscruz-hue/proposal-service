/**
 * ─────────────────────────────────────────────────────────────────────────────
 * Como integrar o Proposal Service ao seu sistema existente
 * ─────────────────────────────────────────────────────────────────────────────
 *
 * Você já usa Supabase Auth — o token JWT do usuário logado é exatamente
 * o que o microserviço espera. Nenhum login extra necessário.
 *
 * Funciona com: React, Next.js, Vue, Angular, ou qualquer JS moderno.
 * ─────────────────────────────────────────────────────────────────────────────
 */

import { createClient } from "@supabase/supabase-js";

// Seu cliente Supabase existente
const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY
);

// URL do microserviço (troque pelo IP/domínio do seu VPS em produção)
const PROPOSAL_SERVICE_URL =
  process.env.NEXT_PUBLIC_PROPOSAL_SERVICE_URL || "http://localhost:8000";

// ─────────────────────────────────────────────────────────────────────────────
// Helper: pega o JWT do usuário logado
// ─────────────────────────────────────────────────────────────────────────────
async function getAuthHeader() {
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (!session) throw new Error("Usuário não autenticado.");

  return {
    Authorization: `Bearer ${session.access_token}`,
    "Content-Type": "application/json",
  };
}

// ─────────────────────────────────────────────────────────────────────────────
// Gerar uma nova proposta
// ─────────────────────────────────────────────────────────────────────────────
export async function generateProposal(proposalData) {
  const headers = await getAuthHeader();

  const response = await fetch(`${PROPOSAL_SERVICE_URL}/generate-proposal`, {
    method: "POST",
    headers,
    body: JSON.stringify(proposalData),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Erro ao gerar proposta");
  }

  return await response.json();
  // Retorna: { id, numero_proposta, cliente_nome, data, valor, url_docx, url_pdf, created_at }
}

// ─────────────────────────────────────────────────────────────────────────────
// Listar propostas do usuário
// ─────────────────────────────────────────────────────────────────────────────
export async function listProposals(page = 1, perPage = 20) {
  const headers = await getAuthHeader();

  const response = await fetch(
    `${PROPOSAL_SERVICE_URL}/proposals?page=${page}&per_page=${perPage}`,
    { headers }
  );

  if (!response.ok) throw new Error("Erro ao listar propostas");
  return await response.json();
}

// ─────────────────────────────────────────────────────────────────────────────
// Exemplo de uso completo em um componente React
// ─────────────────────────────────────────────────────────────────────────────
export async function exampleUsage() {
  try {
    const result = await generateProposal({
      // Dados do cliente
      cliente_tratamento: "Sr.",
      cliente_condominio: "Condomínio do Edifício Solar dos Ipês",
      cliente_contato: "Carlos Mendes",
      cliente_endereco: "Av. Atlântica, 500. Copacabana. Rio de Janeiro – RJ.",
      cliente_telefone: "(21) 9.9999-9999",
      cliente_email: "sindico@solar.com.br",
      cliente_cnpj: "12.345.678/0001-99",
      cliente_cargo: "Síndico",

      // Descrição do serviço
      descricao_servico:
        "Modernização e reforma do agrupamento de PC com aumento de carga",

      // Itens (opcional — para exibir tabela de serviços)
      itens: [
        {
          descricao: "Instalação de quadro CPG",
          unidade: "un",
          quantidade: 1,
          valor_unitario: 15000.0,
        },
        {
          descricao: "Fornecimento e instalação de painéis PMD",
          unidade: "un",
          quantidade: 24,
          valor_unitario: 12000.0,
        },
      ],

      // Opções de pagamento (1 a 3)
      opcoes_pagamento: [
        {
          descricao: "Pagamento por Medição (Boleto Bancário)",
          n_parcelas: 1,
          valor_total: 322000.0,
          valor_unidade_excedente: "(R$2.250,00) VALOR ACIMA DE 30 UNIDADES",
          cronograma_pagamento: [
            { etapa: "Aprovação do projeto", percentual: "0%" },
            { etapa: "Entrega dos novos painéis", percentual: "50%" },
            { etapa: "Término da obra", percentual: "90%" },
            { etapa: "Aprovação da concessionária", percentual: "10%" },
          ],
        },
        {
          descricao: "Parcelado em 12x via Boleto",
          n_parcelas: 12,
          valor_total: 350400.0,
          valor_unidade_excedente: "(R$2.550,00) A CIMA DE 30 UNIDADES",
        },
        {
          descricao: "Parcelado em 24x via Boleto",
          n_parcelas: 24,
          valor_total: 422400.0,
          valor_unidade_excedente: "(R$3.250,00) A CIMA DE 30 UNIDADES",
        },
      ],

      // Prazos
      validade_proposta: "20 (vinte) dias",
      prazo_conclusao: "90 (noventa) dias úteis",
    });

    console.log("✅ Proposta gerada:", result.numero_proposta);
    console.log("📄 PDF:", result.url_pdf);
    console.log("📝 DOCX:", result.url_docx);

    // Abre o PDF em nova aba
    window.open(result.url_pdf, "_blank");

    return result;
  } catch (error) {
    console.error("❌ Erro:", error.message);
    throw error;
  }
}

// ─────────────────────────────────────────────────────────────────────────────
// Alternativa com axios (caso prefira)
// ─────────────────────────────────────────────────────────────────────────────
/*
import axios from 'axios';

export async function generateProposalAxios(proposalData) {
  const { data: { session } } = await supabase.auth.getSession();

  const { data } = await axios.post(
    `${PROPOSAL_SERVICE_URL}/generate-proposal`,
    proposalData,
    {
      headers: {
        Authorization: `Bearer ${session.access_token}`,
      },
    }
  );

  return data;
}
*/
