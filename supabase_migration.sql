-- ─────────────────────────────────────────────────────────────────────────────
-- Migração: tabela de propostas
-- Execute no SQL Editor do Supabase Dashboard
-- ─────────────────────────────────────────────────────────────────────────────

-- Habilita UUID v4
create extension if not exists "pgcrypto";

-- Tabela principal de propostas
create table if not exists public.proposals (
    id              uuid primary key default gen_random_uuid(),
    user_id         uuid not null references auth.users(id) on delete cascade,
    numero_proposta text not null,          -- ex: "0042/2026"
    cliente_nome    text not null,          -- nome do condomínio
    cliente_contato text not null,          -- nome do contato/síndico
    cliente_email   text,
    data            date not null,
    valor           numeric(12, 2) not null default 0,
    url_docx        text,
    url_pdf         text,
    created_at      timestamptz not null default now(),
    updated_at      timestamptz not null default now()
);

-- Índices para performance nas queries mais comuns
create index if not exists proposals_user_id_idx on public.proposals(user_id);
create index if not exists proposals_numero_proposta_idx on public.proposals(numero_proposta);
create index if not exists proposals_created_at_idx on public.proposals(created_at desc);

-- Trigger para atualizar updated_at automaticamente
create or replace function public.set_updated_at()
returns trigger language plpgsql as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

create trigger proposals_updated_at
    before update on public.proposals
    for each row execute function public.set_updated_at();

-- ─────────────────────────────────────────────────────────────────────────────
-- Row Level Security (RLS)
-- O microserviço usa service_role key (bypass RLS).
-- Estas políticas protegem o caso de alguém acessar via anon key.
-- ─────────────────────────────────────────────────────────────────────────────
alter table public.proposals enable row level security;

-- Usuários autenticados só veem suas próprias propostas
create policy "Users can view own proposals"
    on public.proposals for select
    using (auth.uid() = user_id);

create policy "Users can insert own proposals"
    on public.proposals for insert
    with check (auth.uid() = user_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- Storage: Bucket de propostas
-- Execute no SQL Editor OU crie manualmente no Dashboard > Storage
-- ─────────────────────────────────────────────────────────────────────────────

-- Cria o bucket (se ainda não existir)
insert into storage.buckets (id, name, public)
values ('proposals', 'proposals', true)
on conflict (id) do nothing;

-- Política de storage: usuários autenticados fazem upload apenas na própria pasta
create policy "Authenticated users upload to own folder"
    on storage.objects for insert
    to authenticated
    with check (
        bucket_id = 'proposals'
        and (storage.foldername(name))[1] = auth.uid()::text
    );

-- Leitura pública (como o bucket é público, qualquer um com a URL pode baixar)
create policy "Public read proposals"
    on storage.objects for select
    to public
    using (bucket_id = 'proposals');
