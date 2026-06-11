"""
Agent 2: Candidate Discovery & Technical Scoring

Discovers all coins from passing categories with sufficient data.
No hard filters — all coins scored based on:
- Technical alignment: RSI positioning, volume strength, MA alignment
- Category momentum: sector-level strength signal

Scores all candidates: 50% technical alignment + 50% category momentum

Output: Up to 50 ranked candidates (highest scores first) for Agent 3 synthesis
"""

from typing import List, Dict, Optional
import statistics
from .utils import (
    fetch_coingecko, fetch_market_chart, calculate_rsi,
    calculate_moving_average, calculate_momentum, log_info, log_error,
    CATEGORY_TO_COINGECKO_ID
)

def has_sufficient_data(prices: List[float], volumes: List[float]) -> bool:
    """Check if coin has minimum data required for analysis (14 days for RSI)."""
    return len(prices) >= 14 and len(volumes) >= 1

def calculate_technical_score(coin_data: Dict, prices: List[float], volumes: List[float]) -> float:
    """
    Calculate technical alignment score (0-58):
    - RSI positioning (0-20): closer to 56 = more bullish
    - Volume strength (0-20): ratio above 1.3x
    - MA alignment (0-18): price above MAs by %
    """
    try:
        rsi = calculate_rsi(prices, period=14)
        current_price = coin_data.get("current_price", 0)

        # RSI score: optimal around 56 (mid-overbought)
        rsi_diff = abs(rsi - 56)
        rsi_score = max(0, 20 - (rsi_diff * 0.2))

        # Volume score: use last COMPLETED day (same partial-day fix as passes_technical_filters)
        completed_volumes = volumes[:-1] if len(volumes) > 1 else volumes
        last_completed_vol = completed_volumes[-1] if completed_volumes else 0
        avg_volume_30d = (
            statistics.mean(completed_volumes[-30:]) if len(completed_volumes) >= 30
            else statistics.mean(completed_volumes) if completed_volumes else 0
        )
        volume_ratio = last_completed_vol / avg_volume_30d if avg_volume_30d > 0 else 0
        volume_score = min(20, volume_ratio * 10)

        # MA score: price above both MAs
        ma_20 = calculate_moving_average(prices, 20)
        ma_50 = calculate_moving_average(prices, 50)
        ma_above_20 = (current_price - ma_20) / ma_20 if ma_20 > 0 else 0
        ma_above_50 = (current_price - ma_50) / ma_50 if ma_50 > 0 else 0
        ma_score = min(18, (ma_above_20 + ma_above_50) * 5)

        technical_score = rsi_score + volume_score + ma_score
        return max(0, min(58, technical_score))

    except Exception as e:
        log_error(f"Error calculating technical score for {coin_data.get('id')}", e)
        return 0

