# Sentics Trading Intelligence — Phase 1 Technical Specifications

**Date:** June 9, 2026  
**Version:** 2.0 (AWS-Free)  
**Status:** Ready for development  

---

## Executive Summary

Phase 1 is a **cost-optimized, AWS-free MVP** running entirely on Vercel + Supabase with a single daily scheduled update (10 AM EST) plus manual on-demand triggering. The target is rapid validation of product-market fit with <$150/month operating costs, minimal vendor lock-in, and zero AWS complexity.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    User Browser                              │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS
                       ▼
┌──────────────────────────────────────────────────────────────┐
│          Frontend + Backend (Vercel)                          │
│  ├─ Next.js/React dashboard                                  │
│  ├─ Vercel Serverless Functions (Python)                     │
│  │   ├─ GET /api/candidates                                  │
│  │   ├─ GET /api/categories                                  │
│  │   ├─ POST /api/trigger-pipeline (async, user-initiated)   │
│  │   └─ Scheduled handlers (Vercel Cron)                     │
│  └─ Vercel built-in logging + analytics                      │
└──────┬──────────────────────────┬────────────────┬───────────┘
       │                          │                │
       │ Redis cache reads        │ DB reads       │ Cron events
       │ (Upstash Free)           │                │
       ▼                          ▼                ▼
   ┌────────────┐   ┌──────────────────────┐  ┌──────────────┐
   │ Upstash    │   │ Database             │  │ Vercel Cron  │
   │ Redis      │   │ (Supabase Free)      │  │              │
   │ ├─ 10K     │   │ ├─ candidates        │  │ 10 AM EST    │
   │ │ cmds/day │   │ ├─ categories        │  │ daily        │
   │ └─ 90min   │   │ ├─ pipeline_runs     │  │              │
   │   TTL      │   │ └─ sessions (Ph 2)   │  │ Triggers:    │
   └──────┬─────┘   └──────────┬───────────┘  │ /api/run-    │
          │                    │               │ pipeline     │
          └────────────┬───────┴───────────────┘ (async)      │
                       │                         └──────┬─────┘
                       │
                       ▼
      ┌─────────────────────────────────────┐
      │ Agent Pipeline (Vercel Functions)    │
      │ (Python 3.11 runtime)                │
      │                                      │
      │ ├─ Agent 1: Category Momentum        │
      │ │   Input: CoinGecko price/volume    │
      │ │   Output: category scores >= 55    │
      │                                      │
      │ ├─ Agent 2: Candidate Discovery      │
      │ │   Input: category scores + coins   │
      │ │   Output: up to 50 ranked coins    │
      │                                      │
      │ └─ Agent 3: AI Synthesis             │
      │     Input: candidates + context      │
      │     Output: rationales (Claude API)  │
      │                                      │
      │ All errors → Sentry (logging)        │
      └────────────┬─────────────────────────┘
                   │
                   ▼
      ┌─────────────────────────────────────┐
      │ External APIs                        │
      │ ├─ CoinGecko Free API                │
      │ ├─ NewsAPI Free (sentiment)          │
      │ └─ Anthropic Claude API              │
      └─────────────────────────────────────┘
