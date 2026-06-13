-- Migration 002: add market_cap so the dashboard can sort by market cap.
-- Run in the Supabase SQL editor. Idempotent.

alter table public.candidates add column if not exists market_cap double precision;
