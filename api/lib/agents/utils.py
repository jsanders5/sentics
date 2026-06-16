"""
Shared utilities for STI agents.
Handles: API calls, database operations, caching, logging.
"""

import os
import json
import time
import requests
import redis
import sentry_sdk
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from decimal import Decimal

# ---------------------------------------------------------------------------
# Category definitions
# ---------------------------------------------------------------------------
# CATEGORIES: Internal category name -> representative coin IDs used by
# Agent 1 to calculate category momentum scores.  These are intentionally
# small samples (3-5 liquid, high-cap coins per category) to keep API call
# volume low during momentum scoring.
#
# Agent 2 does NOT use this for coin discovery — it calls the CoinGecko
# /coins/markets?category=<id> endpoint so that all coins in a category are
# covered, not just these representatives.
CATEGORIES: Dict[str, List[str]] = {
    "Layer 1":  ["bitcoin", "ethereum", "solana", "cardano", "avalanche-2"],
    "Layer 2":  ["arbitrum", "optimism", "polygon", "starknet"],
    "DeFi":     ["uniswap", "aave", "curve-dao-token", "maker"],
    "AI":       ["fetch-ai", "render-token", "bittensor", "near"],
    "Exchange": ["binancecoin", "okb", "kucoin-shares"],
    "Gaming":   ["gala", "immutable-x", "beam-2"],
    "Meme":     ["dogecoin", "shiba-inu", "pepe"],
}

# CATEGORY_TO_COINGECKO_ID: Translates internal category names to CoinGecko's
# category ID taxonomy, used with /coins/markets?category=<id>.
# Verify IDs at: https://api.coingecko.com/api/v3/coins/categories/list
CATEGORY_TO_COINGECKO_ID: Dict[str, str] = {
    "Layer 1":  "layer-1",
    "Layer 2":  "layer-2",
    "DeFi":     "decentralized-finance-defi",
    "AI":       "artificial-intelligence",
    "Exchange": "exchange-based-tokens",
    "Gaming":   "gaming",
    "Meme":     "meme-token",
}

def get_category_for_coin(coin_id: str) -> str:
    """Map a coin ID to its internal category using the representative sample.
    Returns 'Other' if the coin is not in any representative list.
    Note: use CoinGecko category endpoint for exhaustive membership checks."""
    for category, coins in CATEGORIES.items():
        if coin_id in coins:
            return category
    return "Other"

# Initialize Sentry
sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))

# Supabase REST API config
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY")

def get_supabase_headers() -> Dict:
    """Get headers for Supabase REST API requests."""
    return {
        "apikey": SUPABASE_SECRET_KEY,
        "Authorization": f"Bearer {SUPABASE_SECRET_KEY}",
        "Content-Type": "application/json"
    }

# Redis cache
def get_redis_client():
    """Connect to Upstash Redis."""
    try:
        from redis import Redis
        return Redis.from_url(os.getenv("REDIS_URL"))
    except Exception as e:
        sentry_sdk.capture_exception(e)
        return None

# CoinGecko API calls
def fetch_coingecko(endpoint: str, params: Dict = None, max_retries: int = 3) -> Dict:
    """Fetch data from CoinGecko API (demo or Pro).

    Uses x-cg-demo-api-key header for demo API key.
    Throttles 1s between requests (100 calls/min limit) and retries 429/5xx
    responses with exponential backoff (honoring Retry-After) so a transient
    rate-limit doesn't silently drop a coin from the run.
    """
    url = f"https://api.coingecko.com/api/v3{endpoint}"
    headers = {}
    api_key = os.getenv("COINGECKO_API_KEY")
    if api_key:
        headers["x-cg-demo-api-key"] = api_key

    last_exc = None
    for attempt in range(max_retries):
        try:
            # Rate limiting: 1s delay between requests (100 calls/min limit)
            time.sleep(1)
            response = requests.get(url, params=params, headers=headers or None, timeout=10)

            if response.status_code == 429 or response.status_code >= 500:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else float(2 ** attempt)
                log_error(
                    f"CoinGecko {response.status_code} on {endpoint}; "
                    f"retrying in {delay:.0f}s (attempt {attempt + 1}/{max_retries})"
                )
                last_exc = requests.HTTPError(f"CoinGecko {response.status_code}")
                time.sleep(delay)
                continue

            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            last_exc = e
            time.sleep(float(2 ** attempt))

    sentry_sdk.capture_exception(last_exc)
    raise last_exc

