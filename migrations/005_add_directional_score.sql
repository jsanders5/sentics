-- Migration 005: persist the raw TA directional_score on candidates.
-- Run in the Supabase SQL editor. Idempotent.
--
-- The pipeline is split into stages (TA persists first, FA enriches in a separate
-- chunked invocation). The FA stage loads candidates from the DB, so it needs the
-- TA directional_score (not just the final conviction) to re-blend TA + FA.

alter table public.candidates add column if not exists directional_score double precision;
