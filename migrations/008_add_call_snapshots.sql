-- Migration 008: append-only ledger of every directional trade call.
-- Run in the Supabase SQL editor. Idempotent.
--
-- The `candidates` table is overwritten every run, so it can't tell us whether
-- past calls were right. This table APPENDS one immutable, point-in-time row per
-- directional call per run (the price/levels as shown at run time). Weeks later,
-- eval_calls.py fetches the realized forward price and scores each call — the
-- leak-free ground truth for whether the calls have live edge.

create table if not exists public.call_snapshots (
  id                bigint generated always as identity primary key,
  captured_at       timestamptz not null default now(),
  run_ts            timestamptz,
  symbol            text not null,
  name              text,
  direction         text,
  candidate_score   double precision,   -- conviction at call time (TA stage)
  confidence_tier   text,
  time_horizon      text,
  directional_score double precision,
  price             double precision,   -- price at call time = entry reference
  entry             double precision,
  target            double precision,
  stop              double precision,
  fa_score          double precision
);

create index if not exists call_snapshots_symbol_captured_idx
  on public.call_snapshots (symbol, captured_at desc);
