# Sentics Trading Intelligence — Agent Onboarding Workflow

This document outlines how to use the 9 specialized agents throughout the build process for Phase 1 of Sentics Trading Intelligence.

---

## Phase 1: Pre-Development (Weeks 1–2)

### 1.1 Architecture & Design Phase

**Goal:** Lock down technical architecture and design direction before engineering starts.

**Agent Sequence:**

1. **Crypto Product Manager** — Validate the PRD assumptions
   - Are user personas accurate?
   - Are success metrics realistic (55% hit rate, 40% DAU/MAU)?
   - Should Phase 1 launch with pre-trade planning reference, or defer to Phase 1.1?
   - What's the minimum user cohort for 60-day go/no-go review?
   - Output: Product roadmap + prioritized feature list

2. **FinTech Compliance Specialist** — Identify regulatory blockers
   - Which top-50 coins face elevated securities classification risk?
   - Does the analysis model constitute "investment advice" requiring RIA registration?
   - What disclaimers are legally defensible?
   - Output: Coin exclusion/inclusion list + disclaimer language + legal risk assessment

3. **AI Agent Architecture Specialist** — Design the pipeline
   - How should agents couple (database-first vs. direct calls)?
   - What are failure modes and graceful degradation strategies?
   - Should we batch LLM calls or invoke sequentially?
   - What's the optimal cost per pipeline run?
   - Output: Agent architecture diagram + input/output schemas + failure mode matrix

4. **Data Science ML Specialist** — Validate scoring formulas
   - What backtesting data is available (3–5 years of historical OHLCV)?
   - What are projected hit rates for each time horizon?
   - How should on-chain signal boosts be weighted?
   - Output: Backtesting results + formula validation report + confidence intervals

5. **Crypto Data Engineering Specialist** — Design data pipelines
   - What's the data ingestion architecture from CoinGecko, CryptoPanic, Glassnode?
   - How do we handle rate limits and API failures?
   - What's the monthly cost for each data source?
   - Output: Data pipeline diagram + cost breakdown + fallback strategies

6. **Infrastructure DevOps Specialist** — Plan infrastructure
   - What AWS resources are needed (ECS, EventBridge, RDS, Redis)?
   - How do we containerize agents?
   - What's the cost estimate?
   - Output: Infrastructure diagram + cost estimate + operational runbooks (draft)

7. **UI/UX Designer (FinTech)** — Design the dashboard
   - What's the information hierarchy (what matters most to traders)?
   - How do we layout three panels (categories, table, filters)?
   - What's the responsive design strategy (desktop, tablet, mobile)?
   - Output: Wireframes + design system specs + component library (draft)

**Deliverables at end of Phase 1.1:**
- [ ] Legal sign-off on disclaimers and coin universe
- [ ] Architecture diagram (agents, data flow, infrastructure)
- [ ] Scoring formula with backtesting results (hit rate >= 55% projected)
- [ ] Data pipeline design with cost estimates
- [ ] Infrastructure plan with AWS cost estimate
- [ ] Dashboard wireframes + responsive design specs

---

## Phase 2: Development Kickoff (Week 3)

### 2.1 Team Allocation & Sprint Planning

**Engineer assignments:**
- **Backend/Data:** Crypto Data Engineering Specialist input → Engineer builds ETL pipelines + database schema
- **Backend/Agents:** AI Agent Architecture Specialist input → Engineer builds Agent 1, 2, 3 containers
- **DevOps:** Infrastructure DevOps Specialist input → Engineer sets up AWS, CI/CD, monitoring
- **Frontend:** Full-Stack Crypto Engineer input → Engineer builds dashboard UI
- **QA:** QA Test Automation Specialist input → QA designs test suite

**Daily standups:** Each engineer briefs the relevant specialized agent on blockers and decisions.

---

## Phase 3: Implementation (Weeks 4–10)

### 3.1 Agent 1 Implementation (Crypto Category Trend)

**Engagement sequence:**

1. **AI Agent Architecture Specialist** provides detailed spec for Agent 1:
   - Input contract: what price/volume/sentiment data is required
   - Output schema: category_scores with exact fields
   - Failure modes: what happens if CoinGecko is down?
   - Cost optimization: how to minimize API calls?

2. **Crypto Data Engineering Specialist** provides data pipeline for Agent 1:
   - How to fetch hourly OHLCV from CoinGecko
   - How to calculate sentiment scores from news APIs
   - How to detect macro shifts (BTC dominance, market cap)
   - Data quality checks and validation rules

3. **Data Science ML Specialist** provides formula validation:
   - Correct formula weights (50% price / 35% volume / 15% sentiment)
   - How to calculate weighted averages across category members
   - Macro adjustment thresholds (BTC dominance > 2pp, market cap decline > 5%)

