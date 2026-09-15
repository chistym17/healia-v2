-- Healia schema (PostgreSQL / Supabase)
-- Security model:
--   • RLS enabled + forced on all tables (deny by default)
--   • PUBLIC / anon have zero table access
--   • authenticated may only touch their own rows (auth.uid())
--   • Backend via DATABASE_URL (postgres / bypassrls) can still manage data
--
-- Apply in Supabase SQL Editor, or:
--   psql "$DATABASE_URL" -f db/migrations/001_init.sql

create extension if not exists "pgcrypto";

-- ---------------------------------------------------------------------------
-- users
-- When using Supabase Auth, set users.id = auth.users.id on signup.
-- ---------------------------------------------------------------------------
create table if not exists public.users (
  id uuid primary key default gen_random_uuid(),
  email text not null unique,
  display_name text,
  password_hash text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- session_history
-- ---------------------------------------------------------------------------
create table if not exists public.session_history (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references public.users (id) on delete set null,

  livekit_room_name text,
  livekit_session_id text,

  status text not null default 'started'
    check (status in ('started', 'in_progress', 'processing', 'completed', 'failed')),

  title text,
  transcript jsonb not null default '[]'::jsonb,

  started_at timestamptz not null default now(),
  completed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists session_history_user_id_idx
  on public.session_history (user_id);

create index if not exists session_history_started_at_idx
  on public.session_history (started_at desc);

-- ---------------------------------------------------------------------------
-- session_results
-- ---------------------------------------------------------------------------
create table if not exists public.session_results (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null unique
    references public.session_history (id) on delete cascade,

  summary text not null default '',
  possible_concerns text not null default '',
  actions jsonb not null default '[]'::jsonb,
  warning_signs text not null default '',
  seek_care text not null default '',
  "references" jsonb not null default '[]'::jsonb,

  spoken_answer text,
  confidence text,
  raw_guidance jsonb,

  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists session_results_session_id_idx
  on public.session_results (session_id);

-- ---------------------------------------------------------------------------
-- updated_at helper
-- ---------------------------------------------------------------------------
create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists users_set_updated_at on public.users;
create trigger users_set_updated_at
  before update on public.users
  for each row execute function public.set_updated_at();

drop trigger if exists session_history_set_updated_at on public.session_history;
create trigger session_history_set_updated_at
  before update on public.session_history
  for each row execute function public.set_updated_at();

drop trigger if exists session_results_set_updated_at on public.session_results;
create trigger session_results_set_updated_at
  before update on public.session_results
  for each row execute function public.set_updated_at();

-- ---------------------------------------------------------------------------
-- Lock down grants (no public / anon API access)
-- ---------------------------------------------------------------------------
revoke all on table public.users from public, anon, authenticated;
revoke all on table public.session_history from public, anon, authenticated;
revoke all on table public.session_results from public, anon, authenticated;

-- Authenticated clients may use own rows only (policies below).
grant select, update on table public.users to authenticated;
grant select, insert, update on table public.session_history to authenticated;
grant select, insert, update on table public.session_results to authenticated;

-- No DELETE for clients — soft-close sessions via status instead.
-- No grants to anon at all.

-- ---------------------------------------------------------------------------
-- Row Level Security (deny by default; force even for table owner roles)
-- ---------------------------------------------------------------------------
alter table public.users enable row level security;
alter table public.users force row level security;

alter table public.session_history enable row level security;
alter table public.session_history force row level security;

alter table public.session_results enable row level security;
alter table public.session_results force row level security;

-- users: only own profile
drop policy if exists users_select_own on public.users;
create policy users_select_own on public.users
  for select
  to authenticated
  using (id = auth.uid());

drop policy if exists users_update_own on public.users;
create policy users_update_own on public.users
  for update
  to authenticated
  using (id = auth.uid())
  with check (id = auth.uid());

-- No insert/delete policies for authenticated on users
-- (signup should go through Auth + backend / service role)

-- session_history: only own sessions (never null user_id for client reads)
drop policy if exists session_history_select_own on public.session_history;
create policy session_history_select_own on public.session_history
  for select
  to authenticated
  using (user_id = auth.uid());

drop policy if exists session_history_insert_own on public.session_history;
create policy session_history_insert_own on public.session_history
  for insert
  to authenticated
  with check (user_id = auth.uid());

drop policy if exists session_history_update_own on public.session_history;
create policy session_history_update_own on public.session_history
  for update
  to authenticated
  using (user_id = auth.uid())
  with check (user_id = auth.uid());

-- session_results: only via owned session
drop policy if exists session_results_select_own on public.session_results;
create policy session_results_select_own on public.session_results
  for select
  to authenticated
  using (
    exists (
      select 1
      from public.session_history sh
      where sh.id = session_id
        and sh.user_id = auth.uid()
    )
  );

drop policy if exists session_results_insert_own on public.session_results;
create policy session_results_insert_own on public.session_results
  for insert
  to authenticated
  with check (
    exists (
      select 1
      from public.session_history sh
      where sh.id = session_id
        and sh.user_id = auth.uid()
    )
  );

drop policy if exists session_results_update_own on public.session_results;
create policy session_results_update_own on public.session_results
  for update
  to authenticated
  using (
    exists (
      select 1
      from public.session_history sh
      where sh.id = session_id
        and sh.user_id = auth.uid()
    )
  )
  with check (
    exists (
      select 1
      from public.session_history sh
      where sh.id = session_id
        and sh.user_id = auth.uid()
    )
  );

-- ---------------------------------------------------------------------------
-- Optional: create public.users when a Supabase Auth user signs up
-- Keeps users.id = auth.users.id so RLS policies match.
-- ---------------------------------------------------------------------------
create or replace function public.handle_new_auth_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into public.users (id, email, display_name)
  values (
    new.id,
    new.email,
    coalesce(new.raw_user_meta_data->>'display_name', split_part(new.email, '@', 1))
  )
  on conflict (id) do nothing;
  return new;
end;
$$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_auth_user();