def run(agent1_result: Dict, category_coins_map: Dict = None) -> Dict:
    """
    Run Agent 2: Candidate Discovery

    Args:
    - agent1_result: Output from Agent 1 (list of categories with scores)
    - category_coins_map: Map of categories to top coins (optional, for efficiency)

    Returns:
    {
        "status": "success" | "error",
        "candidates": [
            {
                "symbol": "BTC",
                "name": "Bitcoin",
                "category": "Layer 1",
                "price": 45000,
                "rsi": 65,
                "volume_ratio": 1.8,
                "technical_score": 45,
                "category_momentum": 72,
                "candidate_score": 58.5
            },
            ...
        ],
        "total_candidates": X,
        "low_signal_environment": bool
    }
    """
    import time
    start_time = time.time()

    try:
        log_info("Agent 2 starting: Candidate Discovery")

        # Get passing categories from Agent 1
        passing_categories = agent1_result.get("passing_categories", [])
        if not passing_categories:
            log_info("No passing categories from Agent 1; skipping Agent 2")
            return {
                "status": "success",
                "candidates": [],
                "total_candidates": 0,
                "low_signal_environment": True
            }

        # Fetch category momentum scores for later use (Agent 1 produces these)
        category_scores_map = {
            cat["name"]: cat["momentum_score"]
            for cat in agent1_result.get("categories", [])
        }

        candidates = []

        # For each passing category, fetch its coins from CoinGecko and filter.
        # Using /coins/markets?category=<id> instead of fetching top-50 globally
        # because the global top-50 has no category field — CoinGecko does not
        # return category membership in /coins/markets without the category param.
        for category_name in passing_categories:
            coingecko_category_id = CATEGORY_TO_COINGECKO_ID.get(category_name)
            if not coingecko_category_id:
                log_error(f"No CoinGecko category ID mapped for '{category_name}'; skipping")
                continue

            log_info(f"Fetching coins for category '{category_name}' (CG id: {coingecko_category_id})")

            try:
                category_coins = fetch_coingecko("/coins/markets", {
                    "vs_currency": "usd",
                    "category": coingecko_category_id,
                    "order": "market_cap_desc",
                    "per_page": 10,  # limit to top 10 coins per category for speed
                    "page": 1,
                    "sparkline": "false"
                })
            except Exception as e:
                log_error(f"Failed to fetch coins for category '{category_name}'", e)
                continue

            category_momentum = category_scores_map.get(category_name, 50)
            category_candidate_count = 0

            log_info(f"  Checking {len(category_coins)} coins in '{category_name}' (momentum={category_momentum:.1f})")
            for coin in category_coins:
                coin_id = coin.get("id")
                symbol = coin.get("symbol", "").upper()

                try:
                    # Fetch 30-day price and volume history for technical indicators
                    chart = fetch_market_chart(coin_id, days=30)
                    prices = [p[1] for p in chart.get("prices", [])]
                    volumes = [v[1] for v in chart.get("volumes", [])]

                    # Skip coins with insufficient history (need 14+ days for RSI)
                    if not has_sufficient_data(prices, volumes):
                        print(f"    {symbol}: skip (insufficient data: {len(prices)} days)", flush=True)
                        continue

                    # Score this candidate (no hard gates - all coins with sufficient data are ranked)
                    technical_score = calculate_technical_score(coin, prices, volumes)

                    # Candidate score: 50% technical alignment + 50% category momentum.
                    # technical_score is 0-58 (20 RSI + 20 volume + 18 MA); normalize to 0-100
                    # before blending so both components have equal effective range.
                    # Without normalization the blend is ~37% technical / 63% category because
                    # the raw technical max (58) is 58% of the category max (100).
                    _TECHNICAL_MAX = 58.0
                    technical_normalized = (technical_score / _TECHNICAL_MAX) * 100
                    candidate_score = (technical_normalized * 0.5) + (category_momentum * 0.5)
                    candidate_score = max(0, min(100, candidate_score))

                    # Calculate volume ratio for reporting (same partial-day fix)
                    completed_vols = volumes[:-1] if len(volumes) > 1 else volumes
                    current_vol = completed_vols[-1] if completed_vols else 0
                    avg_vol_30d = (
                        statistics.mean(completed_vols[-30:]) if len(completed_vols) >= 30
                        else statistics.mean(completed_vols) if completed_vols else 0
                    )
                    volume_ratio = round(current_vol / avg_vol_30d, 2) if avg_vol_30d > 0 else 0

                    candidate = {
                        "symbol": symbol,
                        "name": coin.get("name", ""),
                        "category": category_name,
                        "price": coin.get("current_price", 0),
                        "rsi": round(calculate_rsi(prices, period=14), 2),
                        "volume_ratio": volume_ratio,
                        "technical_score": round(technical_score, 2),
                        "category_momentum": round(category_momentum, 2),
                        "candidate_score": round(candidate_score, 2)
                    }

                    candidates.append(candidate)
                    category_candidate_count += 1

                except Exception as e:
                    log_error(f"Error processing coin {coin_id} in category '{category_name}'", e)
                    continue

            log_info(
                f"Category '{category_name}': {category_candidate_count} candidates "
                f"from {len(category_coins)} coins checked"
            )

        # Sort by candidate score descending, limit to 50
        candidates.sort(key=lambda x: x["candidate_score"], reverse=True)
        candidates = candidates[:50]

        low_signal = len(candidates) < 5

        log_info(f"Agent 2 complete: {len(candidates)} candidates")

        return {
            "status": "success",
            "candidates": candidates,
            "total_candidates": len(candidates),
            "low_signal_environment": low_signal,
            "duration_seconds": round(time.time() - start_time, 2)
        }

    except Exception as e:
        log_error("Agent 2 failed", e)
        return {
            "status": "error",
            "error": str(e),
            "candidates": [],
            "total_candidates": 0,
            "low_signal_environment": True
        }
