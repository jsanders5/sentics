---
name: project-coingecko-plan
description: CoinGecko API plan selection analysis for Sentics pipeline — ~60 calls/run, Analyst/Pro tier selected, live pricing must be verified
metadata:
  type: project
---

CoinGecko API plan analysis completed 2026-06-09 for Phase 1 PRD Open Question #4.

**Selected plan:** CoinGecko Analyst/Pro tier (entry-level paid plan)
**Estimated cost:** ~$129/month (MUST BE VERIFIED at coingecko.com/en/api/pricing — pricing has changed multiple times)
**Rate limit:** ~500 calls/min on Pro tier (vs. 30 calls/min on free tier)

**Call volume per Agent 1 run (~60 calls):**
- 1 call: `/coins/markets` (all 50 coins, 24h/7d change, volume, market cap — fully batched)
- 50 calls: `/coins/{id}/market_chart?days=30` (hourly price+volume series, 1 per coin, not batchable)
- 1 call: `/global` (BTC dominance, global market cap)
- 1 call: `/coins/categories`
- 5–10 calls: events, metadata (cached weekly)

**Critical design note:** Use `/coins/{id}/market_chart?days=30&interval=hourly` NOT `/coins/{id}/ohlc` for hourly granularity. The `/ohlc` endpoint only returns 4-hour candles for 7–90 day windows — true hourly OHLCV is not available via that endpoint. Construct OHLC bars from market_chart price ticks if candlestick format is needed.

**Monthly volume estimates:**
- Typical (12 runs/day): ~21,600 calls/month
- Maximum (28 runs/day sustained): ~50,400 calls/month
- Free tier cap (~10,000/month): exceeded in all scenarios

**Why free tier fails:** (1) monthly call cap, (2) endpoint access restrictions on hourly data, (3) no commercial license.

**Fallback:** CoinMarketCap Startup plan (~$333/month). Cold standby only — not run simultaneously. CMC has no events API equivalent; skip events on CMC fallback runs.

**Open actions before PRD is finalized:**
1. Verify current Pro plan cost at coingecko.com/en/api/pricing
2. Confirm `/market_chart?interval=hourly` is available on Analyst plan (not Enterprise-only)
3. Confirm commercial/AI product use permitted under current ToS (coingecko.com/en/api/terms)
4. Verify CoinMarketCap Startup plan cost at coinmarketcap.com/api/pricing

**Why:** These are estimated figures from training data; CoinGecko has rebranded and repriced plans multiple times. Live verification is required before budget sign-off.

**How to apply:** When discussing CoinGecko costs, always caveat with "verify at pricing page" and reference the ~60 calls/run figure as the stable engineering constant.
