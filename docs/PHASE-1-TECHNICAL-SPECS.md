# Sentics Trading Intelligence — Phase 1 Technical Specifications

**Date:** June 9, 2026  
**Version:** 1.0  
**Status:** Ready for development  

---

## Executive Summary

Phase 1 is a **cost-optimized MVP** running on free/cheap cloud tiers with a single daily scheduled update (10 AM EST) plus manual on-demand triggering capability. The target is rapid validation of product-market fit with <$150/month operating costs, not production scale.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    User Browser (Client)                     │
└─────────────────┬───────────────────────────────────────────┘
                  │ HTTPS
                  ▼
┌─────────────────────────────────────────────────────────────┐
│              Frontend (Vercel)                               │
│  ├─ Next.js/React dashboard                                 │
│  ├─ Client-side filtering (TH, category, confidence)        │
│  ├─ Staleness banner + [Force Update] button                │
│  └─ "Last updated 10 AM EST" timestamp                      │
└─────┬────────────────────────────────┬──────────────────────┘
      │ Read cache (Upstash Redis)     │ API calls
      │                                │
      ▼                                ▼
┌──────────────────────┐   ┌────────────────────────────────┐
│ Cache Layer          │   │ API Lambda Functions            │
│ (Upstash Free)       │   │ - GET /candidates             │
│ ├─ Candidates TTL 90 │   │ - GET /categories             │
│ │   min              │   │ - POST /api/trigger-pipeline  │
│ └─ Fresh? Latest run │   └────┬─────────────────────────────┘
└──────────┬───────────┘        │
           │                    │
           ▼                    ▼
      ┌──────────────────────────────────┐
      │ Database (Supabase Free)         │
      │ ├─ candidates table              │
      │ ├─ categories table              │
      │ ├─ pipeline_runs log             │
      │ └─ users/sessions (Phase 2)      │
      └──────────────────────────────────┘
           ▲
           │ Writes
           │
      ┌────┴─────────────────────────────┐
      │                                   │
      ▼                                   ▼
┌──────────────────────┐   ┌──────────────────────┐
│ EventBridge          │   │ Manual Trigger API   │
│ Cron Rule            │   │ (Lambda on-demand)   │
│ ├─ 10 AM EST daily   │   │ Cost: ~$0.20/call    │
│ └─ Invokes Agent 1   │   │ (user accepts cost)  │
└──────────┬───────────┘   └──────────┬───────────┘
           │                          │
           └────────────┬─────────────┘
                        │
                        ▼
      ┌─────────────────────────────────┐
      │ Agent Pipeline (AWS Lambda)      │
      │ ├─ Agent 1: Category Momentum    │
      │ ├─ Agent 2: Candidate Discovery  │
      │ └─ Agent 3: AI Synthesis (Claude)│
      └────────────┬────────────────────┘
                   │
                   ▼
      ┌─────────────────────────────────┐
      │ External APIs (Free/Pro tiers)   │
      │ ├─ CoinGecko Free API            │
      │ ├─ NewsAPI Free (sentiment)      │
      │ └─ Anthropic Claude API          │
      └─────────────────────────────────┘
