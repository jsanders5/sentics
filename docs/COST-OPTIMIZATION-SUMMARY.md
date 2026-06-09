# Cost Optimization Summary: Original vs. Revised Phase 1 Budget

**Date:** June 9, 2026

---

## The Challenge

Original Phase 1 budget: **$1,200/month**  
Revised budget: **$100–150/month**  
**Savings: ~$1,050/month (88% reduction)**

The original plan assumed:
- 6 scheduled runs/day + hourly conditionals
- AWS ECS Fargate infrastructure
- CoinGecko Pro API
- Real-time data freshness requirements

For MVP validation, these assumptions were over-provisioned.

---

## Key Decisions Changed

| Decision | Original | Revised | Rationale |
|---|---|---|---|
| **Run Frequency** | 6×/day + hourly conditionals | 1×/day @ 10 AM EST | Traders check 1–2x/day; MVP validates product, not real-time precision |
| **CoinGecko API** | Pro plan ($129/mo) | Free tier ($0) | 1 run/day = 7.2K calls/month (fits free tier cap of ~10K) |
| **Frontend** | AWS ECS Fargate | Vercel Free tier | Same capabilities; Vercel auto-scales at no cost for MVP load |
| **Database** | AWS RDS | Supabase Free tier | 500MB free; MVP candidate list << 500MB |
| **Cache** | Redis (Upstash paid) | Upstash Free tier | 10K commands/day sufficient for 1 daily run + manual triggers |
| **Agent Execution** | ECS Fargate ($150–250) | AWS Lambda ($1–5) | Same Python code; Lambda cheaper for batch workloads |
| **Data Freshness** | 6-hour max (€50.59-hour SLA) | 24-hour acceptable | Validate hit rate with stale data; upgrade if user feedback demands real-time |
| **Manual Trigger** | Not included | Added | Users can force update anytime; costs ~$0.20 per run (user pays) |

---

## Cost Comparison

### Original Plan: $1,200/month

| Component | Cost | Driver |
|---|---|---|
| CoinGecko Pro | $129 | 500 calls/min rate limit (for 21.6K calls/month) |
| CryptoPanic | $99 | News/rankings API |
| Anthropic Claude | $100 | 6 Agent 3 runs/day × ~150 tokens per candidate |
| AWS ECS Fargate | $200 | Agent containers + scheduling (always-on capacity planning) |
| AWS RDS | $40 | Managed PostgreSQL (minimum tier) |
| Redis | $15 | Upstash paid tier |
| Buffer/contingency | $300 | 25% safety margin |
| **TOTAL** | **$1,200** | Over-provisioned for MVP |

### Revised Plan: $100–150/month

| Component | Cost | Driver |
|---|---|---|
| CoinGecko Free | $0 | 7.2K calls/month (fits free tier) |
| NewsAPI Free | $0 | 3K calls/month (fits free tier) |
| Anthropic Claude | $50–100 | 1 Agent 3 run/day × ~25 candidates × ~150 tokens per rationale |
| AWS Lambda | $1–5 | ~30 invocations/month (scheduled + manual) |
| Supabase Free | $10–20 | 500MB free; overage only if > limit |
| Upstash Free | $0 | 10K commands/day (usual MVP traffic) |
| Buffer/contingency | $20 | 10% safety margin |
| **TOTAL** | **$80–125/month** | Conservative ceiling: $150 |

---

## What You Lose (And Why It's OK)

### ❌ Real-Time Signals
- Original: BTC flash crash (8% 1h drop) → pipeline re-runs within 5 min
- Revised: BTC flash crash → picked up at next 10 AM EST run (up to 24h delay)
- **Why it's fine:** MVP user cohort (100 traders) likely checks dashboards 1–2x/day, not watching for flash crashes. Validate with real users; upgrade later if needed.

### ❌ Hourly Conditional Updates
- Original: Category volume explodes 3x → Agent 1 re-runs
- Revised: Detected at 10 AM run next day
- **Why it's fine:** Same reasoning. Plus: you save $129/month by not needing CoinGecko Pro's fast update cadence.

### ❌ Data Freshness SLA
- Original: Data guaranteed < 6 hours old
- Revised: Data 6–24 hours old (depends on when user last checked vs. 10 AM run)
- **Why it's fine:** Backtest will validate hit rate with stale data. If degradation < 2%, no upgrade needed. If traders complain, you know to upgrade by day 45.

---

## What You Gain

### ✅ Rapid MVP Launch
- No ECS cluster setup (saves 1 week of DevOps work)
- No RDS provisioning (Supabase free tier is instant)
- Deploy to Vercel: just push to main branch

