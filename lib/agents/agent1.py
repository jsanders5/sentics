"""
Agent 1: Category Momentum Scoring

Analyzes price momentum, volume momentum, and macro conditions across
crypto categories to identify bullish sectors.

Output: Category scores (0-100), with passing threshold >= 55
"""

from typing import List, Dict
from datetime import datetime, timedelta
import statistics
from .utils import (
    fetch_coingecko, fetch_btc_dominance, fetch_market_chart,
    calculate_momentum, calculate_moving_average, log_info, log_error,
    CATEGORIES, get_category_for_coin
)

def score_category(category_name: str, coins_data: List[Dict]) -> Dict:
    """
    Score a category based on:
    - 50% price momentum (14d)
    - 35% volume momentum (24h)
    - 15% news sentiment (placeholder for Phase 2)
    """
    if not coins_data:
        return {"name": category_name, "momentum_score": 0, "macro_adjustment": 0}

    try:
        # Calculate price momentum for each coin
        price_momentums = []
        volume_momentums = []

        for coin in coins_data:
            try:
                coin_id = coin.get("id")
                if not coin_id:
                    continue

                # Fetch 30-day market chart
                chart = fetch_market_chart(coin_id, days=30)
                prices = [p[1] for p in chart.get("prices", [])]
                volumes = [v[1] for v in chart.get("volumes", [])]

                if len(prices) > 14:
                    # 14-day price momentum
                    price_mom = calculate_momentum(prices, period=14)
                    price_momentums.append(price_mom)

                    # 24-hour volume momentum
                    if len(volumes) >= 2:
                        volume_mom = calculate_momentum(volumes, period=1)
                        volume_momentums.append(volume_mom)

            except Exception as e:
                log_error(f"Error calculating momentum for {coin.get('id')}", e)
                continue

        if not price_momentums:
            return {"name": category_name, "momentum_score": 0, "macro_adjustment": 0}

        # Calculate weighted score
        avg_price_mom = statistics.mean(price_momentums)
        avg_volume_mom = statistics.mean(volume_momentums) if volume_momentums else 0

        # Normalize to 0-100 scale
        # Momentum can be negative; normalize: -50% to +50% = 0 to 100
        price_score = max(0, min(100, (avg_price_mom + 50) * 1.0))
        volume_score = max(0, min(100, (avg_volume_mom + 50) * 1.0))
        sentiment_score = 50  # Placeholder

        # Weighted combination
        category_score = (price_score * 0.50) + (volume_score * 0.35) + (sentiment_score * 0.15)
        category_score = max(0, min(100, category_score))

        return {
            "name": category_name,
            "momentum_score": round(category_score, 2),
            "macro_adjustment": 0
        }

    except Exception as e:
        log_error(f"Error scoring category {category_name}", e)
        return {"name": category_name, "momentum_score": 0, "macro_adjustment": 0}

def apply_macro_adjustment(categories: List[Dict]) -> List[Dict]:
    """
    Apply macro-level adjustments:
    - If BTC dominance up > 2pp: reduce altcoin scores by 5%
    - If market cap down > 5%: reduce all scores by 3%
    """
    try:
        btc_dom = fetch_btc_dominance()
        log_info(f"Current BTC dominance: {btc_dom}%")

        for category in categories:
            adjustment = 0

            # BTC dominance adjustment (alt categories only)
            if category["name"] not in ["Layer 1"] and btc_dom > 50:
                adjustment -= 5

            category["macro_adjustment"] = adjustment
            if adjustment != 0:
                category["momentum_score"] = max(0, category["momentum_score"] + adjustment)

        return categories

    except Exception as e:
        log_error("Error applying macro adjustment", e)
        return categories

def run(trigger_type: str = "scheduled") -> Dict:
    """
    Run Agent 1: Category Momentum Scoring

    Returns:
    {
        "status": "success" | "error",
        "categories": [{"name": "...", "momentum_score": X, "macro_adjustment": Y}, ...],
        "passing_categories": [...],
        "duration_seconds": X
    }
    """
    import time
    start_time = time.time()

    try:
        log_info("Agent 1 starting: Category Momentum Scoring")

        # Fetch top 50 coins by market cap
        coins = fetch_coingecko("/coins/markets", {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": 50,
            "page": 1,
            "sparkline": False
        })

        # Group coins by category
        category_coins = {cat: [] for cat in CATEGORIES.keys()}
        for coin in coins:
            coin_id = coin.get("id")
            category = get_category_for_coin(coin_id)
            if category != "Other":
                category_coins[category].append(coin)

        # Score each category
        category_scores = []
        for category_name, coins_list in category_coins.items():
            score = score_category(category_name, coins_list)
            category_scores.append(score)

        # Apply macro adjustments
        category_scores = apply_macro_adjustment(category_scores)

        # Filter passing categories (>= 55)
        passing_categories = [c for c in category_scores if c["momentum_score"] >= 55]

        log_info(f"Agent 1 complete: {len(passing_categories)} passing categories")

        return {
            "status": "success",
            "categories": category_scores,
            "passing_categories": [c["name"] for c in passing_categories],
            "duration_seconds": round(time.time() - start_time, 2)
        }

    except Exception as e:
        log_error("Agent 1 failed", e)
        return {
            "status": "error",
            "error": str(e),
            "categories": [],
            "passing_categories": [],
            "duration_seconds": round(time.time() - start_time, 2)
        }
