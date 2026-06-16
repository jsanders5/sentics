# TODO

Tracked follow-ups for the sentics platform.

## Fundamental analysis (news/catalyst) — Agent 4

- [x] **FA layer shipped (commit e945eff).** Agent 4 scans per-coin news via Claude
  web_search → `fa_score` (sentiment×magnitude) + catalyst/summary/sources; blended
  into conviction (agreement strengthens, opposition weakens; does NOT flip the TA
  direction yet). Append-only `fa_snapshots` logs a point-in-time read each run.
  - [x] **Run migration 004** in Supabase (done).
  - [x] **Cheaper news source (commit b2c8f13).** Swapped Claude web_search (per-
    search fee, ~$5/run) for CryptoPanic free-tier headlines + a cheap classify
    model (default `claude-haiku-4-5`, override via `AGENT4_MODEL`). No-headline
    coins skip the model call (free); web search no longer required on the account.
  - [x] **Freshness regression fixed (commit 5d0c716).** Adding Agent 4 pushed the
    pipeline past the Vercel function time limit; since persistence was the LAST
    step and Vercel SIGKILLs on timeout (no background continuation, no Sentry), the
    run spent tokens but never wrote → dashboard stuck at the last pre-FA run, and
    the daily cron was failing too. Fix: persist a TA "freshness floor" right after
    Agent 2, then the full enriched write at the end; skip the FA scan for Neutral.
  - [x] **Async split so FA lands reliably (commits 6254ae8, 0724354).** Pipeline
    split into Stage 1 (`/api/run-pipeline`: TA + rationale + persist, then
    fire-and-forget) and Stage 2 (`/api/run-fa?offset&batch`: FA in 5-coin
    self-chaining batches that PATCH FA + re-blended conviction onto the rows +
    append snapshots). Small batches fit even a low function limit. Refresh button
    is now fire-and-forget + polls `/api/candidates` (no more connection-error).
  - [ ] **SETUP before next run:** (a) run **migration 005** (adds
    `directional_score`); (b) set **`CRYPTOPANIC_API_KEY`** (free signup) on the
    backend env — without it FA is neutral (no-op, no cost); (c) set
    **`AGENTS_SELF_URL`** on the backend env to its own public URL (default
    `https://sentics-agents.vercel.app`) so Stage 1 triggers Stage 2 and batches
    self-chain. Verify the chain runs (`fa_snapshots` row count grows in batches;
    catalysts appear in the drawer over ~1-2 min).
  - [ ] **FA backtest (accumulate-forward):** once enough daily `fa_snapshots`
    accrue (~weeks–months), extend `backtest.py` to join stored fa_scores with
    recomputed TA + forward returns; calibrate `FA_WEIGHT` and decide whether FA may
    flip direction. (Or buy a point-in-time sentiment archive to backtest now.)
  - [ ] **Surface FA on the card** (currently drawer-only) once it's proven useful.

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

- [~] **Backtest-calibrate the constants — HARNESS + CACHE + first calibration done.**
  `api/scripts/backtest.py` (disk-cached, 429-backoff, spaced, CSV dump) replays the
  real scoring over historical daily closes. Findings on 12 coins / 365d (501
  samples, stable across a coin train/test split):
  - **Trend magnitude does not predict edge** (corr(conviction,edge) ~ −0.07,
    non-monotonic quintiles) — confirmed OOS. **Only agreement generalizes**:
    Low-confidence calls are reliably bad (−6.8% edge), High/Medium ~flat.
  - **Done (commit 54aa0f5):** conviction recalibrated to magnitude-base + agreement
    (Low penalty); corr → −0.017, stable OOS; Low now ranks ~40 vs Medium ~67/High 76.
  - **30-coin / 1257-sample run (commit d1b37ff):**
    - **Regime dependence is the dominant effect.** Sub-period edge: early +3.3%
      (hit 60%), mid +2.5% (hit 57%), late −5.3% (hit 35%). The momentum model has
      real edge in trending thirds and inverts in chop.
    - The smaller sample's "High > Medium > Low" did **not** hold — High went
      negative (−4.3%). Removed the overfit High bonus; kept the Low penalty
      (Low is worse in both runs). Conviction magnitude still non-predictive.
  - **Still open / honest caveats:**
    - Conviction is not *positively* predictive — and the larger run shows the
      directional model's edge is **regime-gated**, not absent. Don't overfit one
      window.
    - Validate across **multiple market regimes / longer history** — free tier caps
      daily history ~365d → needs a paid key or stitched windows for multi-year.
    - Add **path-dependent trade-plan eval** (did target hit before stop?) +
      transaction costs for a truer read.
    - Still overlaps with OHLC/ATR (#2) for the volatility/stop constants.

- [ ] **Directional model: separate skill from beta, then decide framing (NEW —
  supersedes the naive regime-filter idea).** A momentum regime gate was prototyped
  (`market_regime`/`regime_allows` in agent2, experimental/not wired) and
  **backtested — it made edge WORSE** (TAKEN −1.3% vs ungated +0.8%). The bias/beta
  diagnostic (now in `backtest.py`) explains why: on the tested 365d window the
  model was net-short (65% Bearish) while price fell −5.6%, so the apparent edge is
  largely **directional beta**, not timing — Bullish calls lost −6.9%, Bearish won
  +4.9%. It also behaves **contrarian** here (Bearish/up +11.7% hit 76%; Bullish/up
  −7.4%), the opposite of momentum. Open work:
    - **Get multi-regime data** (a bull AND a bear window) — single down-window
      results can't separate skill from beta. Needs paid CoinGecko / stitched
      history beyond the free ~365d.
    - **Evaluate edge market-relative** (vs BTC / vs equal-weight basket), not raw,
      to strip beta.
    - Then decide: is the directional model momentum or contrarian — or is it mostly
      a directional bet that should be presented as such? This is a model-DESIGN
      question, not constant tuning.
    - Add path-dependent (target-vs-stop) evaluation alongside.

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
