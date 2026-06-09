# Sentics Trading Intelligence (STI) — Phase 1 Product Requirements Document

## Document Control

| Field | Value |
|---|---|
| **Version** | 1.0 |
| **Date** | 2026-04-30 |
| **Status** | Draft — Pending Legal Review |
| **Author** | Product |
| **Reviewers** | Engineering Lead, Legal Counsel, Data Science Lead |
| **Relationship to Phase 2 PRD** | This document defines the Phase 1 (crypto-only) MVP. The existing PRD-v1.0.md is repositioned as the Phase 2 target state. Phase 1 is a faster-to-market, lower-cost foundation scoped exclusively to cryptocurrency. |

---

## Table of Contents

1. [Problem Statement](#1-problem-statement)
2. [Product Vision](#2-product-vision)
3. [Goals and Success Metrics](#3-goals-and-success-metrics)
4. [User Personas](#4-user-personas)
5. [Scope](#5-scope)
6. [AI Agent Pipeline Architecture](#6-ai-agent-pipeline-architecture)
7. [Orchestration and Scheduling](#7-orchestration-and-scheduling)
8. [MVP Functional Requirements](#8-mvp-functional-requirements)
9. [Post-MVP Roadmap](#9-post-mvp-roadmap)
10. [High-Level Technical Architecture](#10-high-level-technical-architecture)
11. [Non-Functional Requirements](#11-non-functional-requirements)
12. [Legal, Compliance, and Disclaimers](#12-legal-compliance-and-disclaimers)
13. [Key Risks](#13-key-risks)
14. [Open Questions and Decisions Required](#14-open-questions-and-decisions-required)
15. [Go / No-Go Blockers](#15-go--no-go-blockers)
16. [Dependencies](#16-dependencies)

---

## 1. Problem Statement

Retail crypto traders face an acute information problem. The top 50 cryptocurrencies by market cap span multiple categories — Layer 1 blockchains, DeFi protocols, AI tokens, exchange tokens, and more — each with different momentum drivers, on-chain signals, and narrative catalysts. Monitoring this universe manually requires tracking dozens of price charts, following fragmented news sources across Twitter/X, Discord, Telegram, and crypto news sites, and interpreting on-chain data that requires specialized tooling to even access.

Existing tools are either mechanical (screeners that surface price data without synthesis) or conversational (AI chatbots that lack live market data and cannot systematically scan the full universe). Neither approach works 24/7 on the trader's behalf and surfaces opportunities proactively.

The crypto market never closes. It produces signals at 3 AM on a Sunday the same as it does at 11 AM on a Wednesday. A trader who sleeps, works, or simply blinks misses entries. The infrastructure required to monitor the market continuously — data feeds, scoring logic, synthesis — is beyond what any individual can build and maintain.

**Sentics Trading Intelligence (STI) Phase 1** is an AI-powered web application that runs a continuous, multi-stage analysis pipeline across the top 50 cryptocurrencies and delivers a curated, ranked list of buy candidates with a plain-English rationale, time horizon classification, and confidence signal — updated every 6 hours around the clock.

Phase 1 is crypto-only by design. Removing equities eliminates expensive data providers, SEC filing integrations, market-hours scheduling complexity, and fundamental analysis infrastructure. This focus accelerates time to market, reduces cost, and sharpens the product's initial identity for the crypto-first audience most likely to find it immediately valuable.

---

## 2. Product Vision

**Vision statement:** Give every serious crypto trader the analytical advantage of a quantitative research desk, available 24/7 at a price they can afford.

STI is not a trading platform, a portfolio manager, or a social network. It is an intelligence layer — a continuously updated ranked list of cryptocurrencies that a multi-agent AI system believes are worth serious consideration for purchase, organized by time horizon and explained in plain language.

The product surfaces *candidates*, not commands. Every output comes with a clearly labeled AI-generated rationale and a prominent disclaimer. The user makes the final decision.

Phase 1 proves the core value proposition in the crypto domain. Phase 2 extends the pipeline to US equities using the same architecture (see Section 9 and the Phase 2 PRD).

---

## 3. Goals and Success Metrics

### Business Goals

| Goal | Metric | Target | Measurement Window |
|---|---|---|---|
| Validate that AI candidates perform meaningfully | % of candidates hitting stated target return within time horizon | > 55% hit rate | 90 days post-launch |
| Build a sticky daily-use habit | DAU / MAU ratio | >= 40% | 60 days post-launch |
| Demonstrate retention | 7-day user return rate | >= 40% | 60 days post-launch |
| Establish a path to monetization | Free-to-paid conversion rate (expressed interest or waitlist sign-up) | >= 15% | 90 days post-launch |

### Launch Threshold

At least three of the four metrics above must be tracking on-target at 60 days. If fewer than three are on track, the product team will initiate a structured pivot review before committing to Phase 2 engineering investment.

### Explicit Non-Goals for Metrics

- Absolute return performance relative to crypto benchmarks (BTC, ETH) is not a launch metric. STI is not a fund. Hit rate on directional calls within the stated horizon is the correct proxy for pipeline quality.
- Revenue at launch is not a goal. Phase 1 is a retention and product-market-fit experiment.
- Equity coverage is not a Phase 1 goal. Adding equities before Phase 1 success is validated is out of scope and not worth the cost increase.

---

## 4. User Personas

### Primary: The Active Crypto Trader (Casey)

- Age 22–38, high risk tolerance
- Trades crypto daily or multiple times per week; may hold a small equity portfolio but crypto is the primary focus
- Monitors Twitter/X crypto accounts, Telegram alpha groups, on-chain data dashboards (Glassnode, Nansen); skeptical of traditional finance framing
- Spends 1–3 hours per day across news, charts, and social media seeking entry signals
- Values freshness and directional clarity above all — wants the latest signal, not yesterday's analysis
- Interested in narrative momentum and catalysts: ecosystem developments, token unlocks, protocol upgrades, macro correlation breakdowns
- Willing to pay $15–$30/month for a tool that saves time and improves conviction
- Technical comfort: high; reads charts, understands RSI and moving averages, may have used DeFi protocols

**Primary job-to-be-done:** "Tell me which coins are showing real momentum right now and why, in plain language — so I can make a faster, more confident entry decision."

### Secondary: The Active Retail Investor Branching into Crypto (Alex)

- Age 28–45, employed full-time outside finance
- Primarily trades equities but allocates 10–25% of their portfolio to crypto
- Comfortable with brokerage tools; less familiar with crypto-native data sources
- Wants the same quality of analysis they expect from an equity screener, applied to crypto
- Does not follow crypto Twitter; would not use a Telegram alpha group; wants a trustworthy, professional-grade interface
- Will become the primary Phase 2 persona when equities are added

**Primary job-to-be-done:** "Show me which crypto assets have a credible thesis right now — the same way I'd evaluate a stock pick — without having to learn the entire crypto research ecosystem."

### Tertiary (Post-MVP): The Passive Opportunist (Jordan)

- Primarily holds BTC and ETH long-term; occasionally wants to make a tactical altcoin trade
- Low engagement, does not want to spend time in-app
- Would use the daily email digest as their primary touchpoint
- Requires the lowest friction path from insight to action

---

## 5. Scope

### 5.1 In Scope for Phase 1

**Universe of assets**
- Top 50 cryptocurrencies by 30-day average market capitalization (CoinGecko sourced, updated weekly)
- Stablecoins are explicitly excluded from the candidate universe at the data ingestion layer: USDT, USDC, DAI, BUSD, TUSD, FDUSD, and any coin whose 30-day price standard deviation is < 0.5% are filtered out automatically. Stablecoins have no price momentum signal and their presence would pollute technical filter outputs.
- Wrapped tokens that are price-equivalent to a non-wrapped counterpart in the top 50 (e.g., WBTC vs. BTC) are deduplicated; the higher-liquidity version is retained.

**Crypto categories (replaces GICS sectors from Phase 2)**
The following categories are used as the organizational and scoring unit for Agent 1. Each coin is assigned exactly one primary category:
- Layer 1 (L1): base-layer blockchains (BTC, ETH, SOL, ADA, AVAX, etc.)
- Layer 2 (L2): scaling solutions built on top of L1s (MATIC, ARB, OP, etc.)
- DeFi: decentralized finance protocols (UNI, AAVE, CRV, MKR, etc.)
- AI Tokens: blockchain-native AI/compute protocols (FET, RENDER, TAO, etc.)
- Exchange Tokens: centralized or decentralized exchange native tokens (BNB, OKB, CRO, etc.)
- Gaming / Metaverse: blockchain gaming and metaverse assets (AXS, SAND, MANA, etc.)
- Meme Coins: see decision note below

**Meme coin inclusion decision (assumption — requires product sign-off):**
Meme coins (DOGE, SHIB, PEPE, etc.) are included in the candidate universe if they rank within the top 50 by 30-day average market cap. Rationale: excluding them is an arbitrary editorial filter that reduces the accuracy of the top-50 scope claim, and several meme coins have demonstrated sustained momentum signals that are as technically valid as any other asset class. However, Agent 3 rationale generation for meme coins must acknowledge the speculative and sentiment-driven nature of the asset, and the confidence tier ceiling for meme coin candidates is capped at Medium (never High). This is a business logic rule enforced in Agent 3 post-processing. **This decision requires product sign-off before Agent 3 prompt engineering begins.** See Open Question #5.

**Pipeline and intelligence**
- Three-agent AI pipeline (detailed in Section 6)
- Automated orchestration scheduler (detailed in Section 7)
- Candidate Score calculation for each symbol
- Time horizon classification (Short / Medium / Long)
- Plain-English AI rationale for each candidate (50–300 words)

**Dashboard (web application)**
- Ranked candidates table with sortable columns
- Category overview panel (crypto category Momentum Scores, replacing the GICS sector panel)
- Filter controls: time horizon, category, confidence tier
- Candidate detail panel (full rationale, key metrics, scoring breakdown)
- Watchlist (up to 10 symbols, free tier)


**Platform**
- Web application only, responsive design (desktop primary, mobile-friendly)
- No native iOS or Android app

### 5.2 Out of Scope for Phase 1

The following are explicitly excluded. Scope creep into these areas is a launch risk and must be actively managed.

- User authentication of any kind (email + password, Google OAuth, email verification, account management) — moved to Phase 2
- User personalization features (watchlist, saved preferences) — moved to Phase 2
- Email digest and user-targeted notifications — moved to Phase 2
- US equities of any kind (S&P 500, NASDAQ 100, mid-cap) — these belong to Phase 2
- GICS sector ETF data (XLK, XLF, etc.)
- SEC EDGAR Form 4 insider filing data
- Fundamental financial analysis: revenue growth, debt-to-equity ratio, earnings surprises
- Market-hours scheduling logic (not needed — crypto trades 24/7)
- Portfolio tracking or performance history
- Brokerage or exchange API integration (no order placement, no linked accounts)
- Options, futures, perpetual contracts, or any derivative instruments
- Forex and commodities
- Social features (follows, comments, shared watchlists, leaderboards)
- User-visible backtesting or historical performance charts for candidates
- Custom agent configuration or parameter tuning by users
- Real-time price streaming (WebSocket ticker in dashboard)
- Fine-tuned or proprietary LLM (use hosted API only)
- Mobile push notifications
- API access for third-party integrations
- International equities or non-crypto digital assets
- Sell signals of any kind: STI does not generate asset-specific recommendations to exit any position, monitor held positions for exit criteria, or produce ongoing exit signals. A pre-trade planning reference section surfaced at the time of a buy candidate recommendation is explicitly in scope and is not a sell signal (see Section 8.6).

---

## 6. AI Agent Pipeline Architecture

The core intelligence of STI Phase 1 is a three-stage sequential agent pipeline. Each agent has a clearly defined input contract, output schema, and failure behavior. Agents are decoupled — they communicate exclusively through a shared PostgreSQL data store, not direct function calls or message queues.

The Phase 1 pipeline is a simplified, crypto-native version of the Phase 2 pipeline. Eliminating equity-specific inputs (ETF prices, fundamentals, insider filings) and the market-hours scheduling layer makes each agent faster to run, cheaper to operate, and easier to validate.

---

### 6.1 Agent 1: Crypto Category Trend Agent

**Purpose:** Determine which crypto categories are exhibiting positive momentum and therefore warrant deeper analysis in Agent 2. Score all active categories and filter out those in decline to reduce noise downstream.

**Inputs:**
- Price and volume data for the top 50 coins (after stablecoin and duplicate filtering), sourced from CoinGecko API
  - OHLCV data: hourly candles for the last 30 days per coin
  - 24-hour and 7-day price change percentages
  - 24-hour trading volume and 30-day average trading volume
- Crypto news sentiment signals: rolling 24-hour entity-level and category-level sentiment scores derived from financial and crypto-native news headlines (CryptoPanic API or NewsAPI.org with crypto filter)
- Macro signals relevant to crypto: BTC dominance direction (24-hour delta), global crypto market cap direction (24-hour delta), 30-day BTC price trend (as a risk-on/risk-off proxy)

**Category scoring logic:**

For each category, Agent 1 aggregates the coin-level data of all members (weighted by market cap) and computes a Category Momentum Score (0–100):

- **Price momentum component (50% weight):** Weighted average of 7-day price return across category members, normalized to a 0–100 scale relative to the full universe. A category where the median coin is up 20% in 7 days scores near 100; a category where the median coin is down 20% scores near 0.
- **Volume momentum component (35% weight):** Weighted average of (current 24-hour volume / 30-day average daily volume) across category members. A ratio of 1.5x or higher scores near 100; a ratio of 0.5x or lower scores near 0.
- **News sentiment component (15% weight):** Exponentially weighted moving average of category-level sentiment scores over a 72-hour window. Sentiment is sourced from headline-level NLP scores provided by the news API (compound score, -1 to +1), normalized to 0–100.

**Macro adjustment:** If BTC dominance is rising sharply (> 2 percentage points in 24 hours), apply a -10 point adjustment to all non-BTC L1 and altcoin category scores. This captures risk-off rotation back to BTC. If global crypto market cap is declining > 5% in 24 hours, all category scores are floored at max 40 regardless of individual category performance (broad market sell-off signal). Both adjustments are configurable system parameters.

**Output schema:**
```
category_scores: [
  {
    category_id,
    category_name,
    momentum_score,
    avg_7d_price_return_pct,
    avg_volume_ratio,
    sentiment_score,
    coin_count,
    macro_context_applied,
    scored_at
  }
]
```

**Downstream trigger:** Agent 2 is only invoked for categories with Category Momentum Score >= 55. This threshold is lower than the Phase 2 equity equivalent (60) to account for higher crypto volatility — a score of 55 still represents meaningful positive relative momentum in the crypto universe. The threshold is a configurable system parameter (default: 55).

**Failure behavior:** If price data is unavailable for a category (e.g., CoinGecko API outage), that category is scored as null and excluded from Agent 2 input. The pipeline continues with available categories. Agent failure is logged and alerted; the previous valid category scores are retained in cache and served to the dashboard with a staleness indicator.

**Formula weight validation note:** The specific formula weights (50/35/15) are initial recommendations and must be validated by the data science lead before Agent 1 enters production. This is a go/no-go dependency for Agent 1 accuracy. See Open Question #3.

---

### 6.2 Agent 2: Crypto Discovery Agent

**Purpose:** Within categories passing Agent 1's threshold, identify individual coins that meet a quantitative bar for both technical setup and on-chain signal quality. Produce a ranked shortlist of up to 50 candidates for Agent 3's deeper synthesis.

**Inputs:**
- Agent 1 output: categories with Category Momentum Score >= 55
- Price and volume time series for all coins within those categories (from the Phase 1 universe)
- On-chain signals where available (sourced from Glassnode free tier or CoinGecko on-chain metrics): active addresses (7-day trend), exchange net flow (inflow/outflow balance), and large transaction count (7-day trend)
- No fundamental financial data — this layer is explicitly excluded from Phase 1

**Technical filters (all three must pass to be considered a candidate):**

1. **RSI filter:** RSI (14-period, calculated on daily candles) between 40 and 72. Excludes overbought conditions (> 72) and oversold conditions (< 40). The upper bound is set at 72 rather than 70 to account for the fact that crypto assets sustain higher RSI readings for longer during bull runs; this threshold is configurable.

2. **Volume surge filter:** Trailing 5-day average volume >= 1.3x the trailing 30-day average volume. This confirms that the price move has volume backing. The multiplier is 1.3x (vs. 1.5x for equities in Phase 2) because crypto volume is inherently noisier and a lower bar avoids excessive filtering.

3. **Trend filter:** Current price >= the 20-day simple moving average AND >= the 50-day simple moving average. Both conditions must hold. Using two MAs reduces false positives from single-day spikes above a short-term average.

**On-chain signal boost (optional — applied where data is available):**
- If active addresses (7-day trend) are up >= 10% relative to the prior 7-day period: add +5 points to raw Candidate Score
- If exchange net flow is negative (more coins leaving exchanges than entering — a bullish supply signal): add +3 points to raw Candidate Score
- If large transaction count is up >= 20% (whale activity increase): add +4 points to raw Candidate Score
- On-chain data availability varies by coin; this boost is only applied when data is present and flagged in the output. Absence of on-chain data does not penalize the candidate.

**Candidate Score calculation:**
- Technical alignment (50%): composite of RSI positioning (how close to the midpoint of the acceptable range), volume ratio magnitude, and price vs. MA margin
- Category momentum inheritance (35%): the Category Momentum Score from Agent 1, passed through to the candidate
- On-chain signal boost (15%): additive points from the on-chain signals above, normalized to 0–15

**Output:** Up to 50 candidates ranked by Candidate Score. For each candidate:
```
symbol, name, category, candidate_score,
rsi_14d, volume_ratio_5d_30d, price_vs_20d_ma_pct, price_vs_50d_ma_pct,
on_chain_active_addresses_trend, on_chain_exchange_net_flow,
on_chain_large_tx_trend, on_chain_boost_points,
pipeline_run_id, scored_at
```

**Failure behavior:** If fewer than 5 candidates are produced (e.g., broad crypto market downturn passes few filters), Agent 2 outputs what it has. Agent 3 is still invoked. The dashboard shows a "Low signal environment" notice when fewer than 5 candidates are present.

---

### 6.3 Agent 3: Forward-Looking Synthesis Agent

**Purpose:** For each candidate passing Agent 2, generate a forward-looking investment thesis using an LLM. Classify the time horizon, assign a confidence tier, and produce a plain-English rationale. Output the final ranked list of up to 25 candidates.

**Inputs:**
- Agent 2 output: up to 50 candidates with scoring data
- Recent news headlines and summaries for each symbol (last 48 hours, top 5 by relevance, sourced from CryptoPanic or NewsAPI)
- Protocol/ecosystem news: any major on-chain events, mainnet launches, token unlock schedules, governance votes flagged in the last 7 days (sourced from CoinGecko events API or equivalent)
- Macro context summary: a brief structured summary generated from Agent 1's macro signals (BTC dominance trend, global market cap trend, category-level momentum context)

**LLM prompt contract:**

Each symbol is processed with a structured prompt containing:
1. Symbol metadata (name, category, market cap rank)
2. Key quantitative signals (RSI, volume ratio, price vs. 20d/50d MA, Candidate Score, on-chain boost points and their sources)
3. Top 5 recent news headlines with source and date
4. Any protocol events from the past 7 days
5. Macro context summary
6. Instruction to produce: a time horizon classification (Short/Medium/Long), a confidence tier (High/Medium/Low), and a 50–300 word rationale explaining the opportunity in plain English, citing at least one technical signal, one narrative signal (news, protocol event, or category momentum), and — if available — one on-chain signal

**Time horizon definitions:**
- Short: 1–7 days. Primarily driven by technical setup, volume surge, or near-term catalyst (e.g., upcoming token unlock, exchange listing, protocol launch).
- Medium: 1–4 weeks. Combination of technical trend, category momentum, and sustained narrative catalyst.
- Long: 1–3 months. Primarily driven by category-level structural tailwind, ecosystem growth signals, or sustained institutional narrative (e.g., ETF narrative, regulatory clarity, L2 adoption curve).

Note: Crypto time horizons are compressed relative to equities. The Phase 2 PRD uses 1–14 days for Short and 3–6 months for Long. Crypto moves faster; these definitions are calibrated accordingly.

**Confidence tier definitions:**
- High: >= 3 supporting signals across technical, narrative, and on-chain dimensions, with no significant conflicting indicators identified. Meme coin candidates are never eligible for High (see Section 5.1).
- Medium: 2 supporting signals, or 3 supporting signals with at least one conflicting indicator (e.g., strong price momentum but declining on-chain activity).
- Low: 1–2 supporting signals, or any candidate where the LLM identifies a meaningful risk factor (e.g., upcoming large token unlock, regulatory news, declining developer activity).

**Final ranking logic:**
- Primary sort: Candidate Score (descending)
- Secondary sort: Confidence tier (High > Medium > Low)
- Maximum output: 25 candidates per full pipeline run. This is lower than Phase 2's 30 because the crypto universe is smaller (top 50 vs. ~560 equities + 50 crypto) and producing more than 25 candidates from a pool of ~50 (after stablecoin removal) would be sampling too high a percentage of the universe with insufficient selectivity.
- Deduplication: wrapped token equivalents (e.g., WBTC and BTC both passing) are deduplicated at this stage; the higher-scored version is retained.

**Output schema:**
```
candidates: [
  {
    symbol, name, category,
    candidate_score, confidence_tier, time_horizon,
    rationale_text, key_signals: [...],
    on_chain_signals_used: [...],
    last_news_headline,
    protocol_event_flag,
    is_meme_coin,
    pipeline_run_id, generated_at
  }
]
```

**LLM provider:** Anthropic Claude API (claude-sonnet-4 as default; evaluate claude-opus-4 for quality improvement vs. cost). A structured side-by-side evaluation of Anthropic Claude and OpenAI GPT-4o must be completed against a test set of 20 candidate crypto assets before selecting the production provider. Evaluation criteria: rationale quality (human-rated by at least 2 reviewers), adherence to output schema, time horizon accuracy relative to market outcomes (where testable), latency, and cost per 1,000 candidates processed.

**Cost control:** Agent 3 is rate-limited to 6 full pipeline runs per day (every 6 hours = 4 scheduled runs, plus 2 buffer for event-triggered runs). Partial re-runs triggered by category events process only affected-category candidates. See Section 7 for scheduling details.

**Failure behavior:** If the LLM API call fails for a candidate, that candidate is dropped from the output (not surfaced with a blank rationale). If more than 8 candidates fail in a single run, the run is flagged as degraded and the previous successful output is served with a staleness indicator. The 8-candidate threshold is chosen because losing more than roughly 30% of the expected 25-candidate output materially degrades the product experience.

---

### 6.4 Entry Classification Definitions (Agent 3 Business Rules)

Agent 3 classifies each candidate by entry type and entry quality, enriching the candidate output with transparent technical context that users can validate and apply to their own trading decisions.

**Entry Type Definitions**

Three mutually exclusive entry type classifications, determined by technical conditions at the time Agent 3 processes the candidate:

| Entry Type | Technical Conditions |
|---|---|
| **Breakout** | Closing price >= highest close in prior 20 sessions; breakout session volume >= 2x 30-day average; RSI advancing from above 50; price represents new price discovery (not a return to a prior high) |
| **Retest** | A prior resistance level has been broken; current price is within 3–5% above that level (which now acts as support); pullback volume declining vs. the breakout session; RSI between 45–55 |
| **Dip-Buy** | Price >= 50d SMA by >= 10% (established uptrend); current price has pulled back to within 5–8% of the 20d SMA or a known support zone; RSI declined to 40–55 range; pullback volume declining |

If no clear entry type pattern applies, classify as Retest (the most common setup in trending crypto markets). The entry type is surfaced in the candidate detail panel to help traders contextualize the technical setup.

**Entry Quality Tiers**

Entry quality reflects the strength of supporting evidence across technical, narrative, and on-chain dimensions. The tiers directly map to the existing confidence tier system and formalize the technical criteria underlying those confidence assignments.

| Quality Tier | Technical Criteria | Maps To |
|---|---|---|
| **Strong** | RSI 52–65; volume ratio >= 2.0x 30-day average; price >= 20d SMA by >= 5%; at least one on-chain signal confirmed (active addresses, exchange flow, or whale activity) | High confidence |
| **Moderate** | RSI 45–71; volume ratio 1.5–2.0x 30-day average; price >= both 20d and 50d SMA within 5% margin; on-chain data optional | Medium confidence |
| **Speculative** | RSI at extremes (40–45 or 68–72); volume ratio 1.3–1.5x 30-day average; barely above one or both MAs; no on-chain data or conflicting on-chain signals | Low confidence |

**Implementation note:** Entry quality tiers are not an additional classification layer imposed on users — they are the explicit technical criteria underlying the existing confidence tier system. Surfacing them increases transparency and allows traders to validate the AI's confidence assignment against their own technical analysis.

**Agent 3 prompt contract additions**

Agent 3 production instructions are updated to include:
1. Classify the entry type as one of: Breakout, Retest, or Dip-Buy using the criteria above.
2. Confirm that the entry quality tier mapping aligns with the assigned confidence tier. (This is a validation check, not a separate classification.)
3. In the rationale text, include one sentence identifying the nearest prior resistance zone and one sentence identifying the level at which the current technical setup would be considered invalidated. Use this framing: *"The [level] area represents prior resistance that may function as a natural reference point for planning purposes"* and *"A closing price below [level] would technically invalidate the current setup."*
4. Populate the `pre_trade_reference` object in the output schema (see updated schema below).

**Updated Agent 3 output schema**

Add the following fields to each candidate in the Agent 3 output:

```
candidates: [
  {
    symbol, name, category,
    candidate_score, confidence_tier, time_horizon,
    rationale_text, key_signals: [...],
    on_chain_signals_used: [...],
    entry_type,                        // "Breakout" | "Retest" | "Dip-Buy"
    entry_quality,                     // "Strong" | "Moderate" | "Speculative"
    pre_trade_reference: {
      nearest_resistance_zone,         // e.g., "$2.45–$2.55 area (prior rejection high)"
      technical_invalidation_zone,     // e.g., "Below $2.10 (prior swing low)"
      atr_14d_approx,                  // e.g., "$0.18" — 14-day Average True Range
      min_rr_for_horizon,              // e.g., "2.0:1" — minimum risk-to-reward for this time horizon
    }
  }
]
```

---

## 7. Orchestration and Scheduling

The Phase 1 orchestration layer is materially simpler than Phase 2 because crypto trades 24/7. There is no market open/close logic, no market-hours-conditional scheduling, and no earnings calendar polling. All runs follow time-based cadences or crypto-native event triggers.

### 7.1 Standard Scheduled Runs

| Schedule | Trigger | Agents Invoked | Scope | Notes |
|---|---|---|---|---|
| Every 6 hours, 24/7 (00:00, 06:00, 12:00, 18:00 UTC) | Cron | 1 → 2 → 3 (full) | All categories, full crypto universe | Primary full-pipeline cadence |
| Every hour, 24/7 | Cron | 1, then 2 conditionally | All categories | Light refresh; see conditional logic below |
| Daily, 06:45 UTC | Cron | Email digest trigger only | Uses previous 06:00 UTC Agent 3 output | Targets 7:00 AM ET for US users |

**Conditional logic for hourly lightweight runs:**

Agent 2 is only re-invoked during an hourly run if at least one category's Momentum Score has shifted by >= 12 points relative to the previous hourly run. The threshold is 12 points (vs. 15 for equities in Phase 2) because crypto categories move faster and a lower delta threshold catches meaningful shifts sooner. If no category exceeds this delta, Agent 1 data is updated in the store but Agent 2 and Agent 3 are not re-invoked.

Agent 3 is never invoked on hourly runs unless the run is also classified as event-triggered (see Section 7.2).

The dashboard reflects Agent 1 category score updates from each hourly run. The ranked candidates table reflects the last Agent 3 full pipeline run.

### 7.2 Event-Triggered Runs

The following events trigger an out-of-schedule full pipeline run:

| Event | Detection Method | Agents Invoked | Notes |
|---|---|---|---|
| BTC flash crash or spike | BTC 1-hour price change >= +/- 8% | 1 → 2 → 3 (full) | Counts against daily Agent 3 run limit |
| Category-level volume explosion | Any category's volume ratio exceeds 3x 30-day average | 1 → 2 → 3 (category-scoped) | Common in crypto during protocol launches or airdrops |
| Major news spike | CryptoPanic importance score "hot" for any top-50 coin held for >= 30 minutes | 2 → 3 (coin-scoped) | Limited to coins already in the top-50 universe |
| Protocol event trigger | Mainnet launch, major token unlock, or exchange listing for a top-50 coin, flagged via CoinGecko events API | 2 → 3 (coin-scoped) | Protocol events are often the most important crypto catalyst |

**Event run limits:** Event-triggered Agent 3 invocations count toward a daily cap of 6 total Agent 3 runs. If the cap is reached, further event triggers queue and execute at the next scheduled 6-hour window. Agent 1 and Agent 2 have no hard daily cap but must not be invoked more than once per 15 minutes.

**BTC dominance shift handling:** A rapid BTC dominance shift (> 3 percentage points in 4 hours) does not trigger a full pipeline run but updates the macro adjustment parameters in the store, which propagate to the next hourly Agent 1 run. This avoids over-running Agent 3 during large BTC dominance rotations, which are frequent and often reverse.

### 7.3 Pipeline State and Output Freshness

- The PostgreSQL store records the timestamp of every pipeline run per agent.
- Redis caches the final Agent 3 output (ranked candidates list) with a TTL of 90 minutes.
- The dashboard always reads from Redis cache. Cache miss falls back to PostgreSQL.
- The dashboard displays a "Last updated" timestamp and a staleness banner if the Agent 3 output is older than 7 hours. Since crypto runs 24/7, the staleness threshold is not time-of-day conditional (unlike the Phase 2 PRD's market-hours vs. after-hours distinction).
- The staleness banner text: "Analysis last updated [timestamp]. Next scheduled update in approximately [X] hours."

### 7.4 Infrastructure for Scheduling

- AWS EventBridge (or equivalent) for cron-based triggers
- AWS ECS Fargate tasks (or equivalent) for stateless agent execution
- Each agent runs as an independent container; the orchestrator invokes them sequentially and passes the run ID as the coordination key
- Dead-letter queue (SQS DLQ or equivalent) for failed pipeline run notifications to engineering on-call

---

## 8. MVP Functional Requirements

Requirements are organized by feature area. Each includes the user story, acceptance criteria, and MoSCoW priority. All Must Have requirements must be complete and passing acceptance criteria before Phase 1 is declared launch-ready.

---

### 8.1 Ranked Candidates Dashboard

**Priority: Must Have**

**User Story — Main Table:**
As a crypto trader, I want to see a ranked table of AI-identified buy candidates so that I can quickly evaluate which assets are worth my attention right now.

**Acceptance Criteria:**
- Given a visitor on the dashboard, when the page loads, then a table of ranked candidates is displayed within 3 seconds (p95) sourced from the Redis cache.
- Given the candidates table, when it renders, then it displays at minimum: rank, symbol, name, category, time horizon, confidence tier, candidate score, and last-updated timestamp for each row.
- Given the table, when a visitor clicks any column header (rank, score, time horizon, confidence), then the table sorts by that column ascending or descending.
- Given a visitor, when the Agent 3 output is older than 7 hours, then a yellow staleness banner is displayed above the table: "Analysis last updated [timestamp]. Next scheduled update in approximately [X] hours."
- Given a visitor, when fewer than 5 candidates are in the current output, then a blue "Low signal environment" notice is displayed explaining that current market conditions have reduced the candidate pool.
- Given the table with more than 25 rows (should not occur in MVP scope, but defensively handled), when it renders, then it is paginated at 25 rows per page.

---

**User Story — Candidate Detail Panel:**
As a crypto trader, I want to click on a candidate to see the full AI-generated rationale and supporting data so that I can decide whether to investigate it further.

**Acceptance Criteria:**
- Given a visitor clicking any row in the candidates table, when the click registers, then a detail panel (drawer or modal) opens within 500ms displaying: symbol, name, category, full rationale text, time horizon, confidence tier, candidate score breakdown, key signals (RSI, volume ratio, price vs. 20d/50d MA), on-chain signals used in scoring (labeled as unavailable if data was not present), last relevant news headline with link, and any protocol event flag.
- Given the detail panel, when the rationale text is displayed, then the per-rationale disclaimer and the crypto-specific disclaimer (see Section 12.2) are displayed directly below the rationale in a visually distinct style (muted color, smaller font).
- Given the detail panel, when a visitor clicks outside the panel or presses Escape, then the panel closes and the table returns to the same scroll position.
- Given a candidate flagged as a meme coin, when the detail panel opens, then the confidence tier is displayed as "Medium (max)" with a tooltip explaining that meme coin candidates are capped at Medium confidence.

---

**User Story — Category Overview Panel:**
As a crypto trader, I want to see which crypto categories are trending before reviewing individual candidates so that I can understand the market-level context.

**Acceptance Criteria:**
- Given a visitor on the dashboard, when the category overview panel is visible, then all active crypto categories are displayed with their current Category Momentum Score (0–100) and a directional indicator (up/down/flat vs. previous hourly run).
- Given a category with Momentum Score >= 55, when displayed, then it is visually highlighted (e.g., green accent) to indicate it passed the Agent 2 threshold.
- Given a visitor clicking a category in the overview panel, when the click registers, then the candidates table is filtered to show only candidates from that category.
- Given a category where the macro adjustment (broad market sell-off floor of 40) has been applied, when displayed, then the macro adjustment is indicated visually (e.g., an info icon with tooltip: "Score adjusted for broad market conditions").

---

**User Story — Filter Controls:**
As a crypto trader, I want to filter the candidates list by time horizon, category, and confidence so that I can focus on the type of opportunity I am looking for.

**Acceptance Criteria:**
- Given the filter control bar, when rendered, then it contains: time horizon filter (All / Short / Medium / Long), category filter (All / Layer 1 / Layer 2 / DeFi / AI Tokens / Exchange Tokens / Gaming-Metaverse / Meme Coins), and confidence filter (All / High / Medium / Low).
- Given any filter selection, when applied, then the table updates within 300ms (client-side filter, no server round-trip).
- Given multiple filters selected simultaneously, when applied, then the table shows only candidates matching all selected filter values (AND logic).
- Given a visitor resetting all filters, when they click "Clear filters", then all filters return to "All" and the full ranked list is restored.
- Given an active filter that produces zero results, when applied, then the table displays "No candidates match these filters" and the clear filters control remains accessible.

---

### 8.2 Pipeline Monitoring (Internal / Admin)

**Priority: Must Have**

**User Story:**
As an engineer or product team member, I want to see the status of each pipeline run so that I can detect and diagnose failures without manually querying the database.

**Acceptance Criteria:**
- Given any pipeline run completing (successfully or with errors), when it completes, then a run log entry is written to the database recording: run ID, agents invoked, start time, end time, trigger type (scheduled/event), number of categories processed, number of candidates output by Agent 2, number of candidates output by Agent 3, and any error codes.
- Given a pipeline run where any agent fails entirely, when the failure occurs, then an alert is sent to the engineering on-call channel (Slack or PagerDuty equivalent) within 5 minutes.
- Given an internal admin dashboard (basic, not customer-facing), when accessed by an authenticated admin user, then it displays the last 48 hours of pipeline run logs in a table with the fields above, and highlights failed runs in red. (48 hours is used instead of Phase 2's 24 hours because 24 hours covers only 4 scheduled runs; 48 hours provides more diagnostic context for the denser crypto cadence.)
- Given the admin dashboard, when an admin views a failed run, then they can see the error message and the last successfully cached Agent 3 output timestamp.
- Given the admin dashboard, when an admin views the current pipeline state, then they can see the current Category Momentum Scores from the most recent Agent 1 run and identify which categories are above and below the Agent 2 threshold.

---

### 8.3 Legal Disclaimer and Disclosure

**Priority: Must Have**

**Acceptance Criteria:**
- Given any visitor viewing the homepage, marketing pages, or dashboard, when the page renders, then the full disclaimer (see Section 12.2) is displayed in the page footer and on any page that describes the product's analysis capabilities.
- Given a visitor viewing the dashboard for the first time, when the page loads, then a prominent disclaimer modal is displayed containing the full disclaimer plus the crypto-specific addendum. The user may dismiss it by clicking "I understand" or clicking outside the modal.
- Given any candidate detail panel, when displayed, then both the per-rationale disclaimer and the crypto-specific addendum are visible without scrolling within the panel.

---

### 8.4 Responsive Web Application

**Priority: Should Have**

**Acceptance Criteria:**
- Given a visitor accessing the dashboard on a desktop viewport (>= 1024px width), when the page renders, then the category overview panel, candidates table, and filter controls are all visible without horizontal scrolling.
- Given a visitor accessing the dashboard on a tablet viewport (768px – 1023px), when the page renders, then the layout adapts: the category overview panel collapses to a scrollable horizontal row of category chips, and the table remains functional with at least 5 columns visible.
- Given a visitor accessing the dashboard on a mobile viewport (< 768px), when the page renders, then the table is readable with rank, symbol, time horizon, and confidence visible; other columns are accessible via horizontal scroll or collapsed into the detail panel.
- Given any viewport, when a visitor taps a table row on a touch device, then the detail panel opens with the same behavior as a click on desktop.

---

### 8.5 Performance and Loading States

**Priority: Should Have**

**Acceptance Criteria:**
- Given a visitor loading the dashboard, when the page is loading, then skeleton loaders are displayed for the table and category panel before data arrives. A blank white screen with no loading indicator is not acceptable.
- Given the dashboard table, when data has loaded, then the Largest Contentful Paint (LCP) is <= 2.5 seconds on a simulated fast 4G connection.
- Given the dashboard table, when data has loaded, then the Cumulative Layout Shift (CLS) score is <= 0.1.

---

### 8.6 Pre-Trade Planning Reference

**Priority: Should Have** (does not block Phase 1 launch; enhances candidate detail panel with educational context)

**User Story:**
As a crypto trader who decides to act on an STI buy candidate, I want to see the technical reference points relevant to this specific setup — the nearest resistance zone, the technical invalidation level, the 14-day ATR, and the risk-to-reward context for the assigned time horizon — so that I can structure my own trade plan before entering.

**Acceptance Criteria:**
- Given a visitor opening the candidate detail panel, when the panel loads, then a section labeled "Pre-Trade Planning Reference (Educational Context)" is displayed below the main rationale. The section contains: entry type label (Breakout / Retest / Dip-Buy), entry quality label (Strong / Moderate / Speculative, mapped from confidence tier), nearest resistance zone (described in plain text, e.g., "$2.45–$2.55 area (prior rejection high)"), technical invalidation zone (plain text, e.g., "Below $2.10 (prior swing low)"), current 14-day ATR approximation (displayed as a currency value), and minimum risk-to-reward context for the assigned time horizon (displayed as a ratio, e.g., "2.0:1").
- Given the pre-trade reference section, when displayed, then a section-level disclaimer is rendered: "These are general technical reference points for pre-trade planning. They are not recommendations to buy, sell, or hold this asset. All trading decisions are the trader's sole responsibility."
- Given a Low confidence / Speculative quality candidate, when the detail panel displays, then the pre-trade reference section includes a prominent note: "This candidate has limited signal support. Technical invalidation levels for speculative setups may be triggered frequently during normal market volatility; size positions accordingly."
- Given a meme coin candidate, when the detail panel opens, then the pre-trade reference section header adds: "(Meme assets: technical levels are less reliable due to sentiment-driven price action)"
- Given the pre-trade reference section, when displayed on any viewport, then the content is visually distinct from the main rationale (e.g., lighter background color, bordered container, smaller font size) to reinforce that it is supplemental educational context, not the primary investment signal.

---

## 9. Post-MVP Roadmap

### Phase 2 — User Accounts + US Equities Addition (Target: 3–5 months post Phase 1 launch, contingent on 60-day go/no-go)

Phase 2 adds two major features deferred from Phase 1: (1) user authentication and personalization, and (2) US equities analysis. Phase 2 expands STI from crypto-only to the combined asset universe described in the full Phase 2 PRD (PRD-v1.0.md). All Phase 1 architecture decisions are made with Phase 2 compatibility in mind. Key additions:

**User authentication and personalization**
- Email + password authentication with email verification
- Google OAuth (Sign in with Google)
- Basic account management (email, password change)
- Watchlist (up to 10 symbols for free tier, unlimited for paid)
- Daily email digest (7 days/week for crypto, weekdays-only for equities)

**Asset universe expansion**
- S&P 500 + NASDAQ 100 constituents (approximately 560 unique symbols)
- Equity data provider integration: Polygon.io or Alpaca Markets

**Agent pipeline additions**
- Agent 1 extended: adds 11 GICS sector ETF inputs (XLK, XLF, XLV, etc.), macro signals (VIX, 10-year Treasury yield, DXY)
- Agent 2 extended: adds fundamental overlay (revenue growth, D/E ratio, earnings surprises) and insider signal boost (SEC EDGAR Form 4 filings)
- Agent 3 extended: adds earnings calendar, analyst rating changes, equity-specific time horizon calibration (longer horizons than crypto)

**Orchestration changes**
- Adds market-hours scheduling logic (equity pipeline active 9:30 AM – 4:00 PM ET, weekdays only)
- Adds event-triggered runs for FOMC announcements, earnings surprises, and macro shocks

**Dashboard changes**
- Asset class filter added (All / Equities / Crypto)
- GICS sector overview panel added alongside the crypto category panel
- Candidate detail panel extended with equity-specific fields (fundamentals, insider signal, next earnings date)

**Cost implications:** Adding equities increases estimated monthly data cost from $150–$380 (Phase 1) to $650–$1,980 (Phase 2). See Phase 2 PRD Section 10.3 for data source cost breakdown.

**Go/no-go gate:** Phase 2 engineering investment is contingent on Phase 1 meeting at least 3 of the 4 success metrics at the 60-day review. If Phase 1 does not achieve product-market fit in crypto, building Phase 2 on top of a weak foundation is not justified.

### Phase 3 — Depth, Monetization, and Scale (Target: 6–12 months post Phase 1 launch)

Refer to Phase 2 PRD Section 9 (Phase 3) for the full roadmap including: paid subscription tier, sell signals, candidate score explainability, historical candidate archive, alert preferences, expanded universe (crypto top 200), and user-facing performance dashboard.

---

## 10. High-Level Technical Architecture

### 10.1 Component Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Layer                               │
│              Browser (Next.js/React)                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Application Layer                          │
│   Next.js API Routes / REST API (public endpoints)              │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌─────────────────────┐         ┌─────────────────────────────┐
│   Redis Cache        │         │   PostgreSQL (primary store) │
│   (candidates list, │         │   (pipeline runs, scores,    │
│    TTL 90 min)       │         │    users, watchlists, logs)  │
└─────────────────────┘         └─────────────────────────────┘
                                              │
                              ┌───────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Agent Pipeline Layer                        │
│                                                                 │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────┐   │
│  │  Agent 1     │──▶│  Agent 2     │──▶│  Agent 3         │   │
│  │  Crypto      │   │  Crypto      │   │  Forward-Looking  │   │
│  │  Category    │   │  Discovery   │   │  Synthesis (LLM)  │   │
│  │  Trend       │   │              │   │                  │   │
│  └──────────────┘   └──────────────┘   └──────────────────┘   │
│                                                                 │
│  Orchestrator (EventBridge + ECS Fargate tasks)                │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                      Data Source Layer                          │
│                                                                 │
│  CoinGecko API (price, volume, market cap, events)             │
│  Glassnode Free Tier / CoinGecko on-chain (on-chain signals)   │
│  CryptoPanic API / NewsAPI.org (news + sentiment)              │
│  Anthropic Claude API / OpenAI GPT-4o (rationale generation)   │
└─────────────────────────────────────────────────────────────────┘
```

**Key simplification vs. Phase 2:** The data source layer is entirely crypto-native. There is no Polygon.io equity feed, no FMP fundamentals endpoint, and no SEC EDGAR integration. This removes the two highest-cost data sources and the most complex data licensing questions from Phase 1.

### 10.2 Technology Stack

| Layer | Technology | Rationale |
|---|---|---|
| Frontend | Next.js (React) | SSR for SEO on marketing pages, CSR for dashboard interactivity; strong ecosystem; same choice as Phase 2 to minimize migration cost |
| API | Next.js API routes | Consolidate with frontend for Phase 1 MVP; extract to dedicated FastAPI service if latency or agent complexity requires it in Phase 2 |
| Primary database | PostgreSQL (managed: Supabase preferred for Phase 1, migrate to AWS RDS for Phase 2 if scale requires) | Supabase offers lower operational overhead for a small team at Phase 1 scale; Phase 2 will add Auth.js for user authentication |
| Cache | Redis (managed: Upstash preferred for Phase 1) | Low-latency cache for dashboard reads; serverless pricing model suits Phase 1 usage volume |
| Agent runtime | Python 3.11+ | Strong data science and LLM SDK ecosystem |
| Agent packaging | Docker containers on AWS ECS Fargate | Stateless execution; no server management; pay-per-use |
| Scheduler | AWS EventBridge (cron rules) | Native AWS cron integration with ECS |
| Email | SendGrid | Preferred for template management and deliverability tooling; simpler setup than AWS SES for Phase 1 volume |
| LLM API | Anthropic Claude API (primary) | See Section 6.3 for evaluation requirement |
| Monitoring | AWS CloudWatch + Slack webhook for alerts | Lightweight for Phase 1; evaluate Datadog in Phase 2 |

### 10.3 Data Source Specifications

| Source | Data Type | Provider | Fallback | Est. Monthly Cost | Update Frequency |
|---|---|---|---|---|---|
| Crypto price / volume / market cap | OHLCV, 24h change, volume, rankings | CoinGecko Pro API | CoinMarketCap | $0–$130 | Hourly (Pro plan) |
| Crypto on-chain signals | Active addresses, exchange flows, large tx | Glassnode (free tier) | CoinGecko on-chain (where available) | $0 (free tier) | Daily |
| Crypto news + sentiment | Headlines, summaries, importance scores | CryptoPanic API | NewsAPI.org (crypto filter) | $0–$50 | Near-real-time |
| Protocol events | Mainnet launches, token unlocks, listings | CoinGecko Events API | Manual curation for top-10 coins | $0 (included in CoinGecko Pro) | Daily |
| LLM rationale generation | Agent 3 synthesis | Anthropic Claude API | OpenAI GPT-4o | $50–$200 | Per-run (6x/day) |

**Total estimated data + LLM cost at Phase 1 launch volume:** $50–$380/month. Budget should be planned at $500/month with headroom. This is a 75–80% cost reduction vs. Phase 2's $650–$1,980/month estimate, validating the Phase 1 scoping decision.

**Important assumption:** CoinGecko Pro plan is required for hourly data granularity. The free tier is rate-limited to ~30 calls/minute and does not support the hourly OHLCV endpoint at the volume required for top-50 coverage. Confirm plan tier and pricing before development begins (see Open Question #4).

### 10.4 Data Storage Schema (Key Tables)

**pipeline_runs** — One row per agent invocation
```
run_id, agent_id, trigger_type, started_at, completed_at, status,
categories_processed, candidates_in, candidates_out, error_code, error_message
```

**category_scores** — Agent 1 output, one row per category per run
```
run_id, category_id, category_name, momentum_score,
avg_7d_price_return_pct, avg_volume_ratio, sentiment_score,
macro_context_applied, macro_adjustment_applied, scored_at
```

**candidates** — Agent 3 final output, one row per candidate per run
```
run_id, symbol, name, category_id, candidate_score,
confidence_tier, time_horizon, rationale_text,
key_signals_json, on_chain_signals_json,
last_news_headline, protocol_event_flag, is_meme_coin,
generated_at
```

**Schema design note:** Phase 1 is a public, unauthenticated dashboard with no user data storage. User accounts and personalization (watchlists, email preferences) are deferred to Phase 2. The schema above supports the entire Phase 1 pipeline and display layer.

---

## 11. Non-Functional Requirements

### 11.1 Performance

| Requirement | Target | Measurement Method |
|---|---|---|
| Dashboard initial load (authenticated) | p95 <= 3 seconds | Synthetic monitoring, Lighthouse |
| Candidate table render (data already cached) | p95 <= 500ms | Browser performance API |
| Client-side filter application | <= 300ms | Browser performance API |
| Detail panel open | <= 500ms | Browser performance API |
| Redis cache read latency | p99 <= 20ms | CloudWatch / Upstash metrics |
| Agent 1 full run time (all categories) | <= 8 minutes | Pipeline run log |
| Agent 2 full run time (passing categories) | <= 10 minutes | Pipeline run log |
| Agent 3 full run time (25 candidates) | <= 20 minutes | Pipeline run log |
| Full pipeline (Agent 1 → 2 → 3) | <= 40 minutes end-to-end | Pipeline run log |
| Email digest delivery | Within 15 minutes of 06:45 UTC trigger | Email provider delivery report |

Agent pipeline times are faster than Phase 2 targets because Phase 1 has fewer data sources, a smaller universe, and no fundamental data fetching.

### 11.2 Availability and Reliability

| Requirement | Target |
|---|---|
| Web application uptime | >= 99.5% monthly (allows ~3.6 hours downtime/month) |
| Pipeline success rate | >= 95% of scheduled full pipeline runs complete without degraded output |
| Graceful degradation | If Agent 3 output is stale, the previous valid output must be served with the staleness banner. The application must never show an empty candidates table to an authenticated user unless no output has ever been generated. |
| Database backups | Automated daily backups with 7-day retention (Supabase managed in Phase 1) |
| Recovery time objective (RTO) | <= 2 hours for any single-component failure |

### 11.3 Security

| Requirement | Specification |
|---|---|
| HTTPS | HTTPS enforced site-wide; TLS 1.2+ for all connections |
| Rate limiting | Public API endpoints: 100 requests/minute per IP to prevent abuse; rate limit headers included in all responses |
| Data in transit | TLS 1.2+ enforced for all connections including database and cache connections |
| Data at rest | Database encryption enabled (Supabase managed encryption); all third-party API keys stored in secrets manager (AWS Secrets Manager), never in environment variables or version control |
| PII handling | Phase 1 collects no user PII (no email, no accounts). Analytics data (visitor IP, device type, dashboard interactions) are not PII and may be logged per analytics provider's policy. |
| Third-party API security | All API keys (CoinGecko, CryptoPanic, Anthropic, etc.) stored in AWS Secrets Manager with least-privilege access; keys rotated quarterly |
| Dependency scanning | All npm/Python dependencies scanned for known vulnerabilities via automated tools (e.g., npm audit, safety); no high/critical CVEs in production dependencies |

### 11.4 Scalability

Phase 1 does not need to be built for massive scale, but architectural choices must not create ceilings below 10,000 daily active visitors.

- PostgreSQL (Supabase) with connection pooling handles Phase 1 load without schema changes; the data store contains only pipeline results, not user data.
- Redis absorbs dashboard read load; horizontal scaling of the Next.js application (Vercel or ECS) handles web traffic increases.
- The agent pipeline runs on a fixed cadence independent of dashboard traffic; vertical scaling of Fargate task CPU/memory handles pipeline growth.
- The schema is designed for Phase 2 compatibility from day one (see Section 10.4) — adding user accounts and equities in Phase 2 is an extension, not a redesign.

### 11.5 Accessibility

- The web application must achieve WCAG 2.1 Level AA compliance for the dashboard, disclaimer modal, and all interactive elements.
- Minimum contrast ratio: 4.5:1 for normal text, 3:1 for large text.
- All interactive elements must be keyboard-navigable.
- The candidates table must have appropriate ARIA roles and labels for screen reader compatibility.

### 11.6 Data Freshness and Display

- Every data point displayed to the user (category score, candidate score, rationale) must have an associated timestamp visible in the UI.
- The dashboard must never display analysis without indicating when it was generated.
- "Real-time" or "live" must not be used in any UI copy unless price data is updated within 5 minutes. CoinGecko Pro data is typically updated every 1–5 minutes at the Pro tier; confirm refresh rate before using "live" in any copy.

---

## 12. Legal, Compliance, and Disclaimers

This section is high-priority. Crypto analysis carries its own distinct regulatory considerations that are in some ways more complex than equities. Legal review is a hard go/no-go blocker. Do not launch without written legal sign-off on each item in Section 12.1.

### 12.1 Regulatory Classification

**The investment advice question (general):** The analysis in Phase 2 covering securities requires evaluation under the Investment Advisers Act of 1940. Phase 1 is crypto-only, but this does not simplify the regulatory question — it shifts it.

**Crypto-specific regulatory considerations:**

1. **Securities classification of crypto assets:** Some cryptocurrencies have been classified or are at risk of classification as securities by the SEC (most notably XRP, but the debate extends to many altcoins). If STI produces buy-candidate output for a coin that is later classified as a security, and STI has not registered as an RIA, this creates retroactive regulatory exposure. **Legal counsel must provide guidance on which, if any, top-50 coins create elevated securities-classification risk and whether those coins should be excluded from the Phase 1 universe.**

2. **CFTC jurisdiction:** Certain cryptocurrencies (BTC, ETH) have been treated as commodities under CFTC jurisdiction. Analysis of commodity derivatives can require different registrations than securities analysis. Phase 1 covers spot assets only (no futures, no perpetuals), which reduces but may not eliminate this concern.

3. **State money transmission laws:** STI does not transmit funds or custody assets, so money transmission licensing should not apply. Confirm with counsel.

4. **Position (to be validated by counsel):** STI's crypto analysis is general-purpose market analysis content, not personalized investment advice, because: (a) output is identical for all users (no individualization), (b) STI does not provide position sizing, portfolio allocation, or dollar-amount guidance, and (c) prominent disclaimers make the non-advisory nature clear. The crypto-specific addendum strengthens the disclaimer posture.

**Legal counsel must confirm or refute this position in writing, with specific attention to crypto asset securities classification risk, before launch.**

### 12.2 Required Disclaimers

The following disclaimer text is required on all specified surfaces. No paraphrasing without legal review of the revised text.

**Full disclaimer (footer, disclaimer modal):**
> "Sentics Trading Intelligence provides AI-generated market analysis for informational purposes only. This is not investment advice. Sentics is not a registered investment advisor. The information provided is not a recommendation to buy, sell, or hold any security or cryptocurrency. Markets are volatile and investments carry risk of loss, including total loss of principal. Always conduct your own research and consult a qualified financial professional before making any investment decisions. AI-generated analysis may contain errors. Past candidate performance is not a guarantee of future results."

**Per-rationale disclaimer (candidate detail panel):**
> "This analysis is generated by artificial intelligence and is not financial advice. Past performance is not indicative of future results."

**Crypto-specific addendum (required on all surfaces that display crypto analysis, including the detail panel and disclaimer modal):**
> "Cryptocurrency assets are not regulated securities in most jurisdictions. Crypto markets operate 24/7 and are subject to extreme volatility, low liquidity in smaller assets, and rapid price swings. The regulatory status of specific cryptocurrencies may be subject to change. You may lose your entire investment. This analysis does not account for your personal financial situation, risk tolerance, or tax obligations. Crypto assets mentioned may be subject to securities classification by regulatory authorities; consult a qualified legal and financial advisor before investing."

**Pre-Trade Planning Reference disclaimer (candidate detail panel, pre-trade reference section only):**
> "The pre-trade planning references on this page are general technical context provided for educational purposes at the time of this analysis. They represent reference points derived from historical price levels and standard technical analysis frameworks. They are not recommendations to buy or sell this asset. These levels may change materially as market conditions evolve. All decisions about entering, sizing, and exiting any position are solely the trader's responsibility. This information does not constitute investment advice."

**Emphasis note:** The crypto-specific addendum is more prominent in Phase 1 than it was in the Phase 2 PRD (where it appeared as one of three disclaimers). Since Phase 1 is 100% crypto, this addendum must appear in the disclaimer modal as a primary element, not as a footnote. The pre-trade planning reference disclaimer is only displayed in the detail panel's pre-trade reference section and does not appear on the main dashboard.

### 12.3 Terms of Service and Privacy Policy

- Terms of Service must be drafted by legal counsel and linked from the homepage, dashboard footer, and disclaimer modal.
- Privacy Policy must address: data collected (minimal in Phase 1: analytics, cache behavior, no user PII), how it is used, third-party data sharing, cookie usage, and contact for privacy requests.
- Both documents must be versioned; visitors must be notified of material changes via the disclaimer modal or banner.
- Cookie consent banner is required for EU users (GDPR compliance).

### 12.4 Data Provider Licensing

Before launch, confirm the following:
- CoinGecko Pro terms permit use of price and market data in an AI-driven analysis product displayed to end users.
- CryptoPanic or NewsAPI terms permit use of news content as LLM input for synthesis purposes.
- Glassnode free tier terms permit use of on-chain metrics in a commercial product. (If not permitted at free tier, Glassnode Studio plan at ~$39/month is the alternative; budget for this.)
- Anthropic API terms permit commercial use of generated output in a consumer-facing product. (This is standard but must be confirmed.)

---

## 13. Key Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Regulatory: crypto assets covered by STI are classified as securities, creating RIA registration requirement | Medium | Critical — forces product redesign, asset exclusions, or registration | Legal review before launch (go/no-go blocker); maintain an exclusion list capability; monitor SEC enforcement actions |
| AI rationale quality: LLM produces low-quality, speculative, or hallucinated crypto rationales | Medium | High — damages user trust; potential regulatory exposure if rationale is misleading | Human review of 20+ sample outputs pre-launch; confidence tier system; per-rationale disclaimer; prompt engineering validation |
| Candidate hit rate below 55% at 90 days | Medium | High — fails primary product quality metric | Formula validation by data science lead; conservative thresholds; post-launch monitoring and tuning loop |
| CoinGecko rate limits or API changes | Medium | High — Phase 1 depends entirely on CoinGecko; no viable free fallback for hourly data | Upgrade to appropriate Pro plan tier; implement CoinMarketCap as fallback; monitor API status proactively |
| Crypto market in sustained bear cycle at launch | Medium | Medium — fewer assets pass technical filters, leading to chronic "Low signal environment" state | This is correct behavior, not a bug; educate users in onboarding; consider an explicit "Bear market mode" UI state that explains conditions |
| Meme coin inclusion creates reputational damage | Low-Medium | Medium — a meme coin flash crash or rug pull that appeared in STI output could generate negative press | Confidence tier cap at Medium; rationale language must acknowledge speculative nature; monitor for rug-pull signals (exchange net flow drain) |
| On-chain data availability is too sparse to be meaningful | Medium | Low-Medium — on-chain boost points contribute 15% of Candidate Score; if data is unavailable for most coins, this component is effectively dead weight | Set realistic expectations: on-chain data will be available for BTC, ETH, and major DeFi tokens; for others it is a bonus, not a dependency. Remove the on-chain component from scoring if < 20% of top-50 coins have usable data. |
| Data cost overrun | Low | Low-Medium | Phase 1 data cost is low; monitor LLM token usage from day one; add spend alerts |
| User acquisition: product does not reach PMF signal volume | Medium | High — insufficient cohort to evaluate success metrics | Define minimum cohort size for 60-day review before launch; set acquisition channel strategy pre-launch |
| Competitor (CoinGecko, Messari, Nansen) adds AI synthesis layer | Low-Medium | Medium | Speed of execution; brand trust; pipeline sophistication accumulates as defensible advantage |

---

## 14. Open Questions and Decisions Required

Items marked **BLOCKING** must be resolved before the first line of code is written for the affected component.

| # | Question | Decision Needed From | Blocking? | Target Resolution |
|---|---|---|---|---|
| 1 | Does crypto-only analysis (as described) require any regulatory registration or approval before launch, and are any top-50 coins to be excluded due to securities classification risk? | Legal counsel | BLOCKING (launch) | Before development begins |
| 2 | Which LLM provider — Anthropic Claude or OpenAI GPT-4o — is selected for production Agent 3, based on structured evaluation of crypto rationale quality? | Product + Engineering (after evaluation) | BLOCKING (Agent 3 development) | Before Agent 3 sprint begins |
| 3 | What are the validated weighting formulas for Category Momentum Score (Agent 1) and Candidate Score (Agent 2)? | Data Science Lead | BLOCKING (Agent 1 and 2 development) | Week 2 of development |
| 4 | What CoinGecko plan tier is required to support hourly OHLCV for top-50 coins at the expected API call volume, and what is the confirmed cost? | Engineering | BLOCKING (data infrastructure planning) | Before development begins |
| 5 | Are meme coins included in the candidate universe with a confidence tier cap at Medium, or excluded entirely? | Product | BLOCKING (Agent 3 prompt engineering and scoring logic) | Before Agent 2/3 sprint begins |
| 6 | What is the approved Phase 1 data and infrastructure budget per month? | Founder / Finance | BLOCKING (data provider contracts) | Before development begins |
| 7 | Is Glassnode free tier usage permitted in a commercial product? If not, is the Glassnode Studio plan (~$39/month) approved? | Engineering + Legal | Non-blocking (on-chain signals are additive, not blocking) | Before Agent 2 data integration sprint |
| 8 | What is the minimum user cohort size required for the 60-day go/no-go review to be statistically meaningful? | Product + Founder | Non-blocking for launch | Before any public announcement |
| 9 | What is the business model for Phase 2 paid tier (price points, feature list), and does the Phase 1 data model need to support any Phase 2 monetization signals? | Founder | Non-blocking for Phase 1 | Before 60-day go/no-go review |
| 10 | Do the pre-trade planning reference fields (resistance zone, invalidation level, ATR, R:R context) require specific legal review under the crypto securities framework before Agent 3 begins surfacing them? | Legal Counsel | BLOCKING (pre-trade reference feature) | Before Agent 3 prompt engineering for this feature begins |
| 11 | Should entry type (Breakout/Retest/Dip-Buy) be a user-visible filter in the dashboard filter control bar? If yes, adds a new filter control to Section 8.1. | Product | Non-blocking for core feature | Before frontend development of the detail panel |
| 12 | Should the pre-trade reference section be a Phase 1 launch feature or deferred to Phase 1.1? The feature requires Agent 3 prompt additions and a new detail panel section but no new data sources. | Product + Engineering | Non-blocking for Phase 1 launch | Before Agent 3 sprint begins |

---

## 15. Go / No-Go Blockers

The following conditions must all be satisfied before Phase 1 is released to any external user, including a private beta:

1. **Legal sign-off obtained in writing.** Counsel has reviewed the product description, the specific top-50 crypto universe, disclaimer language, and Terms of Service. Counsel has confirmed: (a) the product does not require RIA registration or equivalent registration, (b) any coins with elevated securities classification risk are identified and handled (excluded or disclaimed), and (c) the crypto-specific addendum is legally adequate.

2. **Data provider agreements confirmed.** CoinGecko Pro plan is active and API terms for commercial use are confirmed. CryptoPanic or NewsAPI terms for LLM input use are confirmed. Glassnode usage licensing is confirmed (free tier or paid plan).

3. **LLM provider selected and tested.** A structured evaluation of at least two LLM providers has been completed against a test set of >= 20 crypto candidates. A human review panel (minimum 2 reviewers) has rated sample rationales against a defined quality rubric. The selected provider meets the quality bar: rationale is accurate, cites at least one technical and one narrative signal, and does not hallucinate price levels or events not present in the input.

4. **Candidate Score weighting formula defined, implemented, and documented.** Data Science Lead has signed off on the formula. Agent 2 Candidate Scores are deterministic, reproducible, and documented in a scoring specification artifact.

5. **Disclaimer layer implemented and verified.** All required disclaimer placements listed in Section 12.2 — including the crypto-specific addendum on all specified surfaces — have been implemented, verified by QA, and reviewed by legal.

6. **End-to-end pipeline test completed.** At least one full pipeline run (Agent 1 → Agent 2 → Agent 3) has been executed against live CoinGecko data, produced >= 5 candidates with rationales, and the output has been manually reviewed for quality and accuracy by the product lead. At least one event-triggered run has been tested.

7. **Security review completed.** API endpoint authorization, secrets management, data provider API key handling, and rate limiting have been reviewed by an engineer not responsible for their implementation. No critical or high-severity findings are open.

8. **Graceful degradation verified.** QA has confirmed: (a) a failed Agent 3 run causes the dashboard to serve the previous valid output with the staleness banner, (b) a visitor loading the dashboard when no pipeline output exists sees an appropriate empty state message and not a blank screen, and (c) the "Low signal environment" notice displays correctly when fewer than 5 candidates are output.

---

## 16. Dependencies

| Dependency | Type | Impact if Blocked | Owner |
|---|---|---|---|
| Legal counsel review (crypto-specific) | External | Launch blocked | Founder |
| CoinGecko Pro API access and plan confirmation | External | Agent 1 and 2 data blocked | Engineering |
| CryptoPanic API access | External | Agent 1 sentiment signals blocked | Engineering |
| Anthropic or OpenAI API key | External | Agent 3 development blocked | Engineering |
| Glassnode free tier licensing confirmation | External | On-chain signals blocked (non-blocking for core pipeline) | Engineering |
| AWS infrastructure provisioning (ECS, EventBridge, Secrets Manager) | Internal | Agent deployment and scheduling blocked | Engineering |
| Supabase (PostgreSQL) and Upstash (Redis) provisioned | Internal | Data persistence and caching blocked | Engineering |
| Data Science Lead availability (formula sign-off) | Internal | Agent 1 and 2 accuracy unvalidated | Product |
| Legal: Terms of Service and Privacy Policy drafted | External | Public dashboard launch blocked (required disclosure) | Founder + Legal |

---

## Appendix A: Phase 1 vs. Phase 2 Comparison

| Dimension | Phase 1 (This Document) | Phase 2 (PRD-v1.0.md) |
|---|---|---|
| User authentication | None (public, unauthenticated dashboard) | Email/password + Google OAuth + account management |
| User features | Dashboard only (no personalization) | Dashboard + watchlist + email digest + account settings |
| Asset universe | Top 50 crypto (no stablecoins) | Top 50 crypto + S&P 500 + NASDAQ 100 (~610 total) |
| Sector/category framework | 6–7 crypto categories | 11 GICS sectors + crypto categories |
| Agent 1 inputs | Crypto price/volume, crypto news sentiment, BTC dominance | ETF prices (GICS), crypto category benchmarks, VIX, 10Y yield, DXY |
| Agent 2 fundamental overlay | None | Revenue growth, D/E ratio, earnings surprises |
| Agent 2 insider signal | None | SEC EDGAR Form 4 buy filings |
| On-chain signals | Yes (additive boost) | Yes (crypto only, same as Phase 1) |
| Scheduling | 24/7, every 6 hours for full run | Market-hours-aware for equities; 24/7 for crypto |
| Max candidates per run | 25 | 30 |
| Estimated monthly data cost | $50–$380 | $650–$1,980 |
| Regulatory complexity | Crypto-specific (securities classification risk for some altcoins) | Equities (IAA 1940) + crypto |
| Time to market | Faster (lower integration complexity) | Slower |

---

*End of Document*

*This PRD represents Phase 1 product requirements as understood on 2026-04-30. It is a living document. All changes to Must Have requirements after the development sprint begins require sign-off from both Product and Engineering leads. Phase 2 requirements are defined in PRD-v1.0.md; this document governs Phase 1 only.*
