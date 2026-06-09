# Sentics Trading Intelligence (STI) — Product Requirements Document

## Document Control

| Field | Value |
|---|---|
| **Version** | 1.0 |
| **Date** | 2026-04-30 |
| **Status** | Draft — Pending Legal Review |
| **Author** | Product |
| **Reviewers** | Engineering Lead, Legal Counsel, Data Science Lead |

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

Retail investors who want to trade stocks and cryptocurrencies actively face a common and frustrating problem: they cannot efficiently identify high-quality entry candidates across thousands of securities without either spending hours on manual research or paying for expensive professional-grade tools designed for institutional traders.

Existing consumer-facing tools fall into two camps. Screeners (Finviz, TradingView) are powerful but require the user to know what they are looking for — they surface securities mechanically but offer no synthesis or forward-looking thesis. AI chatbots can generate analysis but lack live market data and cannot systematically scan the full investable universe. Neither approach continuously monitors the market on the user's behalf and surfaces opportunities proactively.

The result: retail investors either miss actionable opportunities, over-trade on noise, or give up and buy index funds. The sophisticated active investor in the middle — willing to research and act, but lacking the time and infrastructure to do so systematically — is underserved.

**Sentics Trading Intelligence (STI)** is an AI-powered web application that bridges this gap. It runs a continuous, multi-stage AI analysis pipeline across US equities and top cryptocurrencies, and delivers a curated, ranked list of buy candidates with a plain-English rationale, time horizon classification, and confidence signal — updated throughout the trading day.

---

## 2. Product Vision

**Vision statement:** Give every serious retail investor the analytical advantage of a quantitative research desk, at a price they can afford.

STI is not a trade execution platform, a portfolio manager, or a social network. It is an intelligence layer — a continuously updated ranked list of securities that a multi-agent AI system believes are worth serious consideration for purchase, organized by time horizon and explained in plain language.

The product surfaces *candidates*, not commands. Every output comes with a clearly labeled AI-generated rationale and a prominent disclaimer. The user makes the final decision.

---

## 3. Goals and Success Metrics

### Business Goals

| Goal | Metric | Target | Measurement Window |
|---|---|---|---|
| Validate that AI candidates perform meaningfully | % of candidates hitting stated target return within time horizon | > 55% hit rate | 90 days post-launch |
| Build a sticky daily-use habit | DAU / MAU ratio | >= 40% | 60 days post-launch |
| Demonstrate retention | 7-day user return rate | >= 40% | 60 days post-launch |
| Establish a path to monetization | Free-to-paid conversion rate | >= 15% | 90 days post-launch |

### Launch Threshold

At least three of the four metrics above must be tracking on-target at 60 days. If fewer than three are on track, the product team will initiate a structured pivot review before committing to Phase 2 engineering investment.

### Explicit Non-Goals for Metrics

- Absolute return performance relative to market benchmarks is not a launch metric. STI is not a fund. Hit rate on directional calls within stated horizon is the correct proxy for pipeline quality.
- Revenue at launch is not a goal. The MVP is a retention and product-market-fit experiment.

---

## 4. User Personas

### Primary: The Active Retail Investor (Alex)

- Age 28–45, employed full-time outside finance
- Trades stocks and/or crypto at least weekly
- Has brokerage accounts (Schwab, Fidelity, Robinhood, Coinbase); does not use a financial advisor
- Spends 30–90 minutes per day on market research across news, screeners, Reddit, and fintech apps
- Frustrated by information overload; wants high signal, low noise
- Willing to pay $15–$30/month for a tool that meaningfully improves their edge
- Technical comfort: moderate-to-high; comfortable reading a table of financial data but not writing code

**Primary job-to-be-done:** "Quickly find 2–3 credible stock or crypto ideas I can act on today, without spending two hours reading."

### Secondary: The Crypto-First Trader (Casey)

- Age 22–35, high risk tolerance
- Trades crypto daily or multiple times per week; may also trade equities
- Follows Twitter/X, Telegram channels, on-chain data; skeptical of traditional finance framing
- Values freshness above all else — wants the latest signal, not yesterday's analysis
- Interested in narrative momentum and catalysts more than fundamentals

**Primary job-to-be-done:** "Tell me which coins are showing real momentum right now and why, in plain language."

### Tertiary (Post-MVP): The Passive Opportunist (Jordan)

- Primarily an index fund investor who occasionally wants to make a tactical individual trade
- Low engagement, does not want to spend time in-app
- Would use the daily email digest as their primary touchpoint
- Requires the lowest friction path from insight to action

---

## 5. Scope

### 5.1 In Scope for MVP

**Universe of securities**
- US equities: S&P 500 constituents + NASDAQ 100 constituents (approximately 560 unique symbols after overlap)
- Cryptocurrency: Top 50 by 30-day average market capitalization (CoinGecko sourced, updated weekly)

**Pipeline and intelligence**
- Three-agent AI pipeline (detailed in Section 6)
- Automated orchestration scheduler (detailed in Section 7)
- Candidate Score calculation for each symbol
- Time horizon classification (Short / Medium / Long)
- Plain-English AI rationale for each candidate (50–300 words)

**Dashboard (web application)**
- Ranked candidates table with sortable columns
- Sector overview panel (sector Momentum Scores)
- Filter controls: asset class, time horizon, sector
- Candidate detail panel (full rationale, key metrics, scoring breakdown)
- Watchlist (up to 10 symbols, free tier)

**User accounts**
- Email + password authentication
- Google OAuth (Sign in with Google)
- Email verification on signup
- Basic account management (email, password change)

**Notifications**
- Daily email digest at 7:00 AM ET, weekdays
- Opt-in only; unsubscribe in one click

**Platform**
- Web application only, responsive design (desktop primary, mobile-friendly)
- No native iOS or Android app

### 5.2 Out of Scope for MVP

The following are explicitly excluded and should not be built, prototyped, or specced during the MVP phase. Scope creep into these areas is a risk that must be actively managed.

- Sell signals of any kind
- Portfolio tracking or performance history
- Brokerage API integration (no order placement, no linked accounts)
- Options, futures, or any derivative instruments
- International equities (ex-US)
- Forex and commodities
- Social features (follows, comments, shared watchlists, leaderboards)
- User-visible backtesting or historical performance charts for candidates
- Custom agent configuration or parameter tuning by users
- Real-time price streaming (WebSocket ticker in dashboard)
- Fine-tuned or proprietary LLM (use hosted API only)
- Mobile push notifications
- API access for third-party integrations