def fetch_top_50_coins() -> List[Dict]:
    """Fetch top 50 coins by market cap (cached 12 hours)."""
    try:
        cache_key = "top_50_coins"
        cached = cache_get(cache_key)
        if cached:
            return cached

        data = fetch_coingecko("/coins/markets", {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 50,
            "page": 1,
            "sparkline": "false"
        })

        if data:
            cache_set(cache_key, {"coins": data}, ttl_minutes=720)
            return data
        return []
    except Exception as e:
        sentry_sdk.capture_exception(e)
        raise

def fetch_market_chart(coin_id: str, days: int = 30) -> Dict:
    """Fetch price and volume history for a coin from CoinGecko (with caching).

    Uses Redis caching with 12h TTL to minimize API calls.
    CoinGecko returns: { "prices": [[ts, price], ...], "total_volumes": [[ts, vol], ...] }
    Normalized to expose "volumes" key for consistency.
    """
    try:
        # Check cache first
        cache_key = f"market_chart:{coin_id}:{days}"
        cached = cache_get(cache_key)
        if cached:
            return cached

        # Fetch from CoinGecko
        data = fetch_coingecko(f"/coins/{coin_id}/market_chart", {
            "vs_currency": "usd",
            "days": days,
            "interval": "daily"
        })

        # Normalize: CoinGecko uses "total_volumes"; expose as both keys
        if "total_volumes" in data and "volumes" not in data:
            data["volumes"] = data["total_volumes"]

        # Guard against a granularity fallback (hourly instead of daily): all
        # downstream indicators assume daily candles. If the spacing looks
        # intraday, log and DON'T cache the bad series for 12h.
        prices = data.get("prices") or []
        if len(prices) >= 3:
            recent = prices[-10:]
            gaps = sorted(recent[i][0] - recent[i - 1][0] for i in range(1, len(recent)))
            median_gap = gaps[len(gaps) // 2]
            if median_gap < 43_200_000:  # < 12h between points → not daily
                log_error(
                    f"market_chart for {coin_id} returned non-daily granularity "
                    f"(median gap {median_gap / 3_600_000:.1f}h); not caching"
                )
                return data

        # Cache for 12 hours
        if prices:
            cache_set(cache_key, data, ttl_minutes=720)

        return data
    except Exception as e:
        sentry_sdk.capture_exception(e)
        raise

def fetch_btc_dominance() -> float:
    """Fetch BTC dominance percentage (cached 12 hours)."""
    try:
        cache_key = "btc_dominance"
        cached = cache_get(cache_key)
        if cached:
            return cached.get("dominance", 0)

        data = fetch_coingecko("/global")
        dominance = data.get("data", {}).get("btc_dominance", 0)

        if dominance > 0:
            cache_set(cache_key, {"dominance": dominance}, ttl_minutes=720)

        return dominance
    except Exception as e:
        sentry_sdk.capture_exception(e)
        return 0

# Database operations (via Supabase REST API)
def insert_candidates(candidates: List[Dict]):
    """Insert or update candidates in database via REST API."""
    try:
        url = f"{SUPABASE_URL}/rest/v1/candidates"
        headers = get_supabase_headers()

        headers["Prefer"] = "resolution=merge-duplicates"

        for candidate in candidates:
            data = {
                "symbol": candidate.get("symbol"),
                "name": candidate.get("name"),
                "category": candidate.get("category"),
                "market_cap": candidate.get("market_cap"),
                "price": candidate.get("price"),
                "rsi": candidate.get("rsi"),
                "volume_ratio": candidate.get("volume_ratio"),
                "technical_score": candidate.get("technical_score"),
                "category_momentum": candidate.get("category_momentum"),
                "directional_score": candidate.get("directional_score"),
                "direction": candidate.get("direction"),
                "time_horizon": candidate.get("time_horizon"),
                "confidence_tier": candidate.get("confidence_tier"),
                "score": candidate.get("score"),
                "rationale": candidate.get("rationale"),
                "key_signals": candidate.get("key_signals"),
                "entry_type": candidate.get("entry_type"),
                "entry_quality": candidate.get("entry_quality"),
                "trade_plan": candidate.get("trade_plan"),
                "fa_score": candidate.get("fa_score"),
                "sentiment": candidate.get("sentiment"),
                "catalyst": candidate.get("catalyst"),
                "fa_summary": candidate.get("fa_summary"),
                "fa_confidence": candidate.get("fa_confidence"),
                "fa_sources": candidate.get("fa_sources"),
                "updated_at": datetime.utcnow().isoformat()
            }

            # Upsert on symbol conflict
            response = requests.post(
                url,
                json=data,
                headers=headers,
                params={"on_conflict": "symbol"}
            )
            response.raise_for_status()

    except Exception as e:
        sentry_sdk.capture_exception(e)
        raise

def get_candidates() -> List[Dict]:
    """Load current candidate rows (for the FA stage, which runs in a separate
    invocation from the TA stage and so can't see the in-memory intermediates)."""
    try:
        url = f"{SUPABASE_URL}/rest/v1/candidates"
        headers = get_supabase_headers()
        response = requests.get(url, headers=headers, params={"order": "score.desc"})
        response.raise_for_status()
        return response.json() or []
    except Exception as e:
        sentry_sdk.capture_exception(e)
        log_error("Failed to load candidates", e)
        return []


def update_candidate_fa(symbol: str, fields: Dict):
    """PATCH only the FA + conviction columns for one symbol — does NOT touch the
    TA / rationale / trade_plan columns the TA stage already wrote."""
    try:
        url = f"{SUPABASE_URL}/rest/v1/candidates"
        headers = get_supabase_headers()
        headers["Prefer"] = "return=minimal"
        response = requests.patch(
            url, json=fields, headers=headers, params={"symbol": f"eq.{symbol}"}
        )
        response.raise_for_status()
    except Exception as e:
        sentry_sdk.capture_exception(e)
        log_error(f"Failed to update FA for {symbol}", e)


def trigger_async(path: str, params: Dict = None):
    """Fire-and-forget POST to one of our own backend stage endpoints. Sends the
    request (which invokes the target serverless function) but does not wait for
    it to finish — a short read timeout is expected and swallowed. Lets the
    pipeline chain stages without any single invocation exceeding the time limit."""
    base = os.getenv("AGENTS_SELF_URL", "https://sentics-agents.vercel.app").rstrip("/")
    url = f"{base}{path}"
    try:
        # connect generously, then stop waiting for the body (it keeps running)
        requests.post(url, params=params or {}, timeout=(8, 1))
    except requests.exceptions.ReadTimeout:
        pass  # expected — the target function is now running independently
    except Exception as e:
        log_error(f"Failed to trigger {path}", e)


def insert_fa_snapshots(rows: List[Dict]):
    """APPEND point-in-time FA snapshots (one row per coin per run). Never upserts
    — this is the immutable, leak-free corpus the FA backtest replays."""
    if not rows:
        return
    try:
        url = f"{SUPABASE_URL}/rest/v1/fa_snapshots"
        headers = get_supabase_headers()
        payload = [
            {
                "symbol": r.get("symbol"),
                "name": r.get("name"),
                "price": r.get("price"),
                "fa_score": r.get("fa_score"),
                "sentiment": r.get("sentiment"),
                "magnitude": r.get("magnitude"),
                "catalyst": r.get("catalyst"),
                "fa_confidence": r.get("fa_confidence"),
                "fa_summary": r.get("fa_summary"),
                "fa_sources": r.get("fa_sources"),
            }
            for r in rows
        ]
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        log_info(f"Appended {len(payload)} FA snapshots")
    except Exception as e:
        sentry_sdk.capture_exception(e)
        log_error("Failed to append FA snapshots", e)


def delete_candidates_except(symbols: List[str]):
    """Delete candidate rows whose symbol is NOT in the given list.

    The pipeline upserts the current universe but never removes symbols that
    have dropped out (e.g. stablecoins now filtered, or coins that fell out of
    the top 25). This prunes those stale rows. No-op on an empty list so we
    never accidentally wipe the whole table.
    """
    if not symbols:
        return
    try:
        url = f"{SUPABASE_URL}/rest/v1/candidates"
        headers = get_supabase_headers()
        quoted = ",".join(f'"{s}"' for s in symbols)
        params = {"symbol": f"not.in.({quoted})"}
        response = requests.delete(url, headers=headers, params=params)
        response.raise_for_status()
        log_info(f"Pruned stale candidates not in current set of {len(symbols)}")
    except Exception as e:
        sentry_sdk.capture_exception(e)
        log_error("Failed to prune stale candidates", e)


def insert_categories(categories: List[Dict]):
    """Insert or update categories in database via REST API."""
    try:
        url = f"{SUPABASE_URL}/rest/v1/categories"
        headers = get_supabase_headers()
        headers["Prefer"] = "resolution=merge-duplicates"

        for category in categories:
            data = {
                "name": category.get("name"),
                "momentum_score": category.get("momentum_score"),
                "macro_adjustment": category.get("macro_adjustment"),
                "updated_at": datetime.utcnow().isoformat()
            }

            # Upsert: merge-duplicates on conflict of name
            response = requests.post(
                url,
                json=data,
                headers=headers,
                params={"on_conflict": "name"}
            )
            response.raise_for_status()

    except Exception as e:
        sentry_sdk.capture_exception(e)
        raise

def insert_pipeline_run(run_id: str, trigger_type: str, status: str, error_msg: str = None):
    """Log pipeline run metadata via REST API."""
    try:
        url = f"{SUPABASE_URL}/rest/v1/pipeline_runs"
        headers = get_supabase_headers()

        data = {
            "run_id": run_id,
            "trigger_type": trigger_type,
            "status": status,
            "error_msg": error_msg,
            "created_at": datetime.utcnow().isoformat()
        }

        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()

    except Exception as e:
        sentry_sdk.capture_exception(e)
        raise

def get_latest_categories() -> List[Dict]:
    """Fetch latest category scores from database via REST API."""
    try:
        url = f"{SUPABASE_URL}/rest/v1/categories"
        headers = get_supabase_headers()
        params = {"order": "updated_at.desc"}

        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()

        return response.json() or []

    except Exception as e:
        sentry_sdk.capture_exception(e)
        return []

# Cache operations
def cache_set(key: str, value: Dict, ttl_minutes: int = 90):
    """Set value in Redis cache."""
    try:
        redis_client = get_redis_client()
        if redis_client:
            redis_client.setex(
                key,
                ttl_minutes * 60,
                json.dumps(value, default=str)
            )
    except Exception as e:
        sentry_sdk.capture_exception(e)

def cache_get(key: str) -> Optional[Dict]:
    """Get value from Redis cache."""
    try:
        redis_client = get_redis_client()
        if redis_client:
            value = redis_client.get(key)
            if value:
                return json.loads(value)
    except Exception as e:
        sentry_sdk.capture_exception(e)
    return None

def cache_invalidate(*keys):
    """Delete cache keys."""
    try:
        redis_client = get_redis_client()
        if redis_client:
            redis_client.delete(*keys)
    except Exception as e:
        sentry_sdk.capture_exception(e)

# Technical indicators
def calculate_rsi(prices: List[float], period: int = 14) -> float:
    """Wilder's RSI over the full price series (seed SMA + recursive smoothing).

    This matches the canonical RSI used by charting tools, unlike a simple
    average of the last `period` deltas (Cutler's), and incorporates the whole
    series instead of discarding everything before the last `period` points.
    """
    if len(prices) < period + 1:
        return 50.0

    deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
    gains = [max(d, 0.0) for d in deltas]
    losses = [max(-d, 0.0) for d in deltas]

    # Seed with a simple average over the first `period` deltas, then smooth.
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period

    if avg_loss == 0:
        return 100.0 if avg_gain > 0 else 50.0

    rs = avg_gain / avg_loss
    return max(0.0, min(100.0, 100 - 100 / (1 + rs)))

def calculate_moving_average(prices: List[float], period: int) -> Optional[float]:
    """Simple moving average, or None when there isn't a full `period` of data.

    Returns None (not the last price) on insufficient data so callers must gate
    period-dependent logic rather than act on a silently corrupted value.
    """
    if not prices or len(prices) < period:
        return None
    return sum(prices[-period:]) / period

def calculate_momentum(prices: List[float], period: int = 7) -> float:
    """Calculate price momentum percentage."""
    if len(prices) < period:
        return 0
    current = prices[-1]
    previous = prices[-period]
    if previous == 0:
        return 0
    return ((current - previous) / previous) * 100

# Logging
def log_info(message: str, **context):
    """Log info message with context."""
    print(f"[INFO] {message}", flush=True)
    if context:
        print(f"       {context}", flush=True)

def log_error(message: str, error: Exception = None):
    """Log error message."""
    print(f"[ERROR] {message}", flush=True)
    if error:
        print(f"        {str(error)}", flush=True)
        sentry_sdk.capture_exception(error)