4. **Engineer implements** based on specs from above agents

5. **QA Test Automation Specialist** designs tests:
   - Unit tests for scoring formula (verify math)
   - Integration tests with live CoinGecko data
   - Failure tests (CoinGecko timeout, missing data)
   - Acceptance criteria: output matches expected schema, scores are between 0–100

6. **Infrastructure DevOps Specialist** provides serverless setup:
   - Vercel Serverless Function (Python 3.11 runtime)
   - Vercel Cron rule: **10 AM EST daily** (primary schedule)
   - Manual trigger via admin dashboard API (Vercel Function on-demand)
   - Logging setup: Vercel Logs + Sentry for error tracking
   - Cost tracking: Vercel free tier (included, no additional cost)

**Checkpoint:** Agent 1 passes all tests and produces valid category scores with >= 55% projected hit rate. **Note: Validate hit rate with 24h stale data (tolerance: < 2% degradation vs. 6-hour-fresh projection).**

---

### 3.2 Agent 2 Implementation (Crypto Discovery)

**Engagement sequence:**

1. **AI Agent Architecture Specialist** provides Agent 2 spec:
   - Input: Agent 1 output (categories >= 55) + price/volume for all coins
   - Filters: RSI 40–72, volume >= 1.3x, price >= both MAs
   - On-chain boost: +5 for active addresses, +3 for net flow, +4 for whale activity
   - Output: up to 50 candidates ranked by score

2. **Data Science ML Specialist** backtests each filter:
   - Does RSI 40–72 correlate with forward momentum?
   - Does volume >= 1.3x reduce false positives?
   - Does MA positioning matter?
   - Recommended tuning adjustments based on backtest results

3. **Crypto Data Engineering Specialist** provides on-chain data integration:
   - How to fetch active addresses, exchange flow, whale tx from Glassnode
   - Data availability expectations (BTC/ETH high, smaller coins sparse)
   - On-chain signal interpretation (what each metric means)

4. **Engineer implements** Agent 2 based on validated filters

5. **QA Test Automation Specialist** validates:
   - Technical filters work as specified
   - On-chain boosts applied only when data available
   - Up to 50 candidates output, ranked by score
   - Edge case: fewer than 5 candidates triggers "Low signal environment"

**Checkpoint:** Agent 2 produces valid candidate list with accurate technical/on-chain scoring.

---

### 3.3 Agent 3 Implementation (Forward-Looking Synthesis)

**Engagement sequence:**

1. **AI Agent Architecture Specialist** provides Agent 3 spec:
   - LLM provider: Claude (default) or GPT-4o (alternative)
   - Prompt structure: symbol metadata + quantitative signals + news + macro context → time horizon + confidence + rationale
   - Output schema: strict JSON with entry_type, confidence_tier, time_horizon, rationale_text, etc.
   - Cost control: 6 runs/day max, batch calls if possible

2. **Data Science ML Specialist** defines quality metrics:
   - Hit rate target: >= 55% per time horizon
   - Confidence tier calibration: High/Medium/Low should map to 60%/55%/45% hit rates
   - Time horizon accuracy: Short candidates should hit within 1–7 days, etc.
   - Entry quality tiers: Strong/Moderate/Speculative mapping

3. **Crypto Data Engineering Specialist** provides input data:
   - Candidate-level metrics from Agent 2
   - Last 48 hours of news headlines + sentiment
   - Protocol events from CoinGecko Events API
   - Macro context (BTC dominance, market cap trend, category momentum)

4. **Engineer builds Agent 3 prompt** (with guidance from all three agents above):
   - Structured prompt that produces consistent JSON output
   - Instructions to cite technical + narrative + on-chain signals
   - Time horizon and confidence tier definitions
   - Meme coin confidence ceiling (Medium max)

5. **Engineer evaluates LLM provider:**
   - Test Claude (Sonnet) vs. GPT-4o on 20 sample candidates
   - Human review panel (2+ reviewers) rates quality
   - Compare latency and cost
   - Select based on quality + cost trade-off

6. **QA Test Automation Specialist** validates:
   - Schema compliance: every candidate has required fields
   - Rationale quality: cites signals, no hallucinations
   - Time horizon accuracy: Short candidates resolve within 1–7 days (testable post-launch)
   - Meme coin cap enforced: High confidence never assigned to meme coins

**Checkpoint:** Agent 3 produces high-quality rationales with >= 55% projected hit rate.

---

### 3.4 Dashboard Implementation

**Engagement sequence:**