---

## 6. AI Agent Pipeline Architecture

The core intelligence of STI is a three-stage sequential agent pipeline. Each agent has a clearly defined input contract, output schema, and failure behavior. Agents are decoupled — they communicate exclusively through a shared PostgreSQL data store, not direct function calls or message queues.

### 6.1 Agent 1: Sector Trend Agent

**Purpose:** Determine which sectors of the market are exhibiting positive momentum and therefore warrant deeper analysis. Filter out sectors in decline to reduce noise in downstream agents.

**Inputs:**
- ETF price and volume data for the 11 GICS sector ETFs (XLK, XLF, XLV, XLE, XLI, XLY, XLP, XLRE, XLU, XLB, XLC) and analogous crypto category benchmarks (DeFi, Layer 1, Layer 2, AI tokens, stablecoins excluded)
- News sentiment signals: rolling 24-hour entity-level sentiment scores for each sector derived from financial news headlines and summaries (Benzinga or NewsAPI)
- Macro signals: 10-year Treasury yield direction (daily delta), VIX level and 5-day trend, USD index (DXY) direction

**Processing logic:**
- Calculate ETF-based momentum: 5-day vs. 20-day price return delta, volume-weighted
- Calculate news sentiment momentum: exponentially weighted moving average of sector sentiment scores, 72-hour window
- Combine into a Momentum Score (0–100) using a weighted formula:
  - ETF momentum: 50%
  - News sentiment: 35%
  - Macro adjustment: 15% (positive macro = modest boost to cyclical sectors; risk-off macro = modest boost to defensive sectors)
- Score all 11 GICS sectors + active crypto categories

**Output schema:**
```
sector_scores: [
  { sector_id, sector_name, momentum_score, etf_return_5d, etf_return_20d, sentiment_score, macro_context, updated_at }
]
```

**Downstream trigger:** Agent 2 is only invoked for sectors with Momentum Score >= 60. This threshold is a configurable system parameter (default: 60).

**Failure behavior:** If ETF data is unavailable for a sector, that sector is scored as null and excluded from Agent 2 input. The pipeline continues with available sectors. Agent failure is logged and alerted; the previous valid sector scores are retained in cache and served to the dashboard with a staleness indicator.

**Candidate Score weighting note:** The specific formula weights (50/35/15) are initial recommendations and must be validated by the data science lead before Agent 1 enters production. This is a go/no-go dependency for Agent 1 accuracy.

---

### 6.2 Agent 2: Stock Discovery Agent

**Purpose:** Within the sectors passing Agent 1's threshold, identify individual securities that meet a quantitative bar for both technical setup and fundamental quality. Produce a ranked shortlist of candidates for Agent 3's deeper synthesis.

**Inputs:**
- Agent 1 output: sectors with Momentum Score >= 60
- Full price/volume time series for all securities within those sectors (from the MVP universe)
- Fundamental data: revenue growth, debt-to-equity, earnings surprise history
- Insider trading data: recent Form 4 filings (SEC EDGAR)

**Technical filters (all must pass):**
- RSI (14-day) between 40 and 70 — excludes overbought (> 70) and oversold (< 40) conditions
- Volume: trailing 5-day average volume >= 1.5x the trailing 30-day average volume (volume surge confirmation)
- Price: current price >= 50-day simple moving average (above trend)

**Fundamental overlay (at least 2 of 3 must pass for equities):**
- Revenue growth (TTM YoY) > 10%
- Debt-to-equity ratio < 2.0
- Last earnings result: beat consensus estimate by any margin (or N/A if not yet reporting)

**Crypto-specific filters (replaces fundamental overlay):**
- 30-day price return > 0% (positive trend)
- 7-day trading volume >= 1.2x 30-day average (momentum confirmation)
- Market cap rank within top 50 maintained (no newly listed tokens)

**Insider signal boost (optional, equity only):**
- If >= 2 insider buy transactions (Form 4) filed within the past 30 days: add +5 points to the raw Candidate Score
- Insider sell transactions: no penalty (sells have too many non-signal interpretations)

**Output:**
- Up to 50 candidates ranked by Candidate Score
- Candidate Score = weighted composite of: technical alignment (40%), sector momentum inheritance (35%), fundamental quality (25%) — weights subject to data science review
- For each candidate: symbol, name, sector, asset class, RSI, volume ratio, price vs. 50-day MA, revenue growth, D/E ratio, insider signal flag, candidate score, pipeline run timestamp

**Failure behavior:** If fewer than 5 candidates are produced (e.g., broad market downturn passes few filters), Agent 2 outputs what it has. Agent 3 is still invoked. The dashboard shows a "Low signal environment" notice when fewer than 5 candidates are present.

---

### 6.3 Agent 3: Forward-Looking Synthesis Agent

**Purpose:** For each candidate passing Agent 2, generate a forward-looking investment thesis using an LLM. Classify the time horizon, assign a final confidence tier, and produce a plain-English rationale. Output the final ranked list of up to 30 candidates.

**Inputs:**
- Agent 2 output: up to 50 candidates with scoring data
- Recent news headlines and summaries for each symbol (last 48 hours, top 5 by relevance)
- Earnings calendar: next expected reporting date for equities
- Recent analyst rating changes (if available from data provider)
- Macro context summary: brief structured summary generated from Agent 1's macro signals

**LLM prompt contract:**

Each symbol is processed with a structured prompt containing:
1. Symbol metadata (name, sector, asset class)
2. Key quantitative signals (RSI, volume ratio, price vs. MA, candidate score, fundamental metrics)
3. Top 5 recent news headlines with source and date
4. Macro context summary
5. Instruction to produce: a time horizon classification (Short/Medium/Long), a confidence tier (High/Medium/Low), and a 50–300 word rationale explaining the opportunity in plain English, citing at least one quantitative signal and one qualitative narrative signal

**Time horizon definitions:**
- Short: 1–14 days. Primarily driven by technical setup and near-term catalyst.
- Medium: 2–8 weeks. Combination of technical trend and fundamental momentum.
- Long: 3–6 months. Primarily driven by structural fundamental thesis with sector tailwind.