```

---

## Component Details

### 1. Frontend (Vercel Next.js)

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

### 2. Backend: Vercel Serverless Functions

**Configuration:**
- Runtime: Python 3.11 or Node.js (Python for agent code)
- Memory: 1024 MB (sufficient for agent pipeline)
- Timeout: 600 seconds (10 min max for full run)
- Ephemeral storage: 512 MB (for intermediate data)

**Functions:**

| Endpoint | Method | Purpose | Runtime |
|---|---|---|---|
| `/api/candidates` | GET | Fetch latest candidates from database/cache | < 500ms |
| `/api/categories` | GET | Fetch latest category scores | < 500ms |
| `/api/trigger-pipeline` | POST | Manually trigger full Agent 1 → 2 → 3 run | Async, 2–3 min |
| `/api/run-pipeline` (internal) | POST | Scheduled executor (called by Vercel Cron) | Async, 2–3 min |

**Environment Variables (in Vercel dashboard):**
```
COINGECKO_API_KEY=<free tier key>
NEWSAPI_KEY=<free tier key>
ANTHROPIC_API_KEY=<secret>
DATABASE_URL=<Supabase connection string>
REDIS_URL=<Upstash connection URL>
SENTRY_DSN=<sentry error tracking>
AGENT_ENV=production
LOG_LEVEL=INFO
```

**Error Handling:**
- Timeouts: Write partial results if Agent 3 times out (use previous rationales for missing candidates)
- API failures: Log to Sentry; do NOT write invalid data to database
- Retry logic: 3 attempts with exponential backoff for transient errors

**Cost:** Free tier sufficient for MVP (up to 100 function invocations/month free, we use ~30)

### 3. Scheduled Execution (Vercel Cron)

**Configuration:**
- Built-in Vercel Cron (no external service needed)
- Add file: `vercel.json` at project root

```json
{
  "crons": [
    {
      "path": "/api/run-pipeline",
      "schedule": "0 15 * * *"
    }
  ]
}
```

**Cron Rule:**
```
0 15 * * *    # 10 AM EST = 3 PM UTC, every day
```

**Execution:**
1. Vercel invokes `/api/run-pipeline` at 10 AM EST
2. Function starts Agent 1 → 2 → 3 pipeline
3. Returns immediately (async job)
4. Results written to database when complete

**Alerting:**
- On failure: Send error to Sentry (automatic)
- Slack integration via Sentry (configured in Sentry dashboard)

### 4. Cache Layer (Upstash Redis Free Tier)

**Configuration:**
- Plan: Free tier (10K commands/day, usually sufficient)
- Region: us-east-1 (same as Vercel default)
- TTL: 90 minutes (refresh at 10:30 AM EST; latest data served until ~12 PM)

**Data Cached:**
- Full candidates list (last Agent 3 output) — key: `candidates:latest`
- Category scores (last Agent 1 output) — key: `categories:latest`
- Last update timestamp — key: `last_update_ts`

**Fallback:** If Redis down or cache miss, queries PostgreSQL directly (slower, but works)

**Cost:** $0 (within free tier for MVP traffic)

### 5. Database (Supabase Free Tier)

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

### 6. Agent Pipeline Execution Flow

**Trigger:** Either scheduled (Vercel Cron @ 10 AM EST) or manual (user clicks [Force Update])

**Execution (Python 3.11 in Vercel Function):**

1. **Agent 1: Category Momentum**
   - Fetch last 30 days of hourly OHLCV for top 50 coins (CoinGecko Free)
   - Fetch BTC dominance, market cap (CoinGecko Free)
   - Calculate: Price momentum, Volume momentum, Macro adjustment
   - Output: 10–20 categories with scores >= 55
   - Latency: ~30–45 seconds

2. **Agent 2: Candidate Discovery**
   - For each passing category, fetch all coins in that category
   - Filter: RSI 40–72, Volume >= 1.3x 24h avg, Price >= both 20d and 50d MA
   - Score: 50% technical + 50% category momentum
   - Output: Up to 50 ranked candidates
   - Latency: ~30–45 seconds

3. **Agent 3: AI Synthesis**
   - For each candidate: invoke Claude with structured prompt
   - Inputs: symbol, price, technicals, category momentum, recent news
   - Output: time_horizon, confidence_tier, rationale (50–300 words)
   - Batch up to 25 at a time (stay under token limits)
   - Latency: ~60–120 seconds (depends on Claude API response time)

4. **Write Results:**
   - `candidates` table: All candidates from Agent 3
   - `categories` table: Agent 1 category scores
   - `pipeline_runs` table: Metadata (timestamps, status, counts)

5. **Invalidate Cache:**
   - Delete `candidates:latest` and `categories:latest` from Redis
   - Next API request will re-populate cache from fresh database read

6. **Logging:**
   - All errors, timing, API call counts → Sentry (automatic)
   - Function logs → Vercel Logs (automatic)
   - DB query logs → Supabase Logs (visible in Supabase dashboard)

**Total Execution Time:** 2–3 minutes

---

## Logging & Monitoring Strategy

### Vercel Logs (Built-In)

**What you see:**
- All function execution logs (stdout/stderr)
- HTTP request/response details
- Function duration + memory usage
- Cold start information
- Errors and exceptions

**Access:** Vercel dashboard → Project → Deployments → [Function name] → Logs

**Cost:** Free, included with all plans

### Sentry (Free Tier)

**What you see:**
- Error tracking + stack traces
- Exception grouping (so duplicate errors show once)
- Release tracking (which code version caused error)
- Breadcrumbs (events leading up to error)
- User context (if you add it)
- Performance monitoring (function duration, API latency)

**Setup:**
```python
import sentry_sdk
sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))