1. **UI/UX Designer (FinTech)** provides full design specs:
   - Three-panel layout (categories, candidates table, detail panel)
   - Responsive design for desktop/tablet/mobile
   - Color palette, typography, component specs
   - Interaction patterns (sort, filter, open detail panel, close on Escape)

2. **Full-Stack Crypto Engineer** implements:
   - Next.js/React frontend (Vercel deployment)
   - Upstash Redis cache integration (90-min TTL, free tier)
   - Supabase PostgreSQL (free tier + pay-as-you-go)
   - Client-side filtering (AND logic across time horizon/category/confidence)
   - Detail panel modal/drawer with smooth open/close
   - **Manual "Force Update" button** in staleness banner → calls `/api/trigger-pipeline` (Lambda on-demand)
   - Last updated timestamp visible; next scheduled update shown (10 AM EST)

3. **Infrastructure DevOps Specialist** provisions:
   - **Frontend:** Vercel Free tier (auto-scaling, serverless functions included)
   - **Backend Functions:** Vercel Serverless Functions (Python 3.11 runtime)
   - **Scheduling:** Vercel Cron (built-in, no external service)
   - **Cache:** Upstash Free tier (10K commands/day)
   - **Database:** Supabase Free tier (500MB, pay-as-you-go after)
   - **Logging:** Vercel Logs + Sentry (free tier error tracking)
   - **Monitoring:** Vercel Analytics + Sentry performance tracking (built-in)
   - Manual trigger endpoint: `/api/trigger-pipeline` (Vercel Function, async)

4. **QA Test Automation Specialist** validates:
   - Responsiveness: desktop/tablet/mobile layouts correct
   - Performance: LCP <= 2.5s, CLS <= 0.1 (Lighthouse audit)
   - Filtering: 300ms client-side response
   - Accessibility: WCAG 2.1 Level AA (contrast, keyboard nav, screen reader)
   - Disclaimers: all four appear on correct surfaces

**Checkpoint:** Dashboard loads in < 3 seconds, filters work smoothly, accessibility verified.

---

### 3.5 Admin Dashboard Implementation

**Engagement sequence:**

1. **Infrastructure DevOps Specialist** specifies internal monitoring UI:
   - Last 48 hours of pipeline run logs
   - Error visibility
   - Threshold status
   - Alert escalation

2. **Engineer builds** internal admin dashboard:
   - Authentication (admin-only access)
   - Run log table with relevant fields (scheduled + manual trigger runs)
   - **Manual Trigger button:** Force immediate Agent 1 → 2 → 3 run (Vercel Function on-demand)
   - Error drill-down with full stack traces (integrated with Sentry)
   - Category threshold visualization (Agent 1 scores vs. 55 threshold)
   - Cost tracking: Vercel function invocations, API call count, LLM tokens consumed
   - System health status: Last successful run time, error rate, uptime indicator

3. **QA Test Automation Specialist** verifies:
   - Only admins can access
   - Run logs display correctly
   - Errors are visible and actionable

**Checkpoint:** Admins can monitor pipeline health and debug failures.

---

## Phase 4: Integration & Testing (Weeks 11–14)

### 4.1 End-to-End Testing

**QA Test Automation Specialist** leads:

1. **Full pipeline test** (Agent 1 → 2 → 3):
   - Against live CoinGecko data
   - Verify output quality
   - Measure latency (target: < 40 min)

2. **Event-triggered run tests:**
   - Simulate BTC flash crash (8% move)
   - Simulate category volume explosion (3x average)
   - Simulate major news spike
   - Verify conditional execution

3. **Graceful degradation tests:**
   - Disable Redis → dashboard falls back to database
   - Disable CoinGecko → uses fallback (CoinMarketCap)
   - Agent 3 fails for 9+ candidates → previous output served
   - Verify staleness banner displays

4. **Performance tests:**
   - Lighthouse audit (LCP, CLS targets)
   - Synthetic monitoring (latency, uptime)
   - Load test (100 concurrent users)

5. **Accessibility tests:**
   - WCAG 2.1 Level AA scan
   - Keyboard navigation
   - Screen reader testing

6. **Security tests:**
   - HTTPS enforcement
   - Rate limiting (100 req/min per IP)
   - No sensitive data in logs
   - API key handling (Secrets Manager)

**Checkpoint:** All tests pass; system is stable and reliable.

---

### 4.2 Go/No-Go Blocker Verification

**QA Test Automation Specialist** verifies all Section 15 blockers:

- [ ] **Legal sign-off:** Written confirmation from counsel
- [ ] **Data provider agreements:** CoinGecko, CryptoPanic, Glassnode, Anthropic terms confirmed
- [ ] **LLM provider selected:** Claude or GPT-4o evaluated and chosen
- [ ] **Scoring formula validated:** Data Science Lead sign-off on weights
- [ ] **Disclaimers implemented:** All four on correct surfaces, legally reviewed
- [ ] **End-to-end pipeline test:** Full run completed, output reviewed, quality verified
- [ ] **Security review:** No critical/high-severity findings open
- [ ] **Graceful degradation verified:** All failure scenarios tested and passing

