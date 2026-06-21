-- Migration 007: persist the resolved TradingView symbol for the card chart link.
-- Run in the Supabase SQL editor. Idempotent.
--
-- A bare ticker isn't a valid TradingView symbol for every coin (and the top-25
-- rotates), so Agent 2 resolves each ticker to its real "EXCHANGE:SYMBOL" (e.g.
-- BINANCE:FETUSDT) via TradingView's symbol search and stores it here. The card
-- links to tradingview.com/chart/?symbol={tv_symbol}, falling back to the symbol
-- overview page when this is null.

alter table public.candidates add column if not exists tv_symbol text;
