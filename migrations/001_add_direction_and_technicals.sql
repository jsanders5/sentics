-- Migration 001: support the top-25 directional model
--
-- Run this against the Supabase Postgres database (SQL Editor) BEFORE the next
-- pipeline run. Agent 2 now writes a `direction` plus the full technical field
-- set; without these columns the candidates upsert will fail with a 400.
--
-- All statements are idempotent (IF NOT EXISTS), safe to re-run.

alter table public.candidates add column if not exists direction        text;
alter table public.candidates add column if not exists price            double precision;
alter table public.candidates add column if not exists rsi              double precision;
alter table public.candidates add column if not exists volume_ratio     double precision;
alter table public.candidates add column if not exists technical_score  double precision;
alter table public.candidates add column if not exists category_momentum double precision;
alter table public.candidates add column if not exists key_signals      jsonb;
alter table public.candidates add column if not exists entry_type       text;
alter table public.candidates add column if not exists entry_quality    text;
alter table public.candidates add column if not exists updated_at       timestamptz default now();

-- `symbol` must be unique for the upsert (on_conflict=symbol) to work.
create unique index if not exists candidates_symbol_key on public.candidates (symbol);

-- Optional: drop the now-unused category column once you've confirmed nothing
-- else reads it. Left in place by default since it's harmless.
-- alter table public.candidates drop column if exists category;
