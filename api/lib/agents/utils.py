"""
Shared utilities for STI agents.
Handles: API calls, database operations, caching, logging.
"""

import os
import json
import requests
import redis
import sentry_sdk
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from decimal import Decimal

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
def fetch_coingecko(endpoint: str, params: Dict = None) -> Dict:
    """Fetch data from CoinGecko free API."""
    try:
        url = f"https://api.coingecko.com/api/v3{endpoint}"
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        sentry_sdk.capture_exception(e)
        raise

def fetch_top_50_coins() -> List[Dict]:
    """Fetch top 50 coins by market cap."""
    try:
        data = fetch_coingecko("/coins/markets", {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 50,
            "page": 1,
            "sparkline": False
        })
        return data
    except Exception as e:
        sentry_sdk.capture_exception(e)
        raise

def fetch_market_chart(coin_id: str, days: int = 30) -> Dict:
    """Fetch OHLCV data for a coin."""
    try:
        data = fetch_coingecko(f"/coins/{coin_id}/market_chart", {
            "vs_currency": "usd",
            "days": days,
            "interval": "daily"
        })
        return data
    except Exception as e:
        sentry_sdk.capture_exception(e)
        raise

def fetch_btc_dominance() -> float:
    """Fetch BTC dominance percentage."""
    try:
        data = fetch_coingecko("/global")
        return data.get("data", {}).get("btc_dominance", 0)
    except Exception as e:
        sentry_sdk.capture_exception(e)
        return 0

# Database operations (via Supabase REST API)
def insert_candidates(candidates: List[Dict]):
    """Insert or update candidates in database via REST API."""
    try:
        url = f"{SUPABASE_URL}/rest/v1/candidates"
        headers = get_supabase_headers()

        for candidate in candidates:
            data = {
                "symbol": candidate.get("symbol"),
                "name": candidate.get("name"),
                "category": candidate.get("category"),
                "time_horizon": candidate.get("time_horizon"),
                "confidence_tier": candidate.get("confidence_tier"),
                "score": candidate.get("score"),
                "rationale": candidate.get("rationale"),
                "entry_type": candidate.get("entry_type"),
                "entry_quality": candidate.get("entry_quality"),
                "updated_at": datetime.utcnow().isoformat()
            }

            # Upsert: try to update, if not exists insert
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

def insert_categories(categories: List[Dict]):
    """Insert or update categories in database via REST API."""
    try:
        url = f"{SUPABASE_URL}/rest/v1/categories"
        headers = get_supabase_headers()

        for category in categories:
            data = {
                "name": category.get("name"),
                "momentum_score": category.get("momentum_score"),
                "macro_adjustment": category.get("macro_adjustment"),
                "updated_at": datetime.utcnow().isoformat()
            }

            # Upsert: try to update, if not exists insert
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
    """Calculate RSI (Relative Strength Index)."""
    if len(prices) < period:
        return 50

    deltas = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    gains = [d if d > 0 else 0 for d in deltas]
    losses = [-d if d < 0 else 0 for d in deltas]

    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period

    if avg_loss == 0:
        return 100 if avg_gain > 0 else 50

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return max(0, min(100, rsi))

def calculate_moving_average(prices: List[float], period: int) -> float:
    """Calculate simple moving average."""
    if len(prices) < period:
        return prices[-1] if prices else 0
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
