-- Migration 006: persist a small OHLC candle series for the card mini-chart.
-- Run in the Supabase SQL editor. Idempotent.
--
-- Agent 2 fetches OHLC from CoinGecko, aggregates to ~30 daily candles, and stores
-- them as a JSON array of {o,h,l,c} objects so the dashboard can render a compact
-- candlestick chart per card without an extra client-side API call.

alter table public.candidates add column if not exists ohlc jsonb;