**Confidence tier definitions:**
- High: >= 3 supporting signals across technical, fundamental, and sentiment dimensions
- Medium: 2 supporting signals, or 3 with at least one conflicting indicator
- Low: 1–2 supporting signals, or any candidate with a notable identified risk in the rationale

**Final ranking logic:**
- Primary sort: Candidate Score (descending)
- Secondary sort: Confidence tier (High > Medium > Low)
- Maximum output: 30 candidates per full pipeline run
- Deduplication: if the same symbol appears as both an equity and a crypto derivative (not possible in MVP scope, but defensively handled), equity takes precedence

**Output schema:**
```
candidates: [
  {
    symbol, name, sector, asset_class,
    candidate_score, confidence_tier, time_horizon,
    rationale_text, key_signals: [...],
    next_earnings_date, last_news_headline,
    pipeline_run_id, generated_at
  }
]
```

**LLM provider:** Anthropic Claude API (claude-opus-4 or claude-sonnet-4 depending on cost/quality evaluation) or OpenAI GPT-4o. A structured side-by-side evaluation of both providers against a test set of 20 candidate symbols must be completed before selecting the production provider. Evaluation criteria: rationale quality (human-rated), adherence to output schema, latency, and cost per 1,000 symbols processed.

**Cost control:** Agent 3 is rate-limited to 4 full pipeline runs per day (including nightly + triggered runs). Partial re-runs triggered by sector events process only affected-sector candidates, not the full 30.

**Failure behavior:** If the LLM API call fails for a candidate, that candidate is dropped from the output (not surfaced with a blank rationale). If more than 10 candidates fail in a single run, the run is flagged as degraded and the previous successful output is served with a staleness indicator.

---

## 7. Orchestration and Scheduling

The orchestration layer is responsible for triggering pipeline runs on schedule, handling event-driven triggers, enforcing rate limits, and managing the state of pipeline outputs.

### 7.1 Standard Scheduled Runs

| Schedule | Trigger | Agents Invoked | Scope |
|---|---|---|---|
| Nightly, 2:00 AM ET, daily | Cron | 1 → 2 → 3 (full) | All sectors, full universe |
| Hourly, 9:30 AM – 4:00 PM ET, weekdays | Cron | 1, then 2 conditionally | Equities only |
| Hourly, 24/7 | Cron | 1 → 2 | Crypto only |
| Morning pre-open, 7:00 AM ET, weekdays | Cron | Email digest trigger only | Uses previous nightly Agent 3 output |

**Conditional logic for hourly equity runs:**

Agent 2 is only re-invoked during an hourly equity run if at least one sector's Momentum Score has shifted by >= 15 points relative to the previous hourly run. If no sector exceeds this delta threshold, Agent 1 data is updated in the store but Agent 2 and 3 are not re-invoked. This prevents unnecessary downstream processing and LLM cost during stable market conditions.

Agent 3 is never invoked on hourly runs unless the run is also classified as event-triggered (see Section 7.2). The dashboard reflects Agent 1 sector updates in near-real-time (within the hourly polling window) while the candidate list reflects the last Agent 3 run.

### 7.2 Event-Triggered Runs

The following events trigger an out-of-schedule pipeline run:

| Event | Detection Method | Agents Invoked | Notes |
|---|---|---|---|
| Earnings surprise | Earnings calendar poll + actual vs. estimate delta | 2 → 3 (sector-scoped) | Triggered if beat/miss >= 10% vs. consensus |
| News spike | News API: mention rate >= 3x 30-min average for a symbol | 2 → 3 (symbol-scoped) | Limited to existing pipeline candidates to avoid unbounded scope |
| FOMC announcement | Hardcoded FOMC calendar dates, market hours | 1 → 2 → 3 (full) | Counts against daily Agent 3 run limit |
| Macro shock | VIX single-session spike >= 20% | 1 → 2 → 3 (full) | Counts against daily Agent 3 run limit |

**Event run limits:** Event-triggered Agent 3 invocations count toward the 4-run-per-day cap. If the cap is reached, event triggers queue but do not invoke Agent 3 until the following day's cap resets at midnight ET. Agent 1 and Agent 2 can still run (they have no hard daily cap, though they should not be invoked more than once per 15 minutes).

### 7.3 Pipeline State and Output Freshness

- The PostgreSQL store records the timestamp of every pipeline run per agent.
- Redis caches the final Agent 3 output (ranked candidates list) with a TTL of 60 minutes.
- The dashboard always reads from Redis cache. Cache miss falls back to PostgreSQL.
- The dashboard displays a "Last updated" timestamp and a staleness banner if the Agent 3 output is older than 6 hours during market hours or older than 14 hours outside market hours.

### 7.4 Infrastructure for Scheduling

- AWS EventBridge (or equivalent) for cron-based triggers
- AWS ECS Fargate tasks (or equivalent) for stateless agent execution
- Each agent runs as an independent container; the orchestrator invokes them sequentially and passes the run ID as the coordination key
- Dead-letter queue (SQS DLQ or equivalent) for failed pipeline run notifications to engineering on-call

---

## 8. MVP Functional Requirements

Requirements are organized by feature area. Each includes the user story, acceptance criteria, and MoSCoW priority. All Must Have requirements must be complete and passing acceptance criteria before the MVP is declared launch-ready.

---

### 8.1 User Authentication and Accounts

**Priority: Must Have**

**User Story — Registration:**
As a new visitor, I want to create an account with my email address and password so that I can access the dashboard and save my preferences.

**Acceptance Criteria:**
- Given a visitor on the signup page, when they submit a valid email and password (>= 8 characters, at least 1 number), then an account is created and a verification email is sent within 60 seconds.
- Given a visitor submitting a duplicate email address, when they attempt to register, then the form displays "An account with this email already exists" and does not create a duplicate account.
- Given a visitor who has not verified their email, when they attempt to log in, then they see a prompt to resend the verification email and cannot access the dashboard.
- Given a visitor clicking "Sign in with Google", when Google OAuth completes successfully, then an account is created or matched (if email already exists) and the user is logged in.
- Given an authenticated user, when they request a password change, then they receive a reset email within 60 seconds and the old password is invalidated upon reset completion.

---

