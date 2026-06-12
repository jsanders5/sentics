---
name: project-oq3-formula-validation
description: OQ#3 resolution — Agent 1 (50/35/15 price/volume/sentiment) and Agent 2 (50/35/15 technical/category/on-chain) formula validation status and sign-off decision
metadata:
  type: project
---

OQ#3 was answered on 2026-06-09. The formulas are analytically defensible as v1.0 hypothesis implementations. They are NOT yet empirically validated against historical data.

**Decision: Provisional Go for Agent 1 and Agent 2 development, conditioned on a mandatory pre-launch empirical validation checkpoint.**

**Why:** No historical backtest has been run. The PRD was written with intuitive weights; no regression or IC analysis has been performed against actual forward returns.

**How to apply:** If asked whether Agent 1/2 development can begin — yes, with the explicit condition that weights remain configurable system parameters until the pre-launch backtest is complete. The backtest must complete before Agent 2 enters production (not just development).

## Validated / Accepted Weights (v1.0 provisional)

**Agent 1 Category Momentum Score:**
- Price momentum: 50% (accepted — primary momentum driver, robust in literature)
- Volume momentum: 35% (accepted with caveat — correlated with price; wash trading is a data quality risk)
- News sentiment: 15% (accepted — weakest but orthogonal signal; NLP quality is key risk)
- Macro adjustment: -10 points if BTC dominance rises >2pp in 24h; floor at 40 if global market cap down >5% (both thresholds accepted provisionally)

**Agent 2 Candidate Score:**
- Technical alignment: 50% (accepted)
- Category momentum inheritance: 35% (accepted)
- On-chain signal boost: 15% (accepted; additive points +5/+3/+4 are accepted as v1.0 defaults)
- ONE ADJUSTMENT RECOMMENDED: exchange net flow boost should be +5 (not +3), active addresses should be +3 (not +5). Rationale: exchange flow is more directly tied to supply dynamics than address count.

## Technical Filter Assessment (updated 2026-06-10 after live run producing 0 candidates)

Two bugs were found and fixed:

**Bug 1 (Critical): Volume filter was comparing today's partial-day CoinGecko volume against 30 full trading days.**
CoinGecko market_chart daily endpoint includes the current partial UTC calendar day as the final data point. At 14:00 UTC that entry contains ~58% of a normal day's volume. The original code used `volumes[-1]` (partial) as the numerator against a 30-day mean that included 29 complete days + the same partial entry. This systematically produced ratios of 0.5–0.7x, making the 1.3x gate structurally impossible to pass during any mid-day run. Fix: use `volumes[:-1]` (drop partial day) consistently in all three volume ratio calculations (filter, scoring, reporting).

**Bug 2 (Structural): Technical score range 0–58 was blended 50/50 with category score range 0–100.**
The raw blend produced effective weights of ~37% technical / ~63% category, not 50/50. Candidate score max was 79, not 100. Fix: normalize technical_score to 0–100 (`technical_score / 58.0 * 100`) before blending.

**Threshold changes made:**
- Volume gate: 1.3x → 1.1x. Rationale: 1.3x is a breakout signal; for a daily pipeline, it eliminates all candidates in consolidating markets. Volume SCORING still rewards higher ratios continuously via `min(20, ratio * 10)`. The 1.1x floor only excludes dead/inactive coins.
- MA gate: price >= 20d AND 50d SMA → price >= 20d SMA only. Rationale: 50d MA is retained as a scoring factor in `calculate_technical_score` via `ma_above_50`; removing it from the hard gate prevents categorically blocking coins in valid consolidation near 50d support.

**Still to validate empirically:** These adjusted thresholds (1.1x, 20d-only MA gate) have not been backtested. They are operational fixes for the daily pipeline. Empirical threshold calibration is part of the mandatory pre-launch backtest.

- RSI 40–72: STILL ACCEPTED. Upper bound of 72 (not 70) is specifically correct for crypto.

## Pre-Launch Backtest Requirements (mandatory gate)
- Data: CoinGecko Pro OHLCV for top 50 coins, daily candles, 3–5 years minimum
- Forward returns: close-to-close at 7d, 28d, 90d
- "Hit" definition: price at end of window >= price at ranking date (binary, no stated target return ambiguity)
- Minimum sample: n >= 385 candidates per time horizon
- Required outcome: hit rate 95% CI lower bound > 50%; p-value < 0.05 per horizon
- Sentiment data depth: CryptoPanic has ~3 years; on-chain from Glassnode free tier has ~2 years
- OLS weight regression to compare proposed 50/35/15 against empirical optimal weights

## Projected Hit Rates (pre-backtest estimates, conservative)
- Short (1–7d): 51–54% (wide CI, momentum noisy at 7 days)
- Medium (1–4w): 54–57% (stronger signal; most likely to hit 55% target)
- Long (1–3mo): 52–56% (bear-market drag pulls this down in multi-year samples)
- The 55% target from the PRD is achievable for Medium horizon in favorable market regimes. Overall average is more likely 53–55%.

## Key Risks Flagged
1. Price/volume correlation inflates apparent weight diversity in Agent 1 — two components measuring the same thing
2. Sentiment NLP quality (CryptoPanic VADER-based) is unvalidated; 15% weight on noisy signal
3. Wash trading in crypto volume data degrades volume component reliability
4. Large tx count (+4 boost) is directionally ambiguous — whale buys and sells both show up as large tx
5. On-chain data availability is sparse for most top-50 coins outside BTC/ETH/major DeFi
6. No target return is defined for hit rate calculation — must be defined before backtest can be designed
