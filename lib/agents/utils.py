"""
Shared utilities for STI agents.
Handles: API calls, database operations, caching, logging.
"""

import os
import json
import requests
import psycopg2
import redis
import sentry_sdk
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from decimal import Decimal

# Initialize Sentry
sentry_sdk.init(dsn=os.getenv("SENTRY_DSN"))

# Database connection
def get_db_connection():
    """Connect to Supabase PostgreSQL."""
    try:
        conn = psycopg2.connect(os.getenv("DATABASE_URL"))
        return conn
    except Exception as e:
        sentry_sdk.capture_exception(e)
        raise

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

# Database operations
def insert_candidates(candidates: List[Dict]):
    """Insert or update candidates in database."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        for candidate in candidates:
            cur.execute("""
                INSERT INTO candidates
                (symbol, name, category, time_horizon, confidence_tier, score,
                 rationale, entry_type, entry_quality, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                ON CONFLICT (symbol) DO UPDATE SET
                    category = EXCLUDED.category,
                    time_horizon = EXCLUDED.time_horizon,
                    confidence_tier = EXCLUDED.confidence_tier,
                    score = EXCLUDED.score,
                    rationale = EXCLUDED.rationale,
                    entry_type = EXCLUDED.entry_type,
                    entry_quality = EXCLUDED.entry_quality,
                    updated_at = NOW()
            """, (
                candidate.get("symbol"),
                candidate.get("name"),
                candidate.get("category"),
                candidate.get("time_horizon"),
                candidate.get("confidence_tier"),
                candidate.get("score"),
                candidate.get("rationale"),
                candidate.get("entry_type"),
                candidate.get("entry_quality")
            ))

        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        sentry_sdk.capture_exception(e)
        raise

def insert_categories(categories: List[Dict]):
    """Insert or update categories in database."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        for category in categories:
            cur.execute("""
                INSERT INTO categories (name, momentum_score, macro_adjustment, updated_at)
                VALUES (%s, %s, %s, NOW())
                ON CONFLICT (name) DO UPDATE SET
                    momentum_score = EXCLUDED.momentum_score,
                    macro_adjustment = EXCLUDED.macro_adjustment,
                    updated_at = NOW()
            """, (
                category.get("name"),
                category.get("momentum_score"),
                category.get("macro_adjustment")
            ))

        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        sentry_sdk.capture_exception(e)
        raise

def insert_pipeline_run(run_id: str, trigger_type: str, status: str, error_msg: str = None):
    """Log pipeline run metadata."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO pipeline_runs (run_id, trigger_type, status, error_msg, created_at)
            VALUES (%s, %s, %s, %s, NOW())
        """, (run_id, trigger_type, status, error_msg))

        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        sentry_sdk.capture_exception(e)
        raise

def get_latest_categories() -> List[Dict]:
    """Fetch latest category scores from database."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT name, momentum_score, macro_adjustment
            FROM categories
            ORDER BY updated_at DESC
        """)

        rows = cur.fetchall()
        cur.close()
        conn.close()

        return [
            {
                "name": row[0],
                "momentum_score": float(row[1]),
                "macro_adjustment": float(row[2]) if row[2] else 0
            }
            for row in rows
        ]
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
