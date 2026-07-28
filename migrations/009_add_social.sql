-- Migration 009: LunarCrush social layer (replaces the RSS/Agent-4 FA layer).
-- Run in the Supabase SQL editor. Idempotent.
--
-- `candidates.social` holds the current per-coin social read (sentiment, galaxy
-- score + delta, alt_rank + delta, social dominance/volume, topic) as JSON, for
-- display. `social_snapshots` appends an immutable point-in-time row per coin per
-- run so we can BACKTEST whether social velocity predicts returns before ever
-- letting it influence the score (display-only until validated).

alter table public.candidates add column if not exists social jsonb;

create table if not exists public.social_snapshots (
  id                bigint generated always as identity primary key,
  captured_at       timestamptz not null default now(),
  run_ts            timestamptz,
  symbol            text not null,
  name              text,
  price             double precision,
  sentiment         double precision,
  galaxy_score      double precision,
  galaxy_delta      double precision,
  alt_rank          double precision,
  alt_rank_delta    double precision,
  social_dominance  double precision,
  social_volume_24h double precision,
  interactions_24h  double precision
);

create index if not exists social_snapshots_symbol_captured_idx
  on public.social_snapshots (symbol, captured_at desc);
