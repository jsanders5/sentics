# TODO

Tracked follow-ups for the sentics platform.

## Trade plans (priority)

- [ ] **Compliance review of trade plans.** The dashboard now outputs specific
  entry / target / stop levels (`compute_trade_plan` in `api/lib/agents/agent2.py`),
  which moves from general "analysis" toward investment-advice territory. Before
  this goes public, run a review with the `fintech-compliance-specialist` agent:
  validate disclaimer language, the "educational / not financial advice" framing
  on plans, and the spot-vs-short presentation. Keep stop/risk shown alongside
  every target.

- [ ] **Higher-precision price levels (OHLC) + ATR-based stops.** Trade-plan
  levels currently use daily *closes* from CoinGecko's `market_chart` endpoint.
  This is fine for MA/swing logic but means stops/targets ignore true intraday
  highs and lows. To tighten them, pull `/coins/{id}/ohlc` and compute swing
  levels / ATR-based stops from real candle ranges (one extra API call per coin —
  mind rate limits). This would also replace the current stop-distance heuristic:
  we presently enforce a volatility floor of `max(daily_close_vol, 3%)` in
  `compute_trade_plan` (`agent2.py`) to stop tight stops from inflating R/R — a
  true ATR from OHLC would place stops on real volatility structure instead of a
  flat floor.

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

- [ ] **FOLLOW-UP: backtest-calibrate the constants.** The new structure is sound but
  the named constants (`W_TREND/W_MOM/W_RSI`, `K_TREND/K_MOM`, `RSI_PEAK/RSI_WIDTH`,
  `DIR_THRESHOLD`, conviction bands, timeframe thresholds in `agent2.py`) are
  un-backtested hypotheses. Calibrate against forward returns before relying on the
  exact numbers. (Overlaps with OHLC/ATR work for stop placement.)

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