```

---

## Component Details

### 1. Frontend (Vercel Free Tier)

**Stack:**
- Framework: Next.js 14 (React 18)
- Deployment: Vercel (free tier, auto-scaling)
- UI Library: Shadcn/ui or equivalent (accessible components)
- Styling: Tailwind CSS
- State: React hooks (client-side filtering only)

**Key Features:**
- Three-panel dashboard layout (categories, candidates table, detail panel)
- Client-side filtering: time horizon, category, confidence tier
- Detail panel modal/drawer with smooth animations
- Staleness banner: "Last updated 10 AM EST. [Force Update] button."
- All disclaimers prominently displayed (footer, modal, per-rationale)

**Performance Targets:**
- LCP (Largest Contentful Paint): <= 2.5s
- CLS (Cumulative Layout Shift): <= 0.1
- FID/INP: <= 200ms
- **Measurement:** Vercel Analytics (built-in), lighthouse-ci on builds

**Accessibility:**
- WCAG 2.1 Level AA (minimum)
- Keyboard navigation (Tab, Shift+Tab, Escape)
- Screen reader labels (aria-label, aria-labelledby)
- Color contrast >= 4.5:1 for text

### 2. Cache Layer (Upstash Redis Free Tier)

**Configuration:**
- Plan: Free tier (10K commands/day, usually sufficient)
- Region: Same as Vercel (us-east-1 default)
- TTL: 90 minutes (refresh at 10:30 AM EST; latest data served until ~12 PM)

**Data Cached:**
- Full candidates list (last Agent 3 output) — key: `candidates:latest`
- Category scores (last Agent 1 output) — key: `categories:latest`
- Last update timestamp — key: `last_update_ts`

**Fallback:** If Redis down or cache miss, queries PostgreSQL directly (slower, but works)

**Cost:** $0 (within free tier for MVP traffic)

### 3. Database (Supabase Free Tier)

**Configuration:**
- Plan: Free tier (500MB storage, shared infrastructure)
- Region: us-east-1
- Backups: Daily automatic (7-day retention)

**Tables:**

| Table | Columns | Purpose | Retention |
|---|---|---|---|
| `candidates` | symbol, name, category, time_horizon, confidence_tier, score, rationale, entry_type, entry_quality, updated_at | Latest Agent 3 output | Current + 1 backup |
| `categories` | name, momentum_score, macro_adjustment, updated_at | Latest Agent 1 output | Current + 1 backup |
| `pipeline_runs` | run_id, trigger_type (scheduled/manual), agents_run, start_time, end_time, status (success/failed), error_msg | Audit log for admin dashboard | 90 days (cost control) |
| `sessions` | session_id, user_agent, created_at, last_activity_at | For Phase 2 user tracking | 30 days (auto-delete) |

**Scaling:**
- If free tier hits 500MB: archive old `pipeline_runs` records (delete > 90 days)
- If queries slow: add Supabase indices on `updated_at`, `category`
- Cost cap: $50/month overage before alerting

### 4. Agent Pipeline (AWS Lambda)

**Configuration:**
- Function: `STI-Agent-Pipeline` (single function, sequential execution)
- Memory: 1024 MB (sufficient for Python environment)
- Timeout: 600 seconds (10 min max for full run)
- Ephemeral storage: 512 MB (for intermediate data)
- Runtime: Python 3.11
- VPC: None (Lambda not in VPC to minimize latency)

**Environment Variables:**
```
COINGECKO_API_KEY=<free tier key>
NEWSAPI_KEY=<free tier key>
ANTHROPIC_API_KEY=<secret from Secrets Manager>
DATABASE_URL=<Supabase connection string, from Secrets Manager>
REDIS_URL=<Upstash connection URL, from Secrets Manager>
AGENT_ENV=production
LOG_LEVEL=INFO
```

**Execution Flow:**
1. Receive trigger (scheduled or manual)
2. Agent 1: Fetch CoinGecko data → calculate category momentum scores
3. Agent 2: Filter candidates (RSI, volume, MA) → rank by score
4. Agent 3: Invoke Claude API for rationales (async batch, up to 25 at a time)
5. Write to PostgreSQL + invalidate Redis cache
6. Return: run_id, candidate count, execution time

**Error Handling:**
- Timeouts: Write partial results if Agent 3 times out (use previous rationales for missing candidates)
- API failures: Log and alert; do NOT write invalid data to database
- Retry logic: 3 attempts with exponential backoff for transient errors

**Cost:**
- Lambda: Free tier = 1M invocations/month (we use ~30 for daily + manual triggers)
- Actual cost: < $1/month

### 5. Scheduled Execution (EventBridge)

**Cron Rule:**
```
cron(0 15 * * ? *)    # 10 AM EST = 3 PM UTC, daily
```

**Trigger:**
- Target: Lambda function `STI-Agent-Pipeline`
- Input: `{"trigger_type": "scheduled", "force": false}`
- Retry: 1 attempt (no retries for scheduled runs; manual retry via button)
- DLQ: Send failed invocations to SQS queue for manual inspection

**Alerting:**
- Failure: CloudWatch event → SNS → Slack notification to #ops channel

### 6. Manual Trigger API (API Gateway + Lambda)

**Endpoint:**
```
POST /api/trigger-pipeline
Headers:
  Authorization: Bearer <admin_token>
  Content-Type: application/json
Body:
  {
    "force": true
  }
