# CLAUDE.md

Guidance for working with the sentics monorepo using Claude Code.

## Project Architecture

This is a monorepo with two Vercel deployments:

### 1. `sentics-sti` (Frontend)
- **Framework**: Next.js
- **Location**: Root directory (`/`)
- **Vercel Project**: https://sentics-sti.vercel.app
- **Purpose**: Web UI for the sentics platform
- **Env Vars**: API endpoints, analytics, etc. (define as needed)

### 2. `sentics-agents` (Backend API)
- **Framework**: FastAPI (Python)
- **Location**: `/api` directory
- **Vercel Project**: https://sentics-agents.vercel.app
- **Purpose**: Agent pipeline orchestration service
- **Entrypoint**: `api/app.py`
- **Required Env Vars** (set in Vercel project settings):
  - `SUPABASE_URL` — Supabase database URL
  - `SUPABASE_SECRET_KEY` — Supabase API key
  - `ANTHROPIC_API_KEY` — Anthropic API key for agents
  - `REDIS_URL` — Redis instance for caching
  - `SENTRY_DSN` — Optional, for error tracking

**Data Sources:**
- All market data: CoinGecko free tier (market cap, categories, OHLCV, BTC dominance)
- Caching: Redis (12h TTL on OHLCV to minimize API calls)

### Library Structure

- `/api/lib/agents/` — Agent pipeline logic
  - `agent2.py` — Candidate discovery & technical filtering (deterministic TA;
    owns `direction` / `time_horizon` / `confidence_tier` / `candidate_score` /
    `trade_plan` — the ground truth downstream stages must never override)
  - `agent3.py` — Claude synthesis: writes rationale/narrative fields only.
    Enforces a `NARRATIVE_KEYS` whitelist before merging so it can never
    clobber Agent 2's fields.
  - `agent4.py` — Claude news/catalyst classification (FA). Blends into
    conviction via `combine_ta_fa()` but by design never flips Agent 2's
    direction.
  - `agent4_graph.py` — LangGraph reconciliation on top of agent4: when a
    catalyst's sentiment meaningfully disagrees with the TA direction, Claude
    is given a tool (`get_symbol_track_record`, reading the `call_snapshots`
    ledger) it can choose to call before finalizing its read. Falls back to
    the plain agent4 classification on any failure.
  - `utils.py` — Shared utilities (API calls, database, logging)
  - (Agent 1 / category-momentum scoring was retired — Agent 2 now analyzes
    the top-25-by-market-cap universe directly. Don't resurrect Agent 1
    references or assume a `category_momentum` scoring stage still runs.)
- `/api/scripts/eval_calls.py` — leak-free forward-tracking eval harness;
  scores live directional calls against realized returns (edge/hit-rate/
  Sharpe/t-stat). Reads the same `call_snapshots` ledger `agent4_graph.py`'s
  tool queries.
- `/api/requirements.txt` — Python dependencies for Vercel

## Invariants a reviewer should enforce

- **TA is ground truth.** No change to `agent3.py` or `agent4.py`/
  `agent4_graph.py` should let Claude-generated fields override
  `direction`, `time_horizon`, `confidence_tier`, `candidate_score`, or
  `trade_plan`. Flag any PR that merges LLM output without going through
  a whitelist.
- **Never break the pipeline.** Every per-candidate LLM call (agent3, agent4,
  reconciliation) must degrade gracefully — catch its own exceptions and fall
  back to a neutral/prior result — rather than raising and failing the whole
  batch.
- **Point-in-time integrity.** `call_snapshots` and FA snapshots are an
  append-only, immutable ledger (never upsert/mutate past rows) — this is
  what makes the eval harness leak-free. Flag any change that updates or
  deletes existing rows instead of appending.
- **Serverless time limits.** Stages that fan out over many candidates
  (agent3, the FA batch stage) must stay chunked/self-chaining or bounded by
  `MAX_WORKERS` — flag anything that would let a single invocation run
  unbounded.

## Deployment Notes

- Frontend deploys automatically on commits to main branch (Next.js)
- Backend deploys to `/api` directory via Vercel Python builder
- Agent pipeline endpoint: `POST /api/run-pipeline?trigger_type=manual|scheduled`
- Cron job scheduled at 15:00 UTC daily (configured in root `vercel.json`)