### ✅ Cost Control & Flexibility
- If product fails at day 60: you've only spent ~$9,000 total ($150 × 60 days), not $72,000 ($1,200 × 60)
- If product succeeds: upgrade infrastructure incrementally as revenue validates spend
- No commitment to expensive services (kill switch: delete Vercel app, close Lambda, shutdown Supabase)

### ✅ Focus on Product, Not Ops
- Fewer services = fewer things to break
- Fewer credentials to manage (no ECS cluster, no RDS failover)
- Post-launch: team focuses on users, not infrastructure scaling

### ✅ Manual Trigger Feature
- Users feel in control ("I can force an update if needed")
- Traders with high conviction trades can refresh without waiting for 10 AM
- Cost is transparent: "This will cost $0.20 in API fees"

---

## Risk Mitigation

### Risk: "We need real-time updates and CoinGecko Free can't handle it"

**Mitigation 1 (Early Detection):** During backtest, validate hit rate with 24h stale data. If degradation > 2%, flag risk immediately.

**Mitigation 2 (Day 45 Decision):** If user feedback says "data is too stale," add CoinGecko Pro ($129) without losing face. You've already validated PMF and can afford it.

**Mitigation 3 (Manual Trigger):** Users can force updates ad-hoc. If power-traders hammer the button 10x/day, you'll see it in CloudWatch costs and know to upgrade.

### Risk: "Supabase free tier hits 500MB and we're stuck"

**Mitigation 1:** Auto-archive `pipeline_runs` table records > 90 days (not critical data).

**Mitigation 2:** Monitor usage weekly; if trending toward 500MB, upgrade to Supabase Pro ($25/month) with plenty of headroom.

**Mitigation 3:** Emergency pivot: migrate to AWS RDS (1 day of work) if needed.

---

## Decision Gates & Upgrade Triggers

### Day 15: Backtest Results
- **If:** Hit rate with 24h stale data >= 53% (vs. 55% target)
- **Then:** Proceed with current plan; no CoinGecko Pro needed yet
- **Else:** Investigate; consider upgrading CoinGecko Pro early

### Day 45: User Feedback & Cost Review
- **If:** Users request real-time updates (25%+ feedback) AND you're confident in revenue
- **Then:** Add CoinGecko Pro ($129/month); scale to 4× daily runs
- **Else:** Keep daily schedule; continue manual trigger model

### Day 60: Go/No-Go Review
- **If:** 3+ success metrics on track (retention, hit rate, DAU, NPS)
- **Then:** Greenlight Phase 2; budget Phase 2 at $500–800/month with better infrastructure
- **Else:** Pivot or extend Phase 1 with revised product hypothesis

---

## Infrastructure Upgrade Path (If Needed)

### Scenario 1: "Hit Rate is Good, But Users Want Real-Time"
- Add CoinGecko Pro: +$129/month
- Increase run frequency: 6× daily (cost: +$30/month LLM inference)
- Keep everything else the same
- **New budget:** $150 + $159 = **~$310/month**

### Scenario 2: "DAU > 500, Need Better Uptime"
- Upgrade Vercel to Pro: +$20/month
- Upgrade Supabase to Pro: +$25/month
- Add CloudFlare Pro for DDoS protection: +$20/month
- Migrate Lambda to Lambda Concurrency Reserved: +$10/month
- **New budget:** $150 + $75 = **~$225/month**

### Scenario 3: "Equities Launch Imminent (Phase 2)"
- Add equities data API (AlphaVantage, IEX, Polygon): +$100–200/month
- Scale ECS Fargate (more agents, more frequent runs): +$200/month
- Add production-grade database (AWS RDS): +$100/month
- **New budget:** **~$500–800/month**

All of these are informed decisions made **after** validating product-market fit, not upfront commitments.

---

## Implementation Checklist

- [ ] **June 9:** Approve $150/month budget ceiling; authorize technical specs
- [ ] **June 10–12:** Verify CoinGecko Free API can handle 7.2K calls/month (contact their support)
- [ ] **June 13–15:** Backtest with 24h stale data; confirm < 2% hit rate degradation
- [ ] **June 16:** Dev team spins up Vercel project, Supabase DB, Lambda function
- [ ] **June 20:** Deploy to staging; full pipeline test against live CoinGecko
- [ ] **June 25:** Manual trigger feature implemented & tested
- [ ] **June 30:** Launch Phase 1 to 50 beta users
- [ ] **July 15 (Day 45):** Review user feedback; decide CoinGecko Pro upgrade
- [ ] **August 8 (Day 60):** Go/no-go review; plan Phase 2 or pivot

---

**Decision Owner:** Product & Finance  
**Prepared by:** Cost optimization review (June 9, 2026)
