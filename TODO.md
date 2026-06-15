# TODO

Tracked follow-ups for the sentics platform.

## Trade plans (priority)

- [x] **Compliance review of trade plans — code/copy fixes DONE (commit 3129d31).**
  fintech-compliance-specialist (opus) pass applied: card micro-disclaimer,
  persistent footer, short-selling unlimited-loss disclosure, stronger plan
  footer, modal sections (Trade-Plan Levels / Short Selling / Regulatory Status),
  per-coin caveat for non-BTC/ETH, directive→descriptive label reframes.
  - [ ] **[COUNSEL] BLOCKERS before public launch** (not code — require a
    securities attorney): written sign-off naming the trade-plan entry/target/stop
    levels **and** the short framing specifically; documented no-monetization gate
    (the free status is the load-bearing IAA defense — a paid tier requires fresh
    review); Terms of Service + Privacy Policy live (limitation of liability, no
    warranty, arbitration; GDPR/cookie consent).
  - [ ] **Nice-to-have:** first-visit acknowledgment gate; maintain the 24-hour
    coin-exclusion capability for rapid enforcement response; reconsider the
    "AI Trading Intelligence" tagline.

- [~] **Higher-precision price levels (OHLC) + ATR-based stops — DEFERRED.**
  Decision: defer; do the backtest first and revisit only if stop placement is the
  weak link. **Finding (verified live):** CoinGecko's free/demo tier has NO daily
  OHLC — `/ohlc?days=30` returns 4-hour candles, `days≥90` returns 4-DAY candles,
  and the demo key lacks `/ohlc/range?interval=daily`. So true daily ATR needs one
  of: aggregate 4h→daily over ~30d (hybrid), a Binance-klines source, or CoinGecko
  Pro. The current close-to-close volatility floor stays until then.

## Scoring-model redesign — DONE (commit aa5e165)

Implemented as one coherent SME-led pass (data-science-ml-specialist, opus).
Verified: calibration matched the spec, end-to-end invariants held, tsc/py_compile clean.

- [x] **Conviction formula** — Neutral → [0,20), directional → [50,100]; full range
  used; Neutral can't outrank a directional call; volume bump directional-only.
- [x] **`ma_score` dead term** — `technical_score` is now a real 0–58, direction-
  agnostic setup strength (trend + momentum + volume, no dead MA term).
- [x] **RSI regime** — smooth gaussian factor peaking at 57; no step-jumps; oversold
  no longer flips the sign.
- [x] **MA double-count** — three collinear MA signals collapsed into one trend factor.
- [x] **"Long" timeframe** — fixed; now calm vol + one-way persistence + real 30d move.
- [x] **R/R shape** — emerges from swing/MA structure with vol floors + [0.5,5] clamp.
- [x] **Wilder's RSI** — seed + recursive smoothing over the full series.
- [x] **MA50 guard** — `calculate_moving_average` returns None on short history;
  `MIN_PRICES` 15→50.

- [~] **Backtest-calibrate the constants — HARNESS BUILT (commit 1b108c6).**
  `api/scripts/backtest.py` replays the real scoring over historical daily closes
  and reports directional edge / hit rate by confidence tier & conviction bucket
  + corr(conviction, edge). Remaining = the actual calibration:
  - Early read (3 coins, free-tier rate-limited, 365d): **confidence-tier ordering
    works** (High +8.8% edge > Medium > Low −15%); **conviction score isn't cleanly
    predictive yet** (corr ~0, non-monotonic buckets) → tune the conviction mapping
    / `DIR_THRESHOLD` / weights.
  - Run it across all 25 coins and multiple periods to get a real signal — the free
    tier 429s after a few coins, so this needs a paid CoinGecko key, caching, or
    spaced fetches.
  - Add path-dependent trade-plan evaluation (did target hit before stop?) and
    transaction costs for a truer read.
  - Still overlaps with OHLC/ATR (#2) for the volatility/stop constants.

## Other known open items

## LLM synthesis follow-ups (from the Opus review of agent3.py)

The rewrite already fixed the criticals (direction-aware entry_type, no fabricated
fallbacks, merge whitelist, MA values in prompt, retries, concurrency, defensive
content/stop_reason handling, model env override). Remaining:

- [ ] **Adopt structured outputs** (`output_config.format` / `messages.parse`) once
  the deployed `anthropic` SDK is known-recent — eliminates the manual JSON
  parsing entirely and enforces the enums at the API boundary. Held back now
  because `requirements.txt` only floors `anthropic>=0.30.0` and the feature is
  newer; bump the pin, then switch.
- [ ] **Consider the Batch API** for the daily run — 50% cheaper than the live
  concurrent calls, no latency downside on a scheduled batch.

## Other known open items

- [ ] **Refresh can time out on long runs.** `POST /api/run-pipeline` triggers the
  pipeline synchronously; a full run (~25 CoinGecko + 25 Claude calls) can exceed
  Vercel's function execution limit even though the run continues server-side.
  Make the trigger fire-and-forget and have the UI poll for completion.

- [ ] **`run-pipeline` has no auth.** The endpoint is public, so anyone could
  trigger expensive CoinGecko/Claude runs. Add a shared-secret guard (or similar)
  before public launch.