try:
  # Your code here
except Exception as e:
  sentry_sdk.capture_exception(e)
```

**Alerts:**
- Error threshold exceeded: Slack notification
- New error type: Email notification
- Performance degradation: Slack notification

**Cost:** Free tier = 5,000 events/month (more than enough for MVP)

### Supabase Logs

**What you see:**
- Database query logs (in dashboard)
- Edge Function execution logs (if using Supabase Edge Functions)
- Realtime subscription events

**Access:** Supabase dashboard → Project → Logs → Edge Function Logs / Database Logs

**Cost:** Free, included with all plans

### Vercel Analytics (Built-In)

**What you see:**
- Web Vitals (LCP, CLS, FID, INP)
- Real User Monitoring (from actual users)
- Time to First Byte (TTFB)
- Function response times by endpoint

**Access:** Vercel dashboard → Project → Analytics

**Cost:** Free, included with all plans

---

## Manual Trigger (User-Initiated Updates)

**UI Flow:**
1. User sees: "Last updated 10 AM EST. [Force Update] button." (in yellow banner)
2. User clicks [Force Update]
3. Modal appears: "Force an immediate update? This will cost approximately $0.20 in API + LLM costs. [Continue] [Cancel]"
4. User clicks [Continue]
5. POST `/api/trigger-pipeline` → Function queued
6. Page shows: "Update in progress... (usually takes 2–3 minutes)"
7. Dashboard refreshes automatically once complete (polling or WebSocket)

**Implementation:**
- Auth: Admin email + password (no OAuth for MVP)
- Rate limit: Max 5 manual triggers per hour per user (prevent abuse)
- Cost tracking: Cost estimate shown before user confirms
- Async execution: POST returns immediately; client polls `/api/run-status/{run_id}` for progress

---

## Data Freshness & User Experience

### Staleness Model

| Time Since Update | Data Status | Indicator | User Action |
|---|---|---|---|
| < 2 hours | Fresh | (none) | Latest data served from cache |
| 2–12 hours | Stale | Yellow banner: "Last updated [time]. Next update: 10 AM EST. [Force Update]" | Data served; button visible |
| > 12 hours | Very Stale | Red banner: "Data is > 12 hours old. Please [Force Update]." | Old data served; strong CTA |

### User Can Force Update Anytime
- Dashboard shows: "Last updated 10 AM EST. [Force Update] button."
- User clicks → cost confirmation
- Pipeline runs immediately (~2–3 min)
- Dashboard refreshes once complete

---

## Cost Breakdown

| Component | Est. Monthly Cost | Notes |
|---|---|---|
| Vercel (frontend + functions) | $0 | Free tier sufficient for MVP |
| Supabase (database) | $10–20 | Free tier + overages if > 500MB |
| Upstash (cache) | $0 | Free tier (10K cmds/day) |
| Sentry (error tracking) | $0 | Free tier (5K events/month) |
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

### Sentry Error Alerts
- Error rate threshold: > 10 errors/day → Slack notification
- New error type detected → Email notification
- Error regression (same error after fix) → Slack notification

### Vercel Function Monitoring
- Function timeout (> 300s): Logged to Sentry, Slack notification
- Cold start time: Tracked in Vercel Analytics
- Memory usage: Vercel tracks; alert if > 900MB consistently

### Database Health
- Query latency p95 > 1s: Check Supabase logs
- Storage approaching 500MB: Upgrade to Pro or archive old runs
- Connection pool exhausted: Supabase admin alerts

### Cost Tracking
- Vercel dashboard: View function execution counts
- Supabase dashboard: View storage + overage usage
- Sentry dashboard: View event quota usage

---

## Security

### Environment Variables (Vercel)
- All API keys stored in Vercel Environment Variables (not in `.env.local`)
- Keys available only to functions, not exposed to client
- Rotated quarterly via Vercel dashboard
- Audit log: Vercel tracks who accessed which secret when

### Authentication
- Admin dashboard: Email + password (no OAuth for MVP)
- Public dashboard: No auth required (free product, all-anonymous)
- Session management: Server-side session IDs (Phase 2)

### Network
- HTTPS enforced by default (Vercel)
- Rate limiting: Vercel middleware (100 requests/min per IP)
- No sensitive data in logs (API keys, user data stripped)
- Log retention: 30 days (Vercel auto-deletes)

### Data Privacy
- Session IDs: Server-side tracking (no PII in browser)
- No user account data Phase 1 (all-anonymous usage)
- Logs: 30-day retention by default (Sentry, Vercel)

---

## Deployment & CI/CD

### Git Workflow
- Branch: `main` (always deployable)
- PRs: Required review before merge to main
- Deploy: Vercel auto-deploys on merge to main (automatic)
- Functions: Updated automatically with main branch

### Testing Before Deploy
- Unit tests: Agent scoring logic (Python pytest)
- Integration tests: Full pipeline against live CoinGecko Free API
- Frontend tests: React component rendering (Jest)
- E2E tests: Dashboard load → filter → detail panel (Playwright, weekly post-launch)

### Rollback
- Frontend: Vercel auto-rollback to previous deployment (one-click)
- Functions: Vercel version management; keep previous version for 1-week rollback window
- Database: Daily automated backups (Supabase); manual restore if needed

### Monitoring Deployments
- Vercel dashboard: See all deployments + logs
- Sentry: Track errors per release (shows which code version caused issue)
- Analytics: Real User Monitoring shows if users affected by new version

---

## Runbook: Common Issues

### "Pipeline hasn't run in 6+ hours"
1. Check Vercel Cron execution: Vercel dashboard → Crons
2. Check Vercel Function logs: See error details
3. If CoinGecko API down: Check CoinGecko status page
4. Manual trigger: Click [Force Update] in admin dashboard
5. If still failing: Check Sentry for error details

### "Dashboard says 'stale data > 12 hours'"
1. Check last successful pipeline run in admin dashboard
2. If last run failed: Check Sentry for error logs
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
- [ ] Verify CoinGecko Free API: confirm 7.2K calls/month fits (contact their support)
- [ ] Set up Sentry account (free tier, takes 5 min)
- [ ] Create Vercel project from Next.js template
- [ ] Create Supabase project (free tier)
- [ ] Create Upstash Redis instance (free tier)
- [ ] Legal review: Confirm no RIA registration required (Q1 decision)
- [ ] Prepare backtest data: Validate hit rate with 24h stale data (tolerance: < 2% degradation)

---

**Architecture:** 100% Vercel + Supabase (zero AWS complexity)  
**Prepared by:** Engineering team (June 9, 2026)
