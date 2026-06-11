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

- `/api/lib/agents/` — Agent code (Agent 1, 2, 3 pipeline logic)
  - `agent1.py` — Category momentum scoring
  - `agent2.py` — Candidate discovery & technical filtering
  - `agent3.py` — Candidate synthesis & rationale generation
  - `utils.py` — Shared utilities (API calls, database, logging)
- `/api/requirements.txt` — Python dependencies for Vercel

## Deployment Notes

- Frontend deploys automatically on commits to main branch (Next.js)
- Backend deploys to `/api` directory via Vercel Python builder
- Agent pipeline endpoint: `POST /api/run-pipeline?trigger_type=manual|scheduled`
- Cron job scheduled at 15:00 UTC daily (configured in root `vercel.json`)
