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

## Technical Filter Assessment
- RSI 40–72: ACCEPTED. Upper bound of 72 (not 70) is specifically correct for crypto.
- Volume 1.3x: ACCEPTED. Crypto-appropriate lower bar vs. equities 1.5x.
- Price >= 20d SMA AND 50d SMA: ACCEPTED. Dual-MA requirement reduces false positives.

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
