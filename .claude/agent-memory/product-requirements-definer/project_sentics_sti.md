---
name: Sentics Trading Intelligence Platform
description: Core product context for the STI dashboard — Phase 1 is crypto-only (PRD-phase1-crypto.md); Phase 2 adds equities (PRD-v1.0.md)
type: project
---

AI-powered web application dashboard that surfaces ranked buy candidates across crypto (Phase 1) and crypto + US equities (Phase 2). Product codename: Sentics Trading Intelligence (STI).

**Why:** Retail traders lack an affordable system that continuously surfaces trend-aware, time-horizon-appropriate trading candidates backed by multi-factor AI analysis. Phase 1 is crypto-only to accelerate time to market and reduce cost/complexity.

**How to apply:** Phase 1 is the active build target. Phase 2 (equities addition) is gated on Phase 1 achieving 3 of 4 success metrics at the 60-day review. When working on architecture or schema, favor Phase 2 compatibility.

---

## Phase Structure

| Phase | Scope | PRD | Status |
|---|---|---|---|
| Phase 1 | Crypto-only (top 50, no stablecoins) | docs/PRD-phase1-crypto.md | Draft 2026-04-30 |
| Phase 2 | Crypto + S&P 500 + NASDAQ 100 | docs/PRD-v1.0.md | Draft 2026-04-30 |

Phase 2 investment is contingent on Phase 1 hitting >= 3 of 4 success metrics at the 60-day review.

---

## Phase 1 Core Architecture

Three-agent sequential pipeline:
1. **Crypto Category Trend Agent** — Scores 6–7 crypto categories (L1, L2, DeFi, AI Tokens, Exchange Tokens, Gaming/Metaverse, Meme Coins) using price/volume momentum + news sentiment + BTC dominance macro signals. Threshold for Agent 2 trigger: >= 55.
2. **Crypto Discovery Agent** — Filters top-50 coins within trending categories. Technical filters: RSI 40–72, volume 5d/30d ratio >= 1.3x, price >= 20d AND 50d MA. On-chain signal boost (additive, where data available). Outputs up to 50 candidates.
3. **Forward-Looking Synthesis Agent** — LLM generates plain-English rationale, time horizon (Short 1–7d / Medium 1–4wk / Long 1–3mo), confidence tier. Max 25 candidates per run.

Agents communicate via shared PostgreSQL store (decoupled). Redis cache TTL = 90 min.

## Phase 1 Orchestration
- **Full pipeline**: Every 6 hours, 24/7 (00:00, 06:00, 12:00, 18:00 UTC)
- **Lightweight refresh**: Hourly Agent 1 + conditional Agent 2 (if category delta >= 12 points)
- **Agent 3 daily cap**: 6 runs/day (4 scheduled + 2 event buffer)
- **Event triggers**: BTC flash crash/spike (>=8% 1hr), category volume explosion (>=3x avg), news spike, protocol events
- No market-hours logic — crypto is 24/7

## Phase 1 Data Sources
- **Crypto price/volume/events**: CoinGecko Pro (required for hourly data)
- **On-chain signals**: Glassnode free tier (or CoinGecko on-chain; licensing TBD)
- **News/sentiment**: CryptoPanic API or NewsAPI.org
- **LLM rationale**: Anthropic Claude API (primary; evaluation vs. OpenAI required before commit)

## Phase 1 Cost Estimate
$50–$380/month (vs. Phase 2's $650–$1,980/month). Budget at $500/month.

## Phase 2 Additions (when gated Phase 1 review passes)
- S&P 500 + NASDAQ 100 equities
- GICS sector ETF data (XLK, XLF, etc.)
- SEC EDGAR Form 4 insider data
- Fundamental overlay (revenue growth, D/E, earnings surprises)
- Market-hours scheduling logic
- Polygon.io or Alpaca for equity data; Benzinga for equity news; FMP for fundamentals
- Max 30 candidates per run

## Success Metrics (both phases)
- > 55% of candidates hit target return within stated horizon at 90 days
- DAU/MAU >= 40% within 60 days
- 7-day user return rate >= 40% within 60 days
- 15% free-to-paid conversion (expressed interest) within 90 days

## Key Open Questions (as of 2026-04-30)
1. Legal: Does crypto-only analysis require any registration? Which coins have securities classification risk? (BLOCKING)
2. LLM provider: Anthropic Claude vs. OpenAI — structured evaluation required before Agent 3 sprint
3. Candidate Score formula: Data science lead sign-off required (BLOCKING for Agent 1/2)
4. CoinGecko Pro plan tier and cost confirmation (BLOCKING for data infrastructure)
5. Meme coin inclusion: confidence cap at Medium, or exclude entirely (BLOCKING for Agent 3 prompt engineering)
6. Monthly data/infra budget approval (BLOCKING for provider contracts)

## Tech Stack (Phase 1)
- Frontend: Next.js (React) + Auth.js
- Database: PostgreSQL via Supabase (migrate to AWS RDS for Phase 2 if needed)
- Cache: Redis via Upstash
- Agents: Python 3.11+ on AWS ECS Fargate
- Scheduler: AWS EventBridge
- Email: SendGrid
