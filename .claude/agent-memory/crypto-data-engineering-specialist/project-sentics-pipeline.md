---
name: project-sentics-pipeline
description: Core architecture facts for the Sentics multi-agent crypto coin ranking pipeline — agent run schedule, data sources, and budget constraints
metadata:
  type: project
---

Multi-agent crypto coin ranking pipeline. Phase 1 PRD is being designed (as of 2026-06-09).

**Agent run schedule:**
- Agent 1 runs every 6 hours (4 runs/day scheduled) + conditionally up to every hour (24 runs/day max if volatility threshold triggers) = up to 28 full runs/day
- Agent 2 and Agent 3 downstream of Agent 1

**Top-50 coins scope:** Pipeline covers top 50 coins by market cap, excluding stablecoins and wrapped tokens.

**API budget:** $500/month hard ceiling across all external data providers.

**Data sources in scope:**
- CoinGecko Pro (primary: price, OHLCV, market cap, events, categories)
- CryptoPanic (news sentiment, primary) → NewsAPI.org (fallback)
- Glassnode (on-chain metrics: active addresses, exchange flows, whale tx)
- CoinMarketCap Pro (CoinGecko fallback)

**Score composition (Agent 2):** On-chain signals are 15% of the score — if Glassnode is unavailable, the system still produces candidates without penalty.

**Why:** Building a data pipeline to support an AI-driven crypto coin ranking/screening product displayed to end users.

**How to apply:** Frame all API cost and volume analysis against the 28-run/day max and $500/month ceiling. Design for graceful degradation when any single provider is down.