**Checkpoint:** Ready for launch.

---

## Phase 5: Launch & Post-Launch (Weeks 15–16+)

### 5.1 Launch Week

**FinTech Compliance Specialist** — Final legal clearance

**Infrastructure DevOps Specialist** — Prod deployment, monitoring activation

**QA Test Automation Specialist** — Final smoke tests in production

**Crypto Product Manager** — Beta user recruitment (minimum cohort size from Phase 1)

**Checkpoint:** Live with real users.

---

### 5.2 Post-Launch Monitoring

**Infrastructure DevOps Specialist** — Daily monitoring:
- Uptime (target: >= 99.5%)
- Pipeline success rate (target: >= 95%)
- Error rates
- Alert response time

**Data Science ML Specialist** — Weekly performance tracking:
- Hit rate calculation (observed vs. projected)
- Time horizon accuracy
- Confidence tier calibration
- Tuning recommendations

**Crypto Product Manager** — User feedback loop:
- Retention metrics (7-day, 30-day)
- Feature usage
- User cohort size tracking
- Feedback on pain points

**QA Test Automation Specialist** — Regression testing:
- Critical path testing after each deployment
- Performance regression monitoring
- Incident investigation

**Checkpoint at 60 days:** Go/No-Go review (target: 3+ of 4 success metrics on track).

---

## Quick Reference: When to Engage Which Agent

| Question / Decision | Agent to Engage |
|---|---|
| **"Does this model require RIA registration?"** | FinTech Compliance Specialist |
| **"Should we include XRP in the coin universe?"** | FinTech Compliance Specialist + Crypto Product Manager |
| **"How should Agent 2 and Agent 3 communicate?"** | AI Agent Architecture Specialist |
| **"Are these technical filter thresholds correct?"** | Data Science ML Specialist |
| **"What data do we need to fetch from CoinGecko?"** | Crypto Data Engineering Specialist |
| **"How do we handle a CoinGecko API outage?"** | Crypto Data Engineering Specialist + Infrastructure DevOps Specialist |
| **"Should we defer pre-trade planning reference to Phase 1.1?"** | Crypto Product Manager |
| **"What should dashboard latency targets be?"** | Full-Stack Crypto Engineer + Infrastructure DevOps Specialist |
| **"Is the dashboard accessible to screen readers?"** | QA Test Automation Specialist + UI/UX Designer |
| **"How do we containerize and deploy agents?"** | Infrastructure DevOps Specialist |
| **"What's the projected hit rate for this formula?"** | Data Science ML Specialist |
| **"Is the dashboard responsive on mobile?"** | UI/UX Designer + QA Test Automation Specialist |
| **"How do we monitor pipeline failures?"** | Infrastructure DevOps Specialist + QA Test Automation Specialist |

---

## Communication Cadence

**Weekly:**
- **All agents + engineers:** Standups (15 min) to surface blockers
- **Crypto Product Manager + Crypto Data Engineering Specialist + AI Agent Architecture Specialist:** Design sync (30 min)

**Bi-weekly:**
- **All agents:** Architecture/design review (1 hour)
- **Data Science ML Specialist + QA Test Automation Specialist:** Testing strategy sync

**Monthly:**
- **All agents + leadership:** Product roadmap review (1 hour)
- **Data Science ML Specialist:** Post-launch metrics review (if live)

---

## Escalation Paths

**Architecture decision blocked?** → AI Agent Architecture Specialist + leadership

**Regulatory question unresolved?** → FinTech Compliance Specialist → external counsel

**Performance targets can't be met?** → Infrastructure DevOps Specialist + Full-Stack Crypto Engineer + leadership

**Hit rate projection falls short?** → Data Science ML Specialist + Crypto Product Manager (may need formula tuning or scope adjustment)

---

## Success Criteria

Phase 1 is complete when:

1. All agent recommendations have been implemented or explicitly deferred
2. All go/no-go blockers (Section 15, PRD) are verified and passing
3. At least 3 of 4 success metrics are on track at 60-day review
4. Team has high confidence in the product's reliability and accuracy
5. No critical unresolved regulatory, technical, or design risks remain

---

## Document Maintenance

- Update this workflow as agents evolve or new agents are added
- Log decisions made per agent (helps future retrospectives)
- Archive decision logs monthly (helps pattern recognition)
- Review workflow effectiveness quarterly (are agents being used effectively?)