```

**Response:**
```json
{
  "run_id": "run_20260609_153042",
  "status": "queued",
  "estimated_cost": "$0.20",
  "estimated_duration_seconds": 120,
  "message": "Pipeline triggered. Check status at /admin/runs/{run_id}"
}
```

**Implementation:**
- Auth: API key stored in Secrets Manager; validate before execution
- Rate limit: Max 5 manual triggers per hour per user (prevent abuse)
- Cost notification: Response shows estimated inference cost upfront
- Async execution: Return immediately; client polls `/admin/runs/{run_id}` for status

**Cost per Invocation:**
- Lambda execution: negligible
- CoinGecko API calls: ~$0.000 (free tier)
- Claude inference: ~$0.15–0.25 depending on candidate count + rationale length
- **User sees:** "This will cost approximately $0.20. Continue? [Yes] [Cancel]"

### 7. Admin Dashboard

**Features:**
- **Auth:** Admin email + password (no OAuth for MVP)
- **Run Logs:** Last 48 hours of pipeline runs (scheduled + manual)
  - Columns: Run ID, Trigger Type, Status, Start Time, Duration, Candidate Count, Errors (if any)
  - Filtering: by date, status, trigger type
  - Detail: Click row → see full logs, error stack trace
- **Manual Trigger:** Big red button: "Force Update Now" → confirm cost → execute
- **Category Scores:** Real-time display of latest Agent 1 scores (vs. 55 threshold)
- **Cost Tracking:** Running total for month, breakdown by Lambda + API + LLM
- **Status:** Green/yellow/red indicator for system health (based on last successful run time)

**Access:** `/admin` (protected by auth middleware)

### 8. Data Flow Example (10 AM EST Daily Run)

1. **EventBridge triggers** Lambda at 10 AM EST
2. **Agent 1 runs:**
   - Fetch last 30 days of hourly OHLCV for top 50 coins (CoinGecko Free)
   - Fetch BTC dominance, market cap (CoinGecko Free)
   - Calculate: Price momentum, Volume momentum, Macro adjustment
   - Output: 10–20 categories with scores >= 55
3. **Agent 2 runs:**
   - For each passing category, fetch all coins in that category
   - Filter: RSI 40–72, Volume >= 1.3x 24h avg, Price >= both 20d and 50d MA
   - Score: 50% technical + 50% category momentum (on-chain removed for Phase 1)
   - Output: Up to 50 ranked candidates
4. **Agent 3 runs:**
   - For each candidate: invoke Claude with structured prompt
   - Inputs: symbol, price, technicals, category momentum, recent news
   - Output: time_horizon, confidence_tier, rationale (50–300 words)
   - Batch up to 25 at a time (stay under token limits)
5. **Write to database:**
   - `candidates` table: All candidates from Agent 3
   - `categories` table: Agent 1 category scores
   - `pipeline_runs` table: Metadata (timestamps, status, counts)
6. **Invalidate cache:**
   - Delete `candidates:latest` and `categories:latest` from Redis
   - Next API request will re-populate cache from fresh database read
7. **Send success notification:**
   - Slack message: "Pipeline succeeded. 47 candidates, 18 categories. Updated at 10:05 AM EST."

---

## Data Freshness & User Experience

### Staleness Model

| Time Since Update | Data Status | Indicator | Action |
|---|---|---|---|
| < 2 hours | Fresh | (none) | Latest data served from cache |
| 2–12 hours | Stale | Yellow banner: "Last updated [time]. Next update: 10 AM EST." | Data served; button visible |
| > 12 hours | Very Stale | Red banner: "Data is > 12 hours old. Please [Force Update]." | Old data served; strong CTA |

### User Can Force Update Anytime
- Dashboard shows: "Last updated 10 AM EST. [Force Update] button."
- User clicks → modal: "Force an immediate update? This will cost ~$0.20 in API + LLM costs. [Continue] [Cancel]"
- After confirmation → Lambda runs Agent 1 → 2 → 3, takes ~2 min
- Dashboard refreshes automatically once complete (polling or WebSocket)

---

## Cost Breakdown

| Component | Est. Monthly Cost | Notes |
|---|---|---|
| Vercel (frontend) | $0 | Free tier sufficient for MVP |
| Supabase (database) | $10–20 | Free tier + overages if > 500MB |
| Upstash (cache) | $0 | Free tier (10K cmds/day) |
| AWS Lambda | < $1 | ~30 invocations/month (scheduled + manual) |
| CoinGecko API | $0 | Free tier (7.2K calls/month @ 1×/day) |
| NewsAPI | $0 | Free tier (3K calls/month) |
| Anthropic Claude | $50–100 | Variable: ~25 candidates × 1 run/day × ~150 tokens per rationale |
| **TOTAL** | **$60–130/month** | Conservative budget: $150/month ceiling |

---

## Scaling & Decision Gates

### Day 45 Decision: CoinGecko Pro?

| Condition | Decision | Rationale |
|---|---|---|
| User feedback: "Update too stale, can't act on yesterday's data" | Upgrade CoinGecko Pro (+$129) | Product feedback drives infrastructure spend |
| Hit rate validation: < 2% degradation vs. projected | Keep free tier | Stale data is acceptable; no upgrade needed |
| DAU > 150 AND hit rate on track | Consider 2×/day runs (4×/day max) | Increase frequency with validated product |

### Day 60 Decision: Scale or Pivot?

| Metric | Target | If Hit | Action |
|---|---|---|---|
| **Retention (7-day)** | >= 40% | ✅ | Proceed to Phase 2 |
| **Hit rate** | >= 55% (Medium horizon) | ✅ | Lock formula; plan backtest validation |
| **DAU** | >= 100 | ✅ | Scale infrastructure incrementally |
| **NPS** | >= 40 | ✅ | Refine messaging; plan equities expansion |

If 3+ metrics on track → greenlight Phase 2 planning.

---

## Monitoring & Alerts

### CloudWatch Metrics

| Metric | Target | Alert Threshold |
|---|---|---|
| Pipeline success rate | >= 95% | < 90% for 2 consecutive runs |
| Lambda execution time | < 180s | > 300s |
| Database query latency | < 500ms p95 | > 1s p95 |
| Cache hit rate | >= 90% | < 80% |
| Cost (running total) | <= $150/mo | > $200 run rate |

### Slack Alerts

- **Pipeline Success:** "✅ Pipeline complete. 47 candidates, 18 categories, 2m 15s."
- **Pipeline Failure:** "❌ Pipeline failed at Agent 3 (Claude API timeout). Previous data served. [View Logs]"
- **Cost Alert:** "💰 Cost trend: $180/month projected (vs. $150 budget). Review usage."

### Admin Dashboard Health Indicator

- 🟢 Green: Last successful run < 2 hours ago
- 🟡 Yellow: Last successful run 2–12 hours ago
- 🔴 Red: Last successful run > 12 hours ago OR last 3 runs all failed

---

## Security

### API Key Management
- All keys stored in **AWS Secrets Manager** (never in code or `.env` files)
- Rotated quarterly
- Access logged to CloudTrail

### Authentication
- Admin dashboard: email + password + TOTP (optional, Phase 1.1)
- Public dashboard: no auth required (free product, no login)

### Network
- HTTPS enforced (Vercel auto-handles)
- Rate limiting: 100 requests/min per IP (Vercel middleware or custom Lambda)
- No sensitive data in logs (API keys, user data stripped)

### Data Privacy
- Session IDs: server-side tracking (no cookies storing PII)
- No user account data Phase 1 (all-anonymous usage)
- Logs: 30-day retention, auto-delete

---

## Deployment & CI/CD

### Git Workflow
- Branch: `main` (always deployable)
- PRs: Required review before merge to main
- Deploy: Vercel auto-deploys on merge to main
- Lambda: Manual deploy via AWS CLI (post-testing)

### Testing Before Deploy
- Unit tests: Agent scoring logic (Python unittest)
- Integration tests: Full pipeline against live CoinGecko Free API (AWS SAM local)
- Frontend tests: React component rendering (Jest)
- E2E tests: Dashboard load → filter → detail panel open (Playwright, weekly post-launch)

### Rollback
- Frontend: Vercel auto-rollback to previous deployment (one-click)
- Lambda: Manual version management; keep previous version for 1-week rollback window
- Database: Daily automated backups (Supabase); manual restore if needed

---

## Runbook: Common Issues

### "Pipeline hasn't run in 6+ hours"
1. Check CloudWatch EventBridge rule execution history
2. Check Lambda execution logs (`/aws/lambda/STI-Agent-Pipeline`)
3. If CoinGecko API down: Check CoinGecko status page
4. Manual trigger: Click [Force Update] in admin dashboard
5. If still failing: Page on-call engineer

### "Dashboard says 'stale data > 12 hours'"
1. Check last successful pipeline run in admin dashboard
2. If last run failed: Check error logs
3. Likely cause: CoinGecko API rate limit or Claude API quota
4. Mitigation: Click [Force Update] to retry

### "Force Update costs $1.50 instead of $0.20?"
1. Likely: Claude API pricing changed or candidate count inflated
2. Check: How many candidates did Agent 2 pass to Agent 3?
3. If > 50: Something is wrong with Agent 2 filters; investigate
4. If normal: Update cost estimate in UI or reduce candidate count

---

## Next Steps Before Development

- [ ] Approve $150/month budget ceiling
- [ ] Verify CoinGecko Free API: confirm 7.2K calls/month fits (contact their support if unclear)
- [ ] Verify Supabase free tier: confirm 500MB storage + overage pricing
- [ ] Set up AWS account structures (Secrets Manager, Lambda, EventBridge, CloudWatch)
- [ ] Create Vercel project skeleton
- [ ] Legal review: Confirm no RIA registration required (Q1 decision)
- [ ] Prepare backtest data: Validate hit rate with 24h stale data (tolerance: < 2% degradation)

---

**Prepared by:** Engineering team based on cost-optimized architecture decision (June 9, 2026)