**User Story — Session Management:**
As a returning user, I want my login session to persist so that I do not have to log in every time I return to the dashboard.

**Acceptance Criteria:**
- Given an authenticated user who closes the browser and returns within 30 days, when they visit the application URL, then they are automatically logged in without re-entering credentials.
- Given an authenticated user on a public/shared device who clicks "Log out", when they log out, then the session token is invalidated server-side and they are redirected to the homepage.
- Given an authenticated user, when their session is idle for more than 30 days without any activity, then the session expires and they must log in again.

---

### 8.2 Ranked Candidates Dashboard

**Priority: Must Have**

**User Story — Main Table:**
As an investor, I want to see a ranked table of AI-identified buy candidates so that I can quickly evaluate which securities are worth my attention today.

**Acceptance Criteria:**
- Given an authenticated user on the dashboard, when the page loads, then a table of ranked candidates is displayed within 3 seconds (p95) sourced from the Redis cache.
- Given the candidates table, when it renders, then it displays at minimum: rank, symbol, name, asset class (equity/crypto), sector, time horizon, confidence tier, candidate score, and last-updated timestamp for each row.
- Given the table, when a user clicks any column header (rank, score, time horizon, confidence), then the table sorts by that column ascending or descending.
- Given an authenticated user, when the Agent 3 output is older than 6 hours during market hours, then a yellow staleness banner is displayed above the table: "Analysis last updated [timestamp]. Refresh may be in progress."
- Given an authenticated user, when fewer than 5 candidates are in the current output, then a blue "Low signal environment" notice is displayed explaining that market conditions have reduced the candidate pool.
- Given the table with more than 30 rows (should not occur in MVP, but defensively), when it renders, then it is paginated at 30 rows per page.

---

**User Story — Candidate Detail Panel:**
As an investor, I want to click on a candidate to see the full AI-generated rationale and supporting data so that I can decide whether to research it further.

**Acceptance Criteria:**
- Given a user clicking any row in the candidates table, when the click registers, then a detail panel (drawer or modal) opens within 500ms displaying: symbol, name, full rationale text, time horizon, confidence tier, candidate score breakdown, key signals (RSI, volume ratio, price vs. MA, fundamental metrics), next earnings date (equity only), and last relevant news headline with link.
- Given the detail panel, when the rationale text is displayed, then the disclaimer "This analysis is generated by artificial intelligence and is not financial advice. Past performance is not indicative of future results." is displayed directly below the rationale in a visually distinct style (muted color, smaller font).
- Given the detail panel, when a user clicks outside the panel or presses Escape, then the panel closes and the table returns to the same scroll position.

---

**User Story — Sector Overview Panel:**
As an investor, I want to see which sectors are trending before reviewing individual candidates so that I can understand the macro context.

**Acceptance Criteria:**
- Given an authenticated user on the dashboard, when the sector overview panel is visible, then all 11 GICS sectors plus active crypto categories are displayed with their current Momentum Score (0–100) and a directional indicator (up/down/flat vs. previous run).
- Given a sector with Momentum Score >= 60, when displayed, then it is visually highlighted (e.g., green accent) to indicate it passed the Agent 2 threshold.
- Given a user clicking a sector in the overview panel, when the click registers, then the candidates table is filtered to show only candidates from that sector.

---

**User Story — Filter Controls:**
As an investor, I want to filter the candidates list by asset class and time horizon so that I can focus on the type of opportunity I am looking for.

**Acceptance Criteria:**
- Given the filter control bar, when rendered, then it contains: asset class filter (All / Equities / Crypto), time horizon filter (All / Short / Medium / Long), and confidence filter (All / High / Medium / Low).
- Given any filter selection, when applied, then the table updates within 300ms (client-side filter, no server round-trip).
- Given multiple filters selected simultaneously, when applied, then the table shows only candidates matching all selected filter values (AND logic).
- Given a user resetting all filters, when they click "Clear filters", then all filters return to "All" and the full ranked list is restored.
- Given an active filter that produces zero results, when applied, then the table displays "No candidates match these filters" and the clear filters control remains accessible.

---

### 8.3 Watchlist

**Priority: Must Have**

**User Story:**
As an investor, I want to save up to 10 securities to a personal watchlist so that I can quickly check on specific symbols I care about without scanning the full table.

**Acceptance Criteria:**
- Given an authenticated user viewing any candidate in the table or detail panel, when they click the "Add to Watchlist" control, then the symbol is added to their watchlist (if fewer than 10 symbols are already saved) and the control updates to indicate it is saved.
- Given a user with 10 symbols on their watchlist, when they attempt to add an 11th, then they see an inline message: "Watchlist limit reached (10/10). Upgrade to Pro for unlimited watchlist." The symbol is not added.
- Given an authenticated user on the dashboard, when they open the watchlist panel, then all saved symbols are displayed with their current candidate score, time horizon, and confidence tier (if they are in the current ranked output) or a "Not currently ranked" indicator (if they are not in the current output).
- Given a user removing a symbol from their watchlist, when they click "Remove", then the symbol is removed immediately without a confirmation dialog.
- Given a user's watchlist, when they log out and log back in, then the same watchlist persists.

---

### 8.4 Daily Email Digest

**Priority: Must Have**

**User Story:**
As an investor, I want to receive a morning email summary of the top AI candidates so that I can review opportunities before the market opens without logging in.

**Acceptance Criteria:**
- Given an authenticated user who has opted in to the email digest (opt-in is prompted on first login, default is opted-out), when 7:00 AM ET is reached on a weekday, then a digest email is sent within 5 minutes.
- Given the digest email, when delivered, then it contains: top 5 candidates from the most recent Agent 3 output (ranked by score), the time horizon and confidence tier for each, a one-sentence excerpt of the rationale, a CTA link back to the dashboard for each candidate, and the legal disclaimer.
- Given the digest email, when delivered on a day where Agent 3 has not run in the prior 18 hours, then it is not sent and a system alert is raised to engineering.
- Given a user who has opted out, when 7:00 AM ET is reached, then no email is sent to that user.
- Given a digest email, when the user clicks the unsubscribe link, then their email digest preference is set to opted-out within 10 seconds and a confirmation page is displayed. The user must not receive another digest email after this action without explicitly re-opting-in.
- Given the digest email, when rendered in a major email client (Gmail, Apple Mail, Outlook), then it is readable and structurally correct on both desktop and mobile viewports.

