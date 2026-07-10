# TODO

Tracked follow-ups for the sentics platform.

## Trust & validation (CURRENT FOCUS)

The trade calls have **no demonstrated edge**, so the project is in **validation-first
mode: do NOT tune scoring constants until live data says there's something to tune.**

- [x] **Honest backtest baselines (commit 025aaf7).** `backtest.py` now reports
  Strategy vs Buy&Hold vs Skill (per-day-normalized, risk-adjusted, drawdown) and
  flags the "beats buy&hold" mirage when the book is one-sided in a trending window.
  **Verdict (365d × 30 coins):** absolute return ~zero (t −0.62; compounded −22%,
  −59% maxDD), conviction uncorrelated with edge (−0.025; High/85+ buckets negative),
  apparent edge is being net-short in a down year (beta, not skill).
- [x] **Live forward-tracking ledger (commit 996d6b7, migration 008 applied).**
  Pipeline appends an immutable point-in-time row per directional call per run to
  `call_snapshots`. `api/scripts/eval_calls.py` scores realized forward edge FROM THE
  LEDGER ITSELF (joins each call to the same coin's later snapshot ~horizon days out
  — no external API, no look-ahead).
  - [ ] **Eval cadence:** first Short (7d) readings ~1 week after 2026-06-24; Medium
    (30d) ~1 month; Long (90d) ~3 months. Run `python3 api/scripts/eval_calls.py
    --horizon 7` (then `--horizon 30`) and judge **absolute** return + whether
    signal-strength buckets rank. Treat <100 matured calls as provisional.
- [x] **Screener reframe (commit 6861875).** UI reframed from "trade signals" to a
  transparent technical screener: "Conviction"→"Signal strength" (explicitly not a
  forecast/recommendation), "Trade Plan"→"Technical Levels", "AI Trading
  Intelligence"→"Technical Screener", persistent framing line. Copy-only.
- [~] **Fibonacci levels tested — NO edge, not wired.** Added experimental
  `fibonacci_levels` / `fib_signal` (golden-pocket-in-trend, flip beyond 0.786) to
  `agent2.py` and a `backtest.py --fib` comparison. Result (365d × 30 coins):
  `corr(fib, forward_return) = −0.003` (zero standalone predictive value); blending
  it in moved skill-t +7.20→+7.22 (Δ+0.02, edge/hit slightly worse); it overlaps the
  trend term (corr +0.32). "Pure fib +2.51% edge" is a beta mirage (only 29% long in
  a down year). Kept experimental/not-wired. Untried variants if revisited: fib as
  mean-reversion (bounce=reversal), or as trade-plan LEVELS rather than a directional
  vote (wouldn't change directional edge but could affect R/R quality).
- [ ] **Decide based on live evidence (weeks out):** if the ledger shows real edge,
  resume calibration; if not, keep it a screener (and weigh retiring the 0–100 number
  entirely). Multi-regime data still needs paid CoinGecko / stitched history.

## Fundamental analysis (news/catalyst) — Agent 4

- [x] **FA layer shipped (commit e945eff).** Agent 4 scans per-coin news via Claude
  web_search → `fa_score` (sentiment×magnitude) + catalyst/summary/sources; blended
  into conviction (agreement strengthens, opposition weakens; does NOT flip the TA
  direction yet). Append-only `fa_snapshots` logs a point-in-time read each run.
  - [x] **Run migration 004** in Supabase (done).
  - [x] **Cheaper news source (commits b2c8f13, 8c7e5dd).** Swapped Claude
    web_search (~$5/run) for **free keyless crypto-news RSS** (Cointelegraph,
    CoinDesk, Decrypt, CryptoSlate; CryptoPanic's free tier was discontinued Apr
    2026, and the other free news APIs now require paid keys). Feeds fetched once
    per batch, filtered per coin, classified by a cheap model (`claude-haiku-4-5`,
    override `AGENT4_MODEL`). No-match coins skip the model call (free). No news API
    key needed; override feeds via `AGENT4_RSS_FEEDS`.
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
  - [x] **SETUP done:** migration 005 applied; `AGENTS_SELF_URL` set on the backend;
    chain verified (TA lands in ~1 min, FA self-chains, catalysts appear in the
    drawer). Migrations 006 (ohlc), 007 (tv_symbol), 008 (call_snapshots) also applied.
  - [x] **Stale-news + coin-specific FA fixes (commit ef85a06).** Drop articles
    older than `AGENT4_MAX_AGE_DAYS` (7); feed the model the article snippet (not just
    titles); coin-specific prompt ("a partner moving AWAY is bearish for this coin",
    score must match summary); one shared RSS snapshot per run across batches;
    case-insensitive symbol match, short tickers (≤2 chars) require a name match.
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
  - [x] **Reframed the "AI Trading Intelligence" tagline** → "Technical Screener"
    (commit 6861875; see Trust & validation above).
  - [ ] **Nice-to-have:** first-visit acknowledgment gate; maintain the 24-hour
    coin-exclusion capability for rapid enforcement response.

- [~] **Higher-precision price levels (OHLC) + ATR-based stops — PARTIALLY DONE.**
  **Mini-chart shipped (commit dff076e):** Agent 2 fetches CoinGecko `/ohlc` and
  aggregates 4h→daily into ~30 daily candles (`utils.aggregate_daily_ohlc`), stored
  in `ohlc` (migration 006) and rendered as a per-card SVG candlestick that links to
  TradingView (resolved per-coin via search, migration 007, commit 6919bc8). So the
  4h→daily aggregation now exists and could feed **ATR-based stops** — still deferred
  pending the validation work; the close-to-close volatility floor stays until then.

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
    - **Update (2026-06):** hardened backtest baselines confirm no skill in the one
      window (see Trust & validation). Net decision = **validation-first**: the live
      `call_snapshots` ledger + `eval_calls.py` now accrue leak-free forward data;
      revisit this design question once that data (ideally spanning a non-down regime)
      can separate skill from beta. Reframed to a screener in the meantime.

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

- [x] **Refresh timeout fixed (commits 6254ae8, 0724354).** Trigger is now
  fire-and-forget; the UI polls `/api/candidates` and shows an "Analyzing news…"
  progress badge (commit efc6e94) for any in-flight run (cron or manual).

- [x] **Scheduled cron fixed (commit ef85a06).** Vercel invokes cron paths with GET,
  but `/api/run-pipeline` was POST-only (405'd every scheduled run) — so the daily
  cron had never fired; data only stayed fresh via the manual button. Proxy now
  accepts GET + POST and forwards `trigger_type`. NOTE: on the **Vercel Hobby** plan
  the cron is once/day with loose timing (acceptable; no GitHub Action added).

- [ ] **`run-pipeline` has no auth.** The endpoint is public, so anyone could
  trigger expensive CoinGecko/Claude runs (and now also the GET cron path). Add a
  shared-secret guard (or similar) before public launch.
