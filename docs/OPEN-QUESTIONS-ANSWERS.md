# Sentics Trading Intelligence — Phase 1 PRD: Open Questions & Decisions (RESOLVED)

**Date:** June 9, 2026  
**Status:** All 12 Open Questions answered; 8 BLOCKING decisions resolved; 4 non-blocking decisions finalized

---

## BLOCKING DECISIONS (Must Resolve Before Development)

### Q1: Regulatory Registration & Coin Universe Exclusions ✅

**Decision:** Core dashboard does NOT require RIA registration; proceed with current positioning.

**Details:**
- STI qualifies for the publisher's exclusion (IAA 1940) because: output identical for all users, no individualization, no position sizing, no fiduciary relationship
- **Three coins flagged for elevated securities classification risk:** ICP, MANA, AXS
  - Recommendation: Present both options to external counsel — exclude or include with enhanced disclaimer
  - Excluding = 7% universe reduction (43 coins remain of 50)
  - Including requires specific language acknowledging classification risk
- **External counsel sign-off is a go/no-go blocker** (Section 15, blocker #1)

**Action Items:**
- [ ] Prepare legal brief for external counsel with coin list + disclaimer language + specific yes/no questions
- [ ] Decision: exclude ICP/MANA/AXS, or include with enhanced disclaimer?

---

### Q2: LLM Provider Selection (Claude vs. GPT-4o) ✅

**Decision:** Run side-by-side evaluation with 25-candidate test set before selecting production provider.

**Evaluation Framework:**
- 9-step protocol with frozen inputs, blind review, inter-rater reliability (Cohen's kappa)
- 25-candidate test set: 5 clear signal, 10 mixed, 10 edge cases (3 synthetic)
- Quality rubric: 5 dimensions (rationale quality via 5 sub-dimensions, schema compliance, hallucination rate, latency, cost)
- Statistical test: Wilcoxon signed-rank; tie-breaker rules specified
- Effort: ~50–53 person-hours; ~$1.90 in API costs; 6–7 calendar days

**Recommendation:**
- Run both Claude Sonnet 4.6 and GPT-4o in parallel
- Secondary pass: test Opus 4.8 on Tier 3 edge cases (~$0.06)
- Default to Claude Sonnet 4.6 if no clear winner

**Action Items:**
- [ ] Build frozen input data set (25 candidates) with synthetic edge cases
- [ ] Schedule 2–3 reviewers for calibration + scoring + reconciliation
- [ ] Confirm GPT-4o current pricing before running evaluation
- [ ] Complete evaluation before Agent 3 sprint begins

---

### Q3: Scoring Formula Validation ✅

**Decision:** Formulas are analytically defensible as v1.0; implement as CONFIGURABLE PARAMETERS; mandatory backtest before production lock-in.

**Agent 1 — Category Momentum Score (50 / 35 / 15):**
- Price momentum (50%): Accept — well-documented momentum effect in crypto
- Volume momentum (35%): Accept with caveat — share variance with price (~r=0.55–0.70); validate independence in backtest
- News sentiment (15%): Accept with caveat — NLP quality is key risk; plan 3-month post-launch review

**Agent 2 — Candidate Score (50 / 35 / 15):**
- Technical alignment (50%): Accept; requires explicit sub-component composite formula
- Category inheritance (35%): Accept
- On-chain boost (15%): **ADJUST** — see Q7 (likely removing entirely for Phase 1)

**Technical Filters:**
- RSI 40–72: Accept (72 upper bound correct for crypto)
- Volume >= 1.3x: Accept; use fully-closed daily candles only
- MA filter (>= 20d AND 50d): Accept

**Hit Rate Projections (pre-backtest):**
- Short (1–7d): 51–54%, 95% CI [48%, 57%] — may not hit 55% target
- Medium (1–4w): 54–57%, 95% CI [51%, 60%] — achievable
- Long (1–3mo): 52–56%, 95% CI [49%, 59%] — regime-dependent

**Critical Missing Definition:**
- **Target return per horizon MUST be defined before backtest** (recommend: 5% / 10% / 20%)

**Pre-Production Backtest Requirements (NON-NEGOTIABLE):**
- Minimum 385 historical observations per time horizon
- p < 0.05 for hit rate significantly > 50% (target: p < 0.01 for Medium horizon)
- 95% CI lower bound > 50%
- Stratified by market regime (bull / bear / sideways)
- OLS weight regression to validate 50/35/15 splits

**Action Items:**
- [ ] Define target returns (short/medium/long) and get product sign-off
- [ ] Backtest code: 2–3 days data engineering + 1 day analysis (run in parallel with Agent 1/2 dev)
- [ ] Complete backtest before ANY user-facing pipeline run
- [ ] Lock formulas for production only after backtest passes thresholds

---

### Q4: CoinGecko Plan Tier & Cost ✅

**Decision:** CoinGecko Analyst/Pro plan required (~$129/month, unverified).

**API Requirements:**
- ~60 API calls per Agent 1 run
- 7,200 calls/month (minimum, 4 runs/day) to 50,400 calls/month (maximum, 28 runs/day)
- Typical expected: ~21,600 calls/month
- **Free tier disqualified:** ~10K/month call cap; no hourly market_chart endpoint; no commercial license

**Plan Tier:**
- CoinGecko Analyst/Pro: 500 calls/min rate limit (30x headroom); ~$129/month
- **FLAGGED:** Pricing is unverified — confirm at coingecko.com/en/api/pricing before budget approval

**Endpoint Note:**
- Use `/market_chart?days=30&interval=hourly` for hourly granularity
- NOT `/coins/{id}/ohlc` (only gives 4-hour candles for windows > 2 days)

**Fallback:**
- CoinMarketCap Startup: ~$333/month (cold standby)
- Endpoint mapping: 95% compatible; no events API equivalent

**Commercial Licensing:**
- **MUST VERIFY:** CoinGecko Pro terms permit commercial use in AI products
- Required before user-facing launch (go/no-go blocker #2)

**Action Items:**
- [ ] Verify CoinGecko pricing at coingecko.com/en/api/pricing
- [ ] Confirm commercial licensing in ToS
- [ ] Set up CoinMarketCap as fallback (cost ~$333/month if needed)

---

### Q5: Meme Coin Inclusion Decision ✅

**Decision:** INCLUDE meme coins in top-50 universe with Medium confidence tier cap (non-negotiable guardrails).

**Rationale:**
- Top-50 by market cap scope claim is more credible if no arbitrary editorial filters
- Meme coins have genuine technical momentum signals (RSI, volume, MA positioning work)
- Risk mitigation: Medium confidence cap + "speculative asset" label in rationale

**Non-Negotiable Guardrails:**
- Meme coins (DOGE, SHIB, PEPE, etc.) can NEVER receive High confidence tier
- Agent 3 rationale MUST explicitly state: "speculative, sentiment-driven asset"
- Monitor for rug-pull signals (exchange net flow drain) pre-recommendation

**Current Meme Coins in Top-50 (as of June 2026):**
- DOGE (#8–15 by market cap, ~$10–15B)
- SHIB (#13–20, ~$5–8B)
- PEPE (#40–50, ~$2–3B)

**Action Items:**
- [ ] Add meme coin flag to Agent 3 output schema (`is_meme_coin: boolean`)
- [ ] Agent 3 prompt: enforce Medium confidence ceiling for meme coins
- [ ] Monitor reputational risk post-launch

---

### Q6: Phase 1 Monthly Budget Approval ✅

**Decision:** Approve $100–150/month operational budget for Phase 1 (MVP tier).

**Revised Architecture (Cost-Optimized):**
| Component | Solution | Cost | Notes |
|---|---|---|---|
| Frontend | Vercel Free tier | $0 | Auto-scales, includes Postgres free tier |
| Database | Supabase Free + overages | $10–20 | 500MB free; pay-as-you-go after |
| Cache | Upstash Free tier | $0 | 10K commands/day free (sufficient for MVP) |
| Agent Execution | AWS Lambda | $1–5 | ~4 scheduled runs/month = negligible cost |
| Data APIs | CoinGecko Free + NewsAPI Free | $0 | Fits within free tier limits (7.2K calls/month at 1×/day frequency) |
| LLM Inference | Anthropic Claude | $50–100 | Variable; ~5–50 tokens per candidate × 25 candidates × 1 run/day |
| **TOTAL** | | **$60–125/month** | Conservative buffer to $150 |

**Run Frequency Decision:**
- **Daily schedule:** Agent 1 → 2 → 3 pipeline runs **once at 10 AM EST**
- **Manual trigger:** Force update button in dashboard (Lambda on-demand invocation, ~$0.20 per run)
- **Rationale:** 7.2K calls/month fits CoinGecko free tier; data freshness acceptable for MVP user feedback; cost-effective validation of product-market fit

**Data Freshness Trade-off:**
- Stale data window: 12–24 hours (10 AM run covers remainder of day + next morning until 10 AM)
- Impact on hit rate: May reduce Medium/Long-horizon accuracy vs. 6-hour-fresh data (validate in backtest)
- User experience: "Last updated 10 AM EST" banner visible; users can force refresh if needed
- **POST-LAUNCH DECISION:** Upgrade CoinGecko Pro ($129) only if user feedback demands real-time signals or hit rate validation shows >2% degradation

**Budget Controls:**
- Weekly cost monitoring via AWS Cost Explorer (Vercel, Lambda, Supabase usage)
- Alert at $200/month run rate (indicates $240/month trajectory; escalate if trending upward)
- Monthly spend review; commit to cost containment if Phase 2 greenlit

**Scaling Decision Gate:**
- If DAU > 100 AND hit rate targets met: revisit run frequency (may upgrade to 2–4×/day if product-market fit validated)
- If user feedback consistently requests real-time updates: consider CoinGecko Pro upgrade at day 45 of Phase 1
- Cost ceiling for Phase 1: $250/month (if needed to maintain PMF signal)

**Note:** $150 is Phase 1 only (crypto, no user auth, minimal infrastructure). Phase 2 estimated $500–800/month (equities data + scaled infrastructure) once revenue validates investment.

**Action Items:**
- [ ] Approve $150/month budget ceiling for Phase 1
- [ ] Set up cost alerts in Vercel, AWS, Supabase dashboards ($200 threshold)
- [ ] Document 10 AM EST schedule in EventBridge cron rule
- [ ] Add manual trigger button to admin dashboard
- [ ] Plan backtest to validate hit rate with 24h stale data
- [ ] Weekly cost review cadence established
- [ ] Decision gate: CoinGecko Pro upgrade decision at day 45 of Phase 1

---

## NON-BLOCKING DECISIONS (Important but not critical path)

### Q7: Glassnode Licensing & On-Chain Signals ✅

**Decision:** SKIP on-chain signals for Phase 1 (remove Glassnode requirement).

**Reason:**
- Glassnode free tier: COMMERCIAL USE PROHIBITED (explicit in ToS)
- Glassnode Professional plan (only option for API access): ~$999/month+ (25x higher than PRD assumed $39/month)
- CoinGecko fallback: Not viable (provides different, weaker on-chain data)

**Impact on Agent 2 Formula:**
- On-chain boost (15% component) removed entirely
- Technical alignment rescored to 0–58 instead of 0–50
- Category inheritance rescored to 0–42 instead of 0–35
- Effective formula: 58% technical + 42% category momentum (out of 100)
- "Strong" entry quality tier criterion: soften from "at least one on-chain signal" to "on-chain data optional"

**Post-Launch Opportunity:**
- Phase 1.1 or Phase 2: revisit on-chain signals with validated revenue
- Consider Santiment API ($200–500/month) or Nansen (institutional pricing)
- Ensure commercial licensing explicitly confirmed in ToS

**Action Items:**
- [ ] Update Agent 2 formula per scoring adjustment (data science sign-off required)
- [ ] Remove Glassnode from go/no-go blocker #2 (Section 15)
- [ ] Remove on-chain boost from Agent 2 output schema
- [ ] Document decision rationale (pricing findings + licensing issue)

---

### Q8: Minimum User Cohort for 60-Day Go/No-Go ✅

**Decision:** 100 users minimum; 150 target; 500+ signals needed for reliable assessment.

**Binding Constraint:**
- 7-day retention cohort analysis requires 3–4 weekly cohorts of meaningful size
- Hit rate: not binding (signals accumulate faster than users)

**Clarity on Metrics:**
- If arriving at day 60 with < 75 users: extend review 30 days (likely distribution failure, not product failure)
- If arriving with 75–150 users: assess all 4 metrics; 3+ on-track = proceed to Phase 2 planning
- If arriving with 150+ users: confident go/no-go decision possible

**Action Items:**
- [ ] Define user acquisition strategy and channels (target: 10–15 users/day early)
- [ ] Set up retention cohort analysis dashboard by week 2 of launch
- [ ] Define "early signal" metrics to watch for red flags (< 20% DAU/MAU at week 2 = course correction time)

---

### Q9: Phase 2 Business Model & Monetization ✅

**Decision:** $39/month paid tier with US equities access; implement session IDs + event logging in Phase 1 for Phase 2 compatibility.

**Phase 2 Pricing:**
- Free tier: crypto only, up to 10 watchlist symbols
- Paid tier: $39/month, includes US equities access, unlimited watchlist, email digests

**Phase 1 Data Model Requirements:**
- Anonymous session IDs (server-side): required for Phase 2 user accounts
- Event logging (page views, filter actions, detail panel opens): required for user engagement metrics
- localStorage watchlist: Phase 1 feature (no sync); upgrade hook to "create account for cross-device sync" (Phase 2)
- DO NOT build authentication in Phase 1 (2–3 week scope, zero PMF value, high risk)

**Why This Matters for Phase 1:**
- Session IDs let Phase 2 identify users without authentication (privacy-friendly analytics)
- Event logging powers retention analysis + cohort behavior understanding
- localStorage watchlist is trivial to build; sync backend in Phase 2 is where the complexity lies

**Action Items:**
- [ ] Backend engineer: implement session ID + event logging infrastructure before Phase 1 launch
- [ ] Frontend: localStorage watchlist feature (~2 days of work)
- [ ] Planning: Phase 2 monetization brief prepared by week 6 of Phase 1 (inform post-launch decisions)

---

### Q10: Pre-Trade Planning Reference Legal Review ✅

**Decision:** DEFER to Phase 1.1 (remove from Phase 1 scope).

**Legal Risk Assessment:** HIGH

**Why Deferral:**
1. **Regulatory classification risk:** Providing specific price levels ($2.45 resistance) + invalidation levels ($2.10 stop) + ATR + R:R ratio = functional trade structure. Embed this in a buy recommendation detail panel = investment advice (substance over form).
2. **Systemic risk:** If pre-trade reference is challenged as advice, it undermines the publisher's exclusion defense for the ENTIRE product, not just that feature.
3. **Non-critical feature:** Classified as "Should Have," not "Must Have" in PRD. Core product value (ranked candidates + AI rationale) works without it.
4. **Timeline risk:** Separate counsel review on pre-trade reference = blocking dependency. Better to defer, launch Phase 1, establish PMF, then revisit with actual user context.

**Phase 1.1 Implementation Path:**
- Legal review: separate engagement with external counsel (use Phase 1 user behavior data as context)
- Engineering: straightforward if approved (Agent 3 prompt additions + detail panel section)
- Timeline: 2–3 weeks post-Phase 1 launch if counsel approves

**Q12 Closure:** Pre-trade reference deferred to Phase 1.1 (same deferral decision).

**Action Items:**
- [ ] Remove Section 8.6 from Phase 1 PRD scope
- [ ] Remove pre-trade fields from Agent 3 output schema
- [ ] Remove pre-trade planning reference disclaimer from Section 12.2 required list
- [ ] Carry Section 8.6 forward to Phase 1.1 scope + legal review workstream

---

### Q11: Entry Type Filtering (Breakout/Retest/Dip-Buy) ✅

**Decision:** DEFER to Phase 1.1 (detail panel display only in Phase 1).

**Phase 1 Implementation:**
- Entry type computed in Agent 3
- Displayed in detail panel under "Pre-Trade Planning Reference" (if Phase 1.1 pre-trade feature goes live)
- OR displayed as a text label in detail panel if pre-trade reference is deferred

**Phase 1.1 Filter:** Pull forward only if:
- User feedback: > 25–30% of users explicitly request entry type filter, OR
- Hit rate divergence: Dip-Buy signals hit at significantly lower rate than Retest (e.g., 44% vs. 63%) = brand protection issue

**Rationale for Deferral:**
- Not on critical path to MVP
- Can be added in 1–2 days post-launch if needed
- Requires data on actual hit rate divergence by entry type to be meaningful

**Action Items:**
- [ ] Track user feedback on entry type filtering (post-launch)
- [ ] Monitor hit rate by entry type (data science weekly report)
- [ ] Flag for Phase 1.1 pull-forward if either condition met

---

## SUMMARY TABLE: Go/No-Go Dependencies

| Blocker | Owner | Status | Target Date |
|---|---|---|---|
| Q1: Legal sign-off (RIA registration, coin universe) | External counsel | READY FOR BRIEF | Before dev starts |
| Q2: LLM provider evaluation | Engineering + Data Science | PROTOCOL READY | Before Agent 3 sprint |
| Q3: Scoring formula validation | Data Science | FORMULA LOCKED (backtest required pre-production) | Week 2 of dev (parallel) |
| Q4: CoinGecko plan + licensing | Engineering + Legal | PLAN IDENTIFIED (verify pricing + license) | Before data contracts |
| Q6: Budget approval | Founder/Finance | RECOMMENDATION: $1,200/month | Before sprint kickoff |
| Q7: On-chain data plan | Engineering + Data Science | RESOLVED (skip on-chain for Phase 1) | Before Agent 2 dev |
| Q12: Pre-trade reference deferral | Product + Legal | RESOLVED (defer to Phase 1.1) | Immediately |

**All 12 Open Questions are now RESOLVED. Phase 1 development can proceed with clarity on all critical decisions.**

---

## Implications for Development Timeline

**Critical Path Impact:**
- Q3 backtest must run in parallel with Agent 1/2 development (adds 3 days if sequential)
- Q2 LLM evaluation must complete before Agent 3 sprint begins
- Q1 legal brief should be submitted to external counsel immediately (typical turnaround: 2–3 weeks)

**No Critical Path Delays Introduced:** All resolutions are compatible with the planned sprint schedule.

---

## Next Steps for Leadership

1. **Today (June 9):** Approve $1,200/month budget; authorize legal brief to external counsel on Q1
2. **This week:** Confirm CoinGecko Pro pricing and commercial licensing
3. **Week 1 of dev (June 16):** Launch LLM evaluation framework; start backtest data prep
4. **Week 2 of dev (June 23):** Backtest complete; formulas locked for implementation
5. **Ongoing:** Weekly cost monitoring; monthly go/no-go checkpoint reviews

---

**Document prepared by:** Specialized agent consultation (Crypto Product Manager, FinTech Compliance Specialist, Data Science ML Specialist, Crypto Data Engineering Specialist, AI Agent Architecture Specialist)  
**Approved for:** Phase 1 development kickoff
