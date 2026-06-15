---
name: project-agent2-directional-redesign
description: Agent 2 was rebuilt from the 50/35/15 candidate-score blend into a top-25 directional conviction model; v2 scoring redesign spec delivered 2026-06-15
metadata:
  type: project
---

As of 2026-06-15, `api/lib/agents/agent2.py` is NO LONGER the 50/35/15 technical/category/on-chain blend described in [[project-oq3-formula-validation]]. It now analyzes the top 25 non-stablecoin coins and produces a directional call (Bullish/Bearish/Neutral), a `directional_score` (internal), and a `candidate_score` (0-100 conviction, the UI "Conviction" ring + sort key). `category_momentum` is hardcoded 0; on-chain boosts are gone. Inputs are close-only (~120 daily closes+volumes from CoinGecko market_chart); no OHLC/ATR.

**Why:** Product pivoted Agent 2 from category-gated candidate discovery to a pure directional/conviction engine over the fixed top-25 universe.

**How to apply:** When validating Agent 2 hit rate, the thing to backtest is now directional accuracy (did Bullish coins go up / Bearish down over the time_horizon) and conviction calibration (do high-conviction calls hit more often), NOT the 50/35/15 weight regression. The OQ3 backtest requirements (n>=385/horizon, 95% CI lower bound >50%, p<0.05) still apply but reframed around direction.

## v2 scoring redesign spec (delivered 2026-06-15, addresses 8 flagged issues)
Key decisions made in the redesign (pending implementation):
- `directional_score` recomposed to exact [-100,+100]: trend ±45 (collapses the 3 collinear MA signals via tanh of a blended deviation), momentum ±40 (tanh of 0.6*mom7+0.4*mom30), RSI ±15 (smooth signed Gaussian peaking at 57). Volume removed from directional_score (it's unsigned).
- Conviction: directional coins map |ds| in [20,100] -> [50,95], +5 volume bump if ratio>=1.3 (directional only). Neutral coins map to [0,20] so they can never outrank directional. Neutrals KEPT in returned list (universe completeness), sorted to bottom.
- `technical_score` redefined as direction-agnostic setup strength (trend 25 + momentum 18 + volume 15 = 0-58); denominator /58 unchanged.
- RSI<30 no longer treated as bullish (was a contradiction); oversold downtrends now read Bearish/Short.
- Timeframe Long now = calm+persistent (low close-to-close vol + return consistency), fixing the backwards "big MA gap = Long" bug.
- Trade-plan R/R now structure-driven (resistance/support + measured move), clamped to [0.5, 5], replacing the 2*vol/1*vol pinning at R/R~2.
- RSI switched to Wilder smoothing (seed + recursive); canonical 30/70 thresholds kept (they were designed for Wilder).
- `calculate_moving_average` returns None when len<period (was returning last price, corrupting MA50); MIN_PRICES raised to 50 with graceful degraded mode for [20,50).