---

### 8.5 Pipeline Monitoring (Internal / Admin)

**Priority: Must Have**

**User Story:**
As an engineer or product team member, I want to see the status of each pipeline run so that I can detect and diagnose failures without manually querying the database.

**Acceptance Criteria:**
- Given any pipeline run completing (successfully or with errors), when it completes, then a run log entry is written to the database recording: run ID, agents invoked, start time, end time, trigger type (scheduled/event), number of sectors processed, number of candidates output by Agent 2, number of candidates output by Agent 3, and any error codes.
- Given a pipeline run where any agent fails entirely, when the failure occurs, then an alert is sent to the engineering on-call channel (Slack or PagerDuty equivalent) within 5 minutes.
- Given an internal admin dashboard (basic, not customer-facing), when accessed by an authenticated admin user, then it displays the last 24 hours of pipeline run logs in a table with the fields above, and highlights failed runs in red.
- Given the admin dashboard, when an admin views a failed run, then they can see the error message and the last successfully cached Agent 3 output timestamp.

---

### 8.6 Legal Disclaimer and Disclosure

**Priority: Must Have**

**Acceptance Criteria:**
- Given any unauthenticated visitor viewing the homepage or marketing pages, when the page renders, then the following disclaimer is displayed in the page footer and on any page that describes the product's analysis capabilities: "Sentics Trading Intelligence provides AI-generated market analysis for informational purposes only. This is not investment advice. Sentics is not a registered investment advisor. Always conduct your own research and consult a qualified financial professional before making investment decisions."
- Given an authenticated user viewing the dashboard for the first time after account creation, when the dashboard loads, then a one-time acknowledgment modal is displayed containing the full disclaimer. The user must click "I understand" to dismiss it. The modal cannot be dismissed by clicking outside it.
- Given any candidate detail panel, when displayed, then the per-rationale disclaimer (AI-generated, not financial advice) is visible without scrolling.
- Given the daily email digest, when delivered, then the footer contains the full disclaimer text verbatim.

---

### 8.7 Responsive Web Application

**Priority: Should Have**

**Acceptance Criteria:**
- Given a user accessing the dashboard on a desktop viewport (>= 1024px width), when the page renders, then the sector overview panel, candidates table, and filter controls are all visible without horizontal scrolling.
- Given a user accessing the dashboard on a tablet viewport (768px – 1023px), when the page renders, then the layout adapts: the sector overview panel collapses to a scrollable horizontal row of sector chips, and the table remains functional with at least 5 columns visible.
- Given a user accessing the dashboard on a mobile viewport (< 768px), when the page renders, then the table is readable with rank, symbol, time horizon, and confidence visible; other columns are accessible via horizontal scroll or collapsed into the detail panel.
- Given any viewport, when the user taps a table row on a touch device, then the detail panel opens with the same behavior as a click on desktop.

---

### 8.8 Performance and Loading States

**Priority: Should Have**

**Acceptance Criteria:**
- Given an authenticated user loading the dashboard, when the page is loading, then skeleton loaders are displayed for the table and sector panel before data arrives. A blank white screen with no loading indicator is not acceptable.
- Given the dashboard table, when data has loaded, then the Largest Contentful Paint (LCP) is <= 2.5 seconds on a simulated fast 4G connection.
- Given the dashboard table, when data has loaded, then the Cumulative Layout Shift (CLS) score is <= 0.1.

---

## 9. Post-MVP Roadmap

### Phase 2 — Depth and Engagement (Target: 3–5 months post-launch)

These requirements are validated based on user feedback from MVP. Do not begin engineering work on Phase 2 until the 60-day go/no-go review is passed.

**Sell Signal and Exit Recommendations**
- Agent 3 extended to produce exit thesis for previously recommended candidates
- Dashboard shows "Watch for exit" flag on candidates that have materially changed signal profile since recommendation
- User Story: As an investor who bought a candidate I found on STI, I want to know when the AI's outlook has changed so I can reconsider my position.

**Candidate Score Explainability Panel**
- Visual breakdown of how each component (technical, fundamental, sector, sentiment) contributed to the candidate score
- Allows users to understand and build trust in the scoring logic
- Must Have for Phase 2

**Unlimited Watchlist (Paid Tier)**
- Remove 10-symbol cap for paid subscribers
- Watchlist price alerts: notify user when a watched symbol enters the current ranked output
- Email or in-app notification (in-app requires notification infrastructure investment)

**Enhanced Filtering**
- Filter by specific sector (not just asset class)
- Filter by minimum candidate score threshold (user-set slider)
- Filter by market cap range (large/mid/small cap for equities)

**Historical Candidate Archive**
- Users can browse past pipeline outputs (30-day rolling window)
- Not a performance chart — shows what candidates were recommended and when, without price outcome data (to avoid survivorship bias presentation issues)
- Internal-only performance tracking continues; this is not the same as user-visible backtesting

**Alert Preferences**
- Users can configure: which events trigger email alerts (earnings surprise on a watched symbol, sector momentum spike)
- In-app notification center (Phase 2)

---

### Phase 3 — Monetization and Scale (Target: 6–12 months post-launch)

**Paid Subscription Tier**
- Define specific tier benefits (unlimited watchlist, advanced filters, real-time alerts, API access under consideration)
- Payment processing: Stripe
- Billing management: upgrade, downgrade, cancel in-app
- Grandfathering policy for early users must be defined before launch

**Expanded Universe**
- Add mid-cap equities (Russell 1000 addition to existing S&P 500 + NASDAQ 100)
- International equities (MSCI World ex-US top 200) — requires evaluation of international data provider options and significant increase in data costs
- Crypto expansion: top 200 by market cap

**Portfolio Context Mode**
- Users can optionally input their current holdings (manual entry only; no brokerage link)
- Dashboard highlights candidates that overlap or complement their current holdings
- Requires clear disclaimer that this is not portfolio management

**Backtesting Dashboard (Internal → User-Facing)**
- After sufficient historical data is accumulated (>= 90 days of pipeline outputs with outcome tracking), evaluate publishing a user-facing performance dashboard
- Legal review required before any performance data is shown to users
- Must show both hits and misses; cherry-picked performance display is prohibited

