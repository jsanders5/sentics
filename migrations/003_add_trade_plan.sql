-- Migration 003: add trade_plan (entry/target/stop/RR + confirmation conditions).
-- Run in the Supabase SQL editor. Idempotent.

alter table public.candidates add column if not exists trade_plan jsonb;
