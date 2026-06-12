---
name: project-context
description: Core context for sentics-sti dashboard design — stack, data model, PRD scope, persona priorities
metadata:
  type: project
---

## Project: Sentics Trading Intelligence (STI) — Phase 1 Dashboard

Phase 1 is a crypto-only, public (no auth), read-only trading intelligence dashboard. Phase 2 adds equities and user accounts. Design must support Phase 1 cleanly and not block Phase 2 extensibility.

**Why:** Faster to market by eliminating equities, auth, and fundamental analysis complexity. Phase 2 gate is 60-day PMF review.

**How to apply:** Design every component so it can accept an asset-class prop (crypto vs. equity) in Phase 2. Leave expansion slots in the layout for watchlist, alerts, and portfolio panels.

## Stack (from code)
- Next.js 16 (App Router), React 19, Tailwind CSS 4, TypeScript
- Fonts: Geist Sans (body) + Geist Mono (numbers) — already loaded in layout.tsx
- Dark mode: CSS variable pattern already in globals.css (`prefers-color-scheme: dark`)
- No component library installed — build from scratch with Tailwind

## Data Model (from API routes)
**Candidates** (`/api/candidates`): symbol, name, category, price, time_horizon (Short/Medium/Long), confidence_tier (High/Medium/Low), score (0–100), rationale, entry_type (Breakout/Retest/Dip-Buy), entry_quality (Strong/Moderate/Speculative), updated_at

**Categories** (`/api/categories`): name, momentum_score (0–100), macro_adjustment, updated_at

**Missing from API (needs backend extension for full spec):** rsi_14d, volume_ratio, price_vs_20d_ma_pct, price_vs_50d_ma_pct, on_chain signals, last_news_headline, protocol_event_flag, is_meme_coin, pre_trade_reference (resistance_zone, invalidation_zone, atr_14d, min_rr)

## Personas (from PRD Section 4)
- Casey (primary): active crypto trader, 2 min on dashboard, wants highest-conviction setups first
- Alex (secondary): equity trader, wants credible screener-style interface, no hype
- Jordan (tertiary, post-MVP): passive opportunist, checks once daily, wants top 3

## Phase 1 MVP Scope (relevant to UI)
- Ranked candidates table (25 max), sortable by any column
- Category overview panel with momentum scores
- Filter bar: time horizon, category, confidence
- Detail drawer per candidate (full rationale, signals, pre-trade reference)
- Disclaimer modal on first visit
- Staleness banner if data > 7 hours old
- Skeleton loading states
- No auth, no watchlist, no portfolio in Phase 1
