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

## Scoring-model redesign (from the Opus review of agent2.py)

These are design decisions, not mechanical bugs — best done as a deliberate,
SME-led pass (data-science-ml-specialist) rather than ad-hoc tweaks, since they
change the meaning of the numbers users see.

- [ ] **Conviction formula wastes scale and lets Neutral outrank real calls.**
  `compute_candidate_score` = `50 + abs(directional_score)*0.5` floors every coin
  at 50, compresses strong trends into ~87–98, and (via `abs()` + the volume
  bonus) lets a Neutral coin with volume score above a genuine Bullish coin —
  even though Neutral coins get no trade plan, yet `run()` ranks purely by this
  score. Map `|directional_score|` directly to 0–100, force Neutral low/zero (or
  exclude from the ranked list), and apply the volume bump only to directional
  candidates.
- [ ] **`ma_score` is effectively dead** (`calculate_technical_score`). It scales
  fractional MA-deviations by `*5`, so the MA-alignment term contributes ~0–2 of
  its nominal 18 points; `technical_score` is really ~0–40, not the advertised
  0–58. Rescale (≈`*45`) or cap each leg, then re-validate the /58 normalization.
- [ ] **RSI regime is discontinuous and self-contradictory** (`analyze_direction`).
  Step jumps at 50/70 can flip the direction verdict on a hair of RSI movement,
  and the `RSI<30 → +5` (bullish mean-reversion) bolted onto a trend score
  contradicts the trend signals. Replace with a smooth contribution peaking
  ~55–60; drop the oversold bump unless modeled separately.
- [ ] **MA signals double-count.** price-vs-MA20 (±20), price-vs-MA50 (±15), and
  MA20-vs-MA50 (±20) are collinear — ~55 of the 100-point scale moves together in
  any trend, inflating `|directional_score|`. Collapse into one trend factor and
  rebalance toward independent signals (momentum, volume, RSI).
- [ ] **"Long" timeframe condition looks backwards** (`assign_timeframe`): a large
  `ma_trend` gap (≥8%) signals a recent sharp move (short-term), not a stable
  trend. Require persistence (price above MA50 over many bars / small positive
  `ma_trend`) for "Long".
- [ ] **R/R is semi-artificially pinned near 2:1.** Target uses `2*vol` while the
  stop floor uses `1*vol`, so in the vol-dominated regime R/R ≈ 2.0 by
  construction, not measured. Either derive both legs from structure or label 2:1
  as a template, not a measurement. (The volatility floor we added stops the
  extreme inflation; this is the remaining shape issue.)
- [ ] **Wilder's vs Cutler's RSI** (`utils.calculate_rsi`). Current impl is a
  simple mean of the last 14 deltas (Cutler's), won't match TradingView, and
  discards the rest of the 120-day series. Threshold-sensitive logic (50/70/72/28)
  flips on the difference. Switch to Wilder's smoothing or document the choice and
  relax the thresholds.
- [ ] **`calculate_moving_average` returns last price when data < period**, silently
  corrupting MA50 for coins with <50 days; `MIN_PRICES=15` admits such coins to
  full analysis. Return None and gate MA50/structure signals (and the trade plan)
  on ≥50 points, or downgrade confidence.

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