**LLM Evaluation and Optimization**
- Quarterly provider re-evaluation as model capabilities evolve
- Explore whether fine-tuning on domain-specific rationale quality data improves output
- Cost optimization: evaluate local/self-hosted models for Agent 2 (classification tasks) to reduce per-run cost

---

## 10. High-Level Technical Architecture

### 10.1 Component Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Layer                               │
│   Browser (Next.js/React)   │   Email Client (Digest)          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Application Layer                          │
│   Next.js API Routes / REST API (authenticated endpoints)       │
│   Auth: NextAuth.js or Auth.js (session + OAuth)               │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌─────────────────────┐         ┌─────────────────────────────┐
│   Redis Cache        │         │   PostgreSQL (primary store) │
│   (candidates list, │         │   (pipeline runs, scores,    │
│    TTL 60 min)       │         │    users, watchlists, logs)  │
└─────────────────────┘         └─────────────────────────────┘
                                              │
                              ┌───────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Agent Pipeline Layer                        │
│                                                                 │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────┐   │
│  │  Agent 1     │──▶│  Agent 2     │──▶│  Agent 3         │   │
│  │  Sector      │   │  Stock       │   │  Forward-Looking  │   │
│  │  Trend       │   │  Discovery   │   │  Synthesis (LLM)  │   │
│  └──────────────┘   └──────────────┘   └──────────────────┘   │
│                                                                 │
│  Orchestrator (EventBridge + ECS Fargate tasks)                │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────────┐
│                      Data Source Layer                          │
│                                                                 │
│  Polygon.io / Alpaca  │  CoinGecko  │  Benzinga / NewsAPI      │
│  FMP (Fundamentals)   │  SEC EDGAR  │  Anthropic / OpenAI API  │
└─────────────────────────────────────────────────────────────────┘
```

### 10.2 Technology Stack

| Layer | Technology | Rationale |
|---|---|---|
| Frontend | Next.js (React) | SSR for SEO on marketing pages, CSR for dashboard interactivity; strong ecosystem |
| API | Next.js API routes or separate FastAPI service | Consolidate with frontend for MVP; extract to dedicated service if latency requires it |
| Authentication | Auth.js (formerly NextAuth) | Native Next.js integration; supports Google OAuth + email/password |
| Primary database | PostgreSQL (managed: AWS RDS or Supabase) | Relational model suits pipeline run logs and user data; mature, well-understood |
| Cache | Redis (managed: AWS ElastiCache or Upstash) | Low-latency cache for dashboard reads; TTL management built-in |
| Agent runtime | Python 3.11+ | Strong data science and LLM SDK ecosystem |
| Agent packaging | Docker containers on AWS ECS Fargate | Stateless execution; no server management; pay-per-use |
| Scheduler | AWS EventBridge (cron rules) | Native AWS cron integration with ECS; no additional scheduler service needed |
| Email | SendGrid or AWS SES | SendGrid preferred for template management and deliverability tooling |
| LLM API | Anthropic Claude API or OpenAI GPT-4o | See Section 6.3 for evaluation requirement |
| Monitoring | AWS CloudWatch + Slack webhook for alerts | Lightweight for MVP; evaluate Datadog in Phase 2 |
| Data ingestion | Polygon.io (equities), CoinGecko (crypto), Benzinga (news), FMP (fundamentals), SEC EDGAR (insider) | See Section 10.3 |

### 10.3 Data Source Specifications

| Source | Data Type | Preferred Provider | Fallback | Est. Monthly Cost | Update Frequency |
|---|---|---|---|---|---|
| Equity price/volume | OHLCV, real-time quotes | Polygon.io | Alpaca Markets | $200–$500 | Per-minute during market hours |
| Crypto price/volume | OHLCV, market cap | CoinGecko API | CoinMarketCap | $0–$130 (Pro plan) | Hourly |
| Financial news | Headlines, summaries, sentiment | Benzinga News API | NewsAPI.org | $200–$400 | Near-real-time |
| Fundamentals | Revenue, D/E, earnings | Financial Modeling Prep | Alpha Vantage | $50–$150 | Daily (after close) |
| Insider filings | Form 4 buy/sell transactions | SEC EDGAR API | — | $0 (public) | Daily |
| LLM | Rationale generation | Anthropic Claude API | OpenAI GPT-4o | $200–$800 | Per-run |

**Total estimated data + LLM cost at launch volume:** $650–$1,980/month. Budget should be planned at $2,000/month with headroom.

### 10.4 Data Storage Schema (Key Tables)

**pipeline_runs** — One row per agent invocation
```
run_id, agent_id, trigger_type, started_at, completed_at, status,
sectors_processed, candidates_in, candidates_out, error_code, error_message
```

**sector_scores** — Agent 1 output, one row per sector per run
```
run_id, sector_id, sector_name, momentum_score, etf_return_5d,
etf_return_20d, sentiment_score, macro_context, scored_at
```

**candidates** — Agent 3 final output, one row per candidate per run
```
run_id, symbol, name, sector_id, asset_class, candidate_score,
confidence_tier, time_horizon, rationale_text, key_signals_json,
next_earnings_date, last_news_headline, generated_at
```

**users**
```
user_id, email, hashed_password, google_sub, email_verified,
created_at, last_login_at, email_digest_opted_in, disclaimer_acknowledged_at
```

**watchlists**
```
watchlist_id, user_id, symbol, asset_class, added_at
```

---

## 11. Non-Functional Requirements

### 11.1 Performance

| Requirement | Target | Measurement Method |
|---|---|---|
| Dashboard initial load (authenticated) | p95 <= 3 seconds | Synthetic monitoring, Lighthouse |
| Candidate table render (data already cached) | p95 <= 500ms | Browser performance API |
| Client-side filter application | <= 300ms | Browser performance API |
| Detail panel open | <= 500ms | Browser performance API |
| Redis cache read latency | p99 <= 20ms | CloudWatch metrics |
| Agent 1 full run time | <= 10 minutes | Pipeline run log |
| Agent 2 full run time | <= 15 minutes | Pipeline run log |
| Agent 3 full run time (30 candidates) | <= 30 minutes | Pipeline run log |
| Full nightly pipeline | <= 60 minutes end-to-end | Pipeline run log |
| Email digest delivery | Within 5 minutes of 7:00 AM ET trigger | Email provider delivery report |

### 11.2 Availability and Reliability

| Requirement | Target |
|---|---|
| Web application uptime | >= 99.5% monthly (allows ~3.6 hours downtime/month) |
| Nightly pipeline success rate | >= 95% of scheduled runs complete without degraded output |
| Graceful degradation | If Agent 3 output is stale, the previous valid output must be served. The application must never show an empty candidates table to an authenticated user unless no output has ever been generated. |
| Database backups | Automated daily backups with 7-day retention (RDS managed) |
| Recovery time objective (RTO) | <= 2 hours for any single-component failure |

### 11.3 Security

| Requirement | Specification |
|---|---|
| Authentication | Industry-standard session tokens; HTTPS enforced site-wide; secure cookie attributes (HttpOnly, SameSite=Strict) |
| Password storage | bcrypt with minimum cost factor 12 |
| API authentication | All dashboard API endpoints require valid session; no unauthenticated data access |
| Rate limiting | Login endpoint: 5 failed attempts per 15 minutes per IP before CAPTCHA challenge; API endpoints: 60 requests/minute per authenticated user |
| Data in transit | TLS 1.2+ enforced for all connections including database and cache |
| Data at rest | Database encryption enabled (RDS managed encryption) |
| PII handling | User email is PII; no PII is logged in application logs or pipeline run logs; email is stored encrypted at rest |
| Third-party API keys | All API keys stored in secrets manager (AWS Secrets Manager or equivalent); never in environment variables in code or version control |
| GDPR/CCPA readiness | User can request data export and account deletion from account settings page; deletion must cascade to watchlists and email preferences; pipeline analysis data is not user PII and is retained |

### 11.4 Scalability

The MVP does not need to be built for massive scale, but it must not have architectural choices that create ceilings below 10,000 registered users and 1,000 daily active users.

- PostgreSQL with connection pooling (PgBouncer or RDS Proxy) should handle MVP load without schema changes up to 50,000 users.
- Redis cache absorbs dashboard read load; horizontal scaling of the Next.js application (ECS or Vercel) handles web traffic increases.
- The agent pipeline is not user-facing latency-critical; it runs on a fixed cadence and can scale compute vertically per Fargate task if run time grows with universe expansion.

### 11.5 Accessibility

- The web application must achieve WCAG 2.1 Level AA compliance for the dashboard and authentication flows.
- Minimum contrast ratio: 4.5:1 for normal text, 3:1 for large text.
- All interactive elements must be keyboard-navigable.
- The candidates table must have appropriate ARIA roles and labels for screen reader compatibility.

### 11.6 Data Freshness and Display

- Every data point displayed to the user (sector score, candidate score, rationale) must have an associated timestamp visible in the UI.
- The dashboard must never display analysis without indicating when it was generated.
- "Real-time" or "live" must not be used in any UI copy unless price data is updated within 5 minutes. If price data is delayed, the delay must be disclosed (e.g., "Prices delayed 15 minutes").

---

## 12. Legal, Compliance, and Disclaimers

This section is high-priority. Legal review is a hard go/no-go blocker. Do not launch without written legal sign-off on each item in Section 12.1.

### 12.1 Regulatory Classification

STI provides AI-generated analysis of securities. The critical legal question is whether this activity constitutes investment advice requiring registration as a Registered Investment Advisor (RIA) under the Investment Advisers Act of 1940 (US) or equivalent regulation.

**Position (to be validated by counsel):** STI is general-purpose market analysis content, not personalized investment advice, because:
1. Recommendations are not personalized to the user's financial situation, goals, risk tolerance, or existing holdings.
2. Output is the same for all users (no individualization).
3. The product does not provide buy/sell signals linked to specific dollar amounts, position sizes, or portfolio allocation.
4. Prominent disclaimers at every interaction point make the non-advisory nature clear.

**Legal counsel must confirm or refute this position in writing before launch.**

If counsel determines that RIA registration is required, the product must not launch until registration is complete or the product is materially redesigned to fall outside the regulatory threshold.

### 12.2 Required Disclaimers

The following disclaimer text is required on all specified surfaces. No paraphrasing without legal review of the revised text.

**Full disclaimer (footer, email, onboarding modal):**
> "Sentics Trading Intelligence provides AI-generated market analysis for informational purposes only. This is not investment advice. Sentics is not a registered investment advisor. The information provided is not a recommendation to buy, sell, or hold any security or cryptocurrency. Markets are volatile and investments carry risk of loss, including total loss of principal. Always conduct your own research and consult a qualified financial professional before making any investment decisions. AI-generated analysis may contain errors. Past candidate performance is not a guarantee of future results."

**Per-rationale disclaimer (candidate detail panel):**
> "This analysis is generated by artificial intelligence and is not financial advice. Past performance is not indicative of future results."

**Crypto-specific addendum (required where crypto is discussed):**
> "Cryptocurrency assets are not regulated securities in most jurisdictions. Crypto markets operate 24/7 and are subject to extreme volatility and liquidity risk. You may lose your entire investment."

### 12.3 Terms of Service and Privacy Policy

- Terms of Service must be drafted by legal counsel and linked from signup, dashboard footer, and every email.
- Privacy Policy must address: data collected, how it is used, third-party data sharing (none in MVP, but data provider agreements may have implications), user rights (access, deletion, portability), and contact for privacy requests.
- Both documents must be versioned; users must be notified and re-acknowledge if material changes are made.
- Cookie consent banner is required for EU users (GDPR compliance). Implement Consent Mode or equivalent.

### 12.4 Data Provider Licensing

All data providers have terms of service that govern usage. Before launch:
- Confirm that Polygon.io (or selected equity data provider) permits use of data in an AI-driven recommendation display product.
- Confirm that financial news providers (Benzinga) permit use of article content or summaries as LLM input.
- Confirm that FMP fundamental data can be incorporated into scored outputs displayed to end users.

Failure to secure appropriate data licenses creates legal exposure independent of the investment advice question.

---

## 13. Key Risks

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Legal/regulatory: Product classified as investment advice requiring RIA registration | Medium | Critical — forces product redesign or registration process | Legal review before launch (go/no-go blocker); strong disclaimer layer; do not personalize output |
| AI rationale quality: LLM produces low-quality, hallucinated, or misleading rationales | Medium | High — damages user trust, potential regulatory exposure | Human review of sample outputs pre-launch; confidence tier system reduces visibility of weak candidates; per-rationale disclaimer |
| Candidate hit rate below 55% at 90 days | Medium | High — fails primary product quality metric; undermines business case | Weighting formula validation by data science lead pre-launch; conservative initial scoring thresholds; post-launch monitoring and tuning loop |
| Data source cost overrun | Low-Medium | Medium — unit economics impact | Cost monitoring from day one; alert thresholds on LLM spend; reduce Agent 3 run frequency if cost exceeds budget |
| Data provider API downtime | Medium | Medium — pipeline failure, stale output | Graceful degradation: serve last valid output with staleness indicator; fallback data providers defined per source |
| Meme coin or manipulated asset inclusion | Medium | Medium — reputational damage; user loss | Top-50-by-market-cap filter excludes most; weekly universe refresh; optionally add a manual exclusion list for known meme tokens |
| User acquisition: product does not reach PMF signal volume | Medium | High — insufficient data to evaluate success metrics | Define minimum meaningful cohort size for 60-day review before launch; set acquisition channel strategy before launch (not a blocker, but a risk) |
| LLM provider pricing change | Low | Medium — cost impact | Multi-provider evaluation before launch reduces lock-in; monitor provider pricing quarterly |
| Competitor copies pipeline design | Low | Low-Medium | Speed of execution and brand trust are the moat; pipeline sophistication and tuning accumulate as defensible advantage |

---

## 14. Open Questions and Decisions Required

The following items require a decision from a named stakeholder before the referenced milestone. Items marked **BLOCKING** must be resolved before the first line of code is written for the affected component.

| # | Question | Decision Needed From | Blocking? | Target Resolution |
|---|---|---|---|---|
| 1 | Does the product as described require RIA registration or any other regulatory approval before launch? | Legal counsel | BLOCKING (launch) | Before development begins |
| 2 | Which LLM provider — Anthropic Claude or OpenAI GPT-4o — is selected for production Agent 3? | Product + Engineering (after structured evaluation) | BLOCKING (Agent 3 development) | Before Agent 3 sprint begins |
| 3 | What are the exact weighting formulas for Candidate Score (Agent 2) and Momentum Score (Agent 1)? | Data Science Lead | BLOCKING (Agent 1 and Agent 2 development) | Week 2 of development |
| 4 | What is the approved data budget per month? | Founder / Finance | BLOCKING (data provider contracts) | Before development begins |
| 5 | Is the MVP free tier fully open (no paywalling of any features), or is the watchlist limit (10) the only restriction? | Product | BLOCKING (dashboard feature gating development) | Before frontend development begins |
| 6 | What is the meme coin exclusion policy? Manual exclusion list, market cap rank only, or additional quality criteria? | Product + Data Science | Non-blocking for launch | Before nightly pipeline first runs |
| 7 | Does the email digest default to opted-in or opted-out for new users? | Product + Legal | Non-blocking but affects CAN-SPAM/GDPR compliance design | Before email system development |
| 8 | Which equity data provider — Polygon.io or Alpaca — is selected? | Engineering | Non-blocking initially (either works) | Before Agent 2 data integration sprint |
| 9 | What is the business model for Phase 2 paid tier (price points, feature list)? | Founder | Non-blocking for MVP | Before 60-day go/no-go review |
| 10 | What is the policy for early user pricing / grandfathering into a future paid tier? | Founder | Non-blocking for MVP | Before any public announcement of paid tier |

---

## 15. Go / No-Go Blockers

The following conditions must all be satisfied before the product is released to any external user, including a private beta:

1. **Legal sign-off obtained in writing.** Counsel has reviewed the product description, disclaimer language, and Terms of Service and has confirmed the product does not require RIA registration (or the required registration is complete).

2. **Data provider agreements confirmed.** Contracts or API terms with all Tier 1 data providers (equity, crypto, news, fundamentals) have been reviewed and usage rights for the intended purpose are confirmed.

3. **LLM provider selected and tested.** A structured evaluation of at least two LLM providers has been completed. A human review panel has rated >= 20 sample rationales against quality rubric. The selected provider meets the quality bar.

4. **Candidate Score weighting formula defined and implemented.** The data science lead has signed off on the formula. Agent 2 Candidate Scores are deterministic and documented.

5. **Disclaimer layer implemented and verified.** All required disclaimer placements listed in Section 12.2 have been implemented, verified by QA, and reviewed by legal.

6. **End-to-end pipeline test completed.** At least one full pipeline run (Agent 1 → Agent 2 → Agent 3) has been executed against live data, produced >= 5 candidates with rationales, and the output has been manually reviewed for quality by the product lead.

7. **Security review completed.** Authentication flow, API endpoint authorization, secrets management, and rate limiting have been reviewed by an engineer not responsible for their implementation. No critical or high-severity findings are open.

8. **Graceful degradation verified.** QA has tested and confirmed that: (a) a failed Agent 3 run causes the dashboard to serve the previous valid output with the staleness banner; (b) a user with no pipeline output ever sees an appropriate empty state message and not a blank screen.

---

## 16. Dependencies

| Dependency | Type | Impact if Blocked | Owner |
|---|---|---|---|
| Legal counsel review | External | Launch blocked | Founder |
| Polygon.io API contract | External | Agent 2 equity data blocked | Engineering |
| CoinGecko API access | External | Agent 1/2 crypto data blocked | Engineering |
| Benzinga News API contract | External | Agent 1 sentiment blocked | Engineering |
| Financial Modeling Prep API contract | External | Agent 2 fundamentals blocked | Engineering |
| Anthropic or OpenAI API key | External | Agent 3 development blocked | Engineering |
| AWS infrastructure provisioning | Internal | All deployment blocked | Engineering |
| Data science lead availability (formula sign-off) | Internal | Agent 1 and 2 accuracy unvalidated | Product |
| SendGrid or AWS SES account setup | Internal | Email digest blocked | Engineering |

---

*End of Document*

*This PRD represents the product requirements as understood on 2026-04-30. It is a living document and will be versioned as decisions are made and the product evolves. All changes to Must Have requirements after the development sprint begins require sign-off from both Product and Engineering leads.*
