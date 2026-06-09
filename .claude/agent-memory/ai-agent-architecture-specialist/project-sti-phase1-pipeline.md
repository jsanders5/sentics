---
name: project-sti-phase1-pipeline
description: Sentics Trading Intelligence Phase 1 — three-stage crypto agent pipeline architecture, open questions, and current sprint blockers
metadata:
  type: project
---

Sentics Trading Intelligence (STI) Phase 1 is a crypto signal pipeline with three LLM-assisted agents: Agent 1 (Crypto Category Trend Scorer), Agent 2 (Crypto Discovery Ranker), Agent 3 (Forward-Looking Synthesis). Agents communicate via PostgreSQL only — no direct function calls. Redis cache (90-minute TTL) for dashboard reads.

**Why:** Phase 1 is the launch target. The pipeline must produce ranked crypto buy candidates with rationales 6 times per day, surfaced on a dashboard. Go/No-Go for launch requires three blockers to be resolved.

**How to apply:** All architectural decisions should default to PostgreSQL-first coupling, graceful degradation over perfection, and staying within the $50–$200/month LLM budget ceiling.

## Current Go/No-Go Blockers (as of 2026-06-08)

- **OQ#1**: Data vendor selection (CoinGecko vs. alternatives) — not yet resolved
- **OQ#2**: LLM provider selection for Agent 3 — Claude Sonnet 4.6 vs. GPT-4o — evaluation framework designed (this session); evaluation not yet run. Blocks Agent 3 sprint start.
- **OQ#3**: On-chain data sourcing (Nansen vs. Dune vs. Flipside) — not yet resolved

## Pipeline Architecture Summary

**Agent 1** — Scores 7 crypto categories (Layer 1, Layer 2, DeFi, AI Tokens, Exchange Tokens, Gaming/Metaverse, Meme Coins) using price momentum (50%), volume (35%), sentiment (15%). Output: Category Momentum Score per category. Runtime target: ≤8 min.

**Agent 2** — Filters top 50 crypto by 30-day avg market cap (stablecoins excluded). Must-pass filters: RSI 14-period between 40–72; trailing 5-day avg volume ≥1.3× trailing 30-day avg; price ≥ 20d SMA and 50d SMA. Scoring: technical alignment (50%), category momentum (35%), on-chain (15%). Output: up to 25 ranked candidates per run. Runtime: ≤10 min.

**Agent 3** — Calls LLM for each candidate. Produces: confidence_tier (High/Medium/Low), time_horizon (Short=1–7d/Medium=1–4w/Long=1–3mo), entry_type (Breakout/Retest/Dip-Buy), entry_quality (Strong/Moderate/Speculative), rationale_text (50–300 chars), pre_trade_reference (resistance zone, invalidation zone, ATR-14d, min R:R). Hard rules: meme coins capped at Medium confidence; High requires ≥3 signals with no conflicts. Runtime: ≤20 min.

**Full pipeline**: ≤40 min end-to-end. 6 runs/day max. Event-triggered runs (BTC flash crash, category volume 3×, major news, protocol events) count against the 6-run/day limit or run as category/coin-scoped sub-runs.

## Cost Model (verified 2026-06-08)

Claude Sonnet 4.6: $3.00/1M input, $15.00/1M output (PRD-cited figure of $1.50/$6 per 1M is ~2× outdated).
Estimated per-candidate cost (Agent 3): ~$0.014 at Sonnet 4.6 pricing.
Projected monthly (6 runs/day × 25 candidates): ~$60–$65/month. Within $50–$200 target.

## Hit Rate Target

>55% of candidates hitting stated target return within stated time horizon, measured at 90 days post-launch. This is the ultimate quality signal for the LLM provider choice.

See [[project-oq2-evaluation-framework]] for the full LLM evaluation protocol.
