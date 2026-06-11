---
name: project-rate-limit-fix
description: CoinGecko 429 rate limit root cause and recommended fix — Agent 2 market_chart loop is the culprit; caching + provider migration options analyzed
metadata:
  type: project
---

CoinGecko free tier 429 errors diagnosed 2026-06-10. Running ~1-2 pipeline runs/day.

**Root cause:** Agent 2's `market_chart` loop calls `/coins/{id}/market_chart` for every coin in every passing category (`per_page: 100` × up to 7 categories = up to 700 calls per run). Agent 1 only adds ~28 calls. Total per run: ~335 calls. At 2 runs/day = ~670/day = 20,000/month vs. CoinGecko free tier cap of ~10,000/month.

**Fastest fix (no provider switch):** `fetch_market_chart()` in utils.py is NOT using the Redis cache already wired in `cache_set`/`cache_get`. Adding a 12-hour TTL cache to that function drops ~300+ calls/run to ~0 on repeated runs within the TTL window. 30 minutes of work.

**Recommended long-term hybrid (free tier, $0/month):**
- Market cap rankings + BTC dominance → CoinCap (/v2/assets, 500 req/min, no monthly cap)
- OHLCV history 30d daily → Binance Public API (/api/v3/klines, 1200 req/min, no monthly cap, no lifetime cap)
- Category coin lists → Keep CoinGecko with 6h TTL cache (<200 calls/month)

**Binance klines migration notes:**
- Symbol-based (BTCUSDT format) not ID-based; need COINGECKO_ID_TO_BINANCE mapping for CATEGORIES dict (26 entries)
- Agent 2 coin loop: use `f"{coin['symbol'].upper()}USDT"` from /coins/markets response — works for ~95% of top 100
- Response: array of arrays. Index 4 = close price (string), index 7 = quote asset volume (USD terms for USDT pairs)
- Normalize to `{prices: [[ts_ms, close]], volumes: [[ts_ms, usd_volume]]}` — identical shape to current fetch_market_chart output
- Gap: coins not listed on Binance (some small gaming/DeFi tokens) return 400; skip or fall back to Kraken OHLC

**What NOT to use:**
- CoinDesk/CCData (formerly CryptoCompare): 11,000 calls/month cap + 250,000 LIFETIME cap — exhausted in ~12 months at current volume, hard dealbreaker
- CMC Free: No historical OHLCV on free tier — hard blocker
- Messari Free: 20 req/min rate limit makes Agent 2 run take ~15 minutes — too slow
- CoinCap: Good for rankings/BTC dominance but no OHLCV/volume history per coin

**Why:** Agent 2's `per_page: 100` category coin list is the call multiplier. Even reducing to 20 coins/category would cut calls by 5x while still catching top mid-caps.

**How to apply:** Before recommending a full provider migration, suggest caching fix first. The Redis infra is already in place in utils.py.
