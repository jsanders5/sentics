"""
Agent 2: Top-25 Market Analysis & Directional Scoring

Fetches the top 25 cryptocurrencies by market cap from CoinGecko and runs
deterministic technical analysis on each to determine:
  - Direction:  Bullish | Bearish | Neutral
  - Timeframe:  Short (1-7d) | Medium (1-4w) | Long (1-3mo)
  - Confidence: High | Medium | Low
  - candidate_score (0-100): conviction strength in the directional call

No category filtering — every one of the top 25 is analyzed and returned.
Agent 3 consumes this output to generate the narrative rationale; the
direction / timeframe / confidence values here are the source of truth.
"""

from typing import List, Dict, Tuple
import statistics
import time

from .utils import (
    fetch_coingecko, fetch_market_chart, calculate_rsi,
    calculate_moving_average, calculate_momentum, log_info, log_error,
    cache_get, cache_set,
)

# Pure meme coins capped at Medium confidence regardless of signal strength
# (elevated manipulation risk — consistent with the product disclaimer).
MEME_SYMBOLS = {"DOGE", "SHIB", "PEPE", "WIF", "BONK", "FLOKI"}

# Fallback stablecoin denylist (by symbol) used if the CoinGecko category
# lookup fails. Stablecoins are pegged and have no meaningful direction, so
# they are excluded from the top-25 trading universe.
STABLECOIN_SYMBOLS = {
    "USDT", "USDC", "DAI", "USDS", "USDE", "USD1", "FDUSD", "TUSD", "PYUSD",
    "USDD", "FRAX", "GUSD", "LUSD", "USDP", "BUSD", "EURT", "EURS", "CRVUSD",
    "GHO", "USDX", "USDB", "USDL",
}

TOP_N = 25
FETCH_N = 50               # over-fetch so we still get 25 after dropping stablecoins
# >90 so CoinGecko's auto-granularity returns DAILY candles even if the
# `interval=daily` param is ever dropped on the demo tier (2–90d → hourly,
# >90d → daily). Also gives the 50-day MA comfortable buffer.
HISTORY_DAYS = 120
MIN_PRICES = 15            # RSI(14) needs at least 15 points


def load_stablecoin_ids() -> set:
    """Authoritative stablecoin CoinGecko IDs (cached 12h). Falls back to the
    symbol denylist if the category lookup fails."""
    cached = cache_get("stablecoin_ids")
    if cached and cached.get("ids"):
        return set(cached["ids"])
    try:
        rows = fetch_coingecko("/coins/markets", {
            "vs_currency": "usd",
            "category": "stablecoins",
            "per_page": 100,
            "page": 1,
            "sparkline": "false",
        })
        ids = [r.get("id") for r in rows if r.get("id")]
        if ids:
            cache_set("stablecoin_ids", {"ids": ids}, ttl_minutes=720)
        return set(ids)
    except Exception as e:
        log_error("Failed to fetch stablecoin list; using symbol denylist only", e)
        return set()


def is_stablecoin(coin: Dict, stablecoin_ids: set) -> bool:
    return (
        coin.get("id") in stablecoin_ids
        or coin.get("symbol", "").upper() in STABLECOIN_SYMBOLS
    )


def has_sufficient_data(prices: List[float], volumes: List[float]) -> bool:
    return len(prices) >= MIN_PRICES and len(volumes) >= 1


def _volume_ratio(volumes: List[float]) -> float:
    """Last completed day's volume vs 30-day average (ignores partial current day)."""
    completed = volumes[:-1] if len(volumes) > 1 else volumes
    last = completed[-1] if completed else 0
    avg = (
        statistics.mean(completed[-30:]) if len(completed) >= 30
        else statistics.mean(completed) if completed else 0
    )
    return round(last / avg, 2) if avg > 0 else 0.0


def calculate_technical_score(price: float, prices: List[float], rsi: float, volume_ratio: float) -> float:
    """Bullish technical alignment, 0-58 (kept for continuity with the detail view).
    RSI positioning (0-20) + volume strength (0-20) + MA alignment (0-18)."""
    rsi_score = max(0, 20 - abs(rsi - 56) * 0.2)
    volume_score = min(20, volume_ratio * 10)

    ma_20 = calculate_moving_average(prices, 20)
    ma_50 = calculate_moving_average(prices, 50)
    above_20 = (price - ma_20) / ma_20 if ma_20 > 0 else 0
    above_50 = (price - ma_50) / ma_50 if ma_50 > 0 else 0
    ma_score = min(18, max(0, (above_20 + above_50) * 5))

    return round(max(0, min(58, rsi_score + volume_score + ma_score)), 2)


def analyze_direction(
    price: float, prices: List[float], rsi: float, volume_ratio: float
) -> Tuple[str, float, Dict]:
    """Return (direction, directional_score, signals) from technical signals.

    directional_score ranges roughly -100..+100; positive = bullish bias.
    """
    ma_20 = calculate_moving_average(prices, 20)
    ma_50 = calculate_moving_average(prices, 50)
    mom_7 = calculate_momentum(prices, 7)
    mom_30 = calculate_momentum(prices, 30)

    pct_vs_50 = (price - ma_50) / ma_50 if ma_50 > 0 else 0
    ma_trend = (ma_20 - ma_50) / ma_50 if ma_50 > 0 else 0  # >0 = uptrend structure

    score = 0.0

    # Price vs moving averages
    above_20 = price > ma_20
    above_50 = price > ma_50
    score += 20 if above_20 else -20
    score += 15 if above_50 else -15

    # Moving-average structure (golden vs death alignment)
    ma_aligned_up = ma_20 > ma_50
    score += 20 if ma_aligned_up else -20

    # Short- and medium-term momentum (clamped contributions)
    score += max(-20, min(20, mom_7))
    score += max(-15, min(15, mom_30))

    # RSI regime
    if 50 <= rsi <= 70:
        score += 10           # healthy bullish momentum
    elif rsi > 70:
        score -= 5            # overbought, reversal risk
    elif 30 <= rsi < 50:
        score -= 10           # weak
    else:                     # rsi < 30
        score += 5            # oversold, mean-reversion bounce potential

    if score >= 25:
        direction = "Bullish"
    elif score <= -25:
        direction = "Bearish"
    else:
        direction = "Neutral"

    signals = {
        "above_20": above_20,
        "above_50": above_50,
        "ma_aligned_up": ma_aligned_up,
        "mom_7": mom_7,
        "mom_30": mom_30,
        "pct_vs_50": pct_vs_50,
        "ma_trend": ma_trend,
        "rsi": rsi,
        "volume_ratio": volume_ratio,
    }
    return direction, round(score, 2), signals


def assign_timeframe(direction: str, rsi: float, volume_ratio: float, signals: Dict) -> str:
    """Short = near-term catalyst, Long = stable structural trend, else Medium."""
    mom_7 = signals["mom_7"]
    ma_trend = signals["ma_trend"]
    pct_vs_50 = signals["pct_vs_50"]

    # Near-term catalysts: volume spike, RSI extreme, or sharp recent move
    if volume_ratio >= 2.0 or rsi >= 72 or rsi <= 28 or abs(mom_7) >= 15:
        return "Short"

    # Strong, established structural trend → longer horizon
    if abs(ma_trend) >= 0.08 and abs(pct_vs_50) >= 0.10:
        return "Long"

    return "Medium"


def assign_confidence(direction: str, symbol: str, signals: Dict) -> str:
    """High/Medium/Low based on how many signals agree with the direction."""
    if direction == "Neutral":
        return "Low"

    bull = direction == "Bullish"
    agree = 0
    agree += 1 if signals["above_20"] == bull else 0
    agree += 1 if signals["above_50"] == bull else 0
    agree += 1 if signals["ma_aligned_up"] == bull else 0
    agree += 1 if (signals["mom_7"] > 0) == bull else 0
    volume_confirms = signals["volume_ratio"] >= 1.3

    if agree >= 4 and volume_confirms:
        tier = "High"
    elif agree >= 3:
        tier = "Medium"
    else:
        tier = "Low"

    # Meme coins capped at Medium regardless of strength
    if symbol in MEME_SYMBOLS and tier == "High":
        tier = "Medium"

    return tier


def compute_candidate_score(directional_score: float, volume_ratio: float) -> float:
    """Conviction strength (0-100), direction-agnostic. Stronger/clearer setups rank higher."""
    base = 50 + abs(directional_score) * 0.5      # 50..100
    if volume_ratio >= 1.3:
        base += 5
    return round(max(0, min(100, base)), 2)


def _fmt(p: float) -> str:
    """Format a price for human-readable trade-plan conditions."""
    if p >= 1:
        return f"${p:,.2f}"
    return f"${p:,.6f}"


def _volatility(prices: List[float]) -> float:
    """Std-dev of daily returns over the last ~30 days, as a fraction (fallback 0.03)."""
    rets = [
        (prices[i] - prices[i - 1]) / prices[i - 1]
        for i in range(1, len(prices))
        if prices[i - 1] > 0
    ]
    window = rets[-30:] if len(rets) >= 2 else rets
    if len(window) < 2:
        return 0.03
    try:
        return max(0.005, statistics.pstdev(window))
    except statistics.StatisticsError:
        return 0.03


def compute_trade_plan(
    direction: str, price: float, prices: List[float], rsi: float
) -> Dict:
    """Derive a concrete, data-backed trade plan: entry/target/stop + conditions + R/R.

    Long plan for Bullish, short plan for Bearish, no actionable plan for Neutral.
    Levels come from the 20/50-day MAs, the recent 30-day swing range, and
    close-to-close volatility. All levels are paired with a confirmation
    condition (a price level plus an indicator/volume trigger).
    """
    ma20 = calculate_moving_average(prices, 20)
    ma50 = calculate_moving_average(prices, 50)
    recent = prices[-30:] if len(prices) >= 30 else prices
    swing_high = max(recent)
    swing_low = min(recent)
    vol = _volatility(prices)

    levels = {
        "ma20": round(ma20, 6),
        "ma50": round(ma50, 6),
        "swing_high": round(swing_high, 6),
        "swing_low": round(swing_low, 6),
    }

    if direction == "Bullish":
        if price >= swing_high * 0.98:
            entry = swing_high
            entry_condition = f"Close above the recent high {_fmt(swing_high)} on volume > 1.3× average"
        elif price >= ma20:
            entry = ma20
            entry_condition = f"Pullback holds the 20-day MA ({_fmt(ma20)}) with RSI staying above 50"
        else:
            entry = ma20
            entry_condition = f"Reclaim the 20-day MA ({_fmt(ma20)}) on volume > 1.3× average"

        vol_target = entry * (1 + max(2 * vol, 0.05))
        target = max(swing_high, vol_target) if swing_high > entry else vol_target
        stop = min(ma50, swing_low)
        if stop >= entry:
            stop = entry * (1 - max(1.5 * vol, 0.04))
        # Volatility floor: a stop must sit at least max(vol, 3%) below entry,
        # otherwise a too-tight stop inflates R/R into meaningless territory.
        stop = min(stop, entry * (1 - max(vol, 0.03)))

        target_condition = f"Take profit near {_fmt(target)} (prior resistance / +{(target/entry-1)*100:.0f}%)"
        stop_condition = f"Invalidated on a close below {_fmt(stop)} (below 50-day MA / recent low)"
        risk, reward = entry - stop, target - entry
        bias = "long"

    elif direction == "Bearish":
        if price <= swing_low * 1.02:
            entry = swing_low
            entry_condition = f"Breakdown below the recent low {_fmt(swing_low)} on rising volume"
        elif price <= ma20:
            entry = ma20
            entry_condition = f"Failed bounce into the 20-day MA ({_fmt(ma20)}) with RSI below 50"
        else:
            entry = ma20
            entry_condition = f"Loss of the 20-day MA ({_fmt(ma20)}) on volume > 1.3× average"

        vol_target = entry * (1 - max(2 * vol, 0.05))
        target = min(swing_low, vol_target) if swing_low < entry else vol_target
        stop = max(ma50, swing_high)
        if stop <= entry:
            stop = entry * (1 + max(1.5 * vol, 0.04))
        # Volatility floor: stop must sit at least max(vol, 3%) above entry.
        stop = max(stop, entry * (1 + max(vol, 0.03)))

        target_condition = f"Cover near {_fmt(target)} (prior support / {(target/entry-1)*100:.0f}%)"
        stop_condition = f"Invalidated on a close above {_fmt(stop)} (above 50-day MA / recent high)"
        risk, reward = stop - entry, entry - target
        bias = "short"

    else:  # Neutral
        return {
            "bias": "none",
            "summary": (
                f"No clear setup — wait for a break of the 20-day MA ({_fmt(ma20)}) "
                f"or the {_fmt(swing_low)}–{_fmt(swing_high)} range"
            ),
            "levels": levels,
        }

    risk_reward = round(reward / risk, 2) if risk > 0 else None

    return {
        "bias": bias,
        "entry": round(entry, 6),
        "entry_condition": entry_condition,
        "target": round(target, 6),
        "target_condition": target_condition,
        "stop": round(stop, 6),
        "stop_condition": stop_condition,
        "risk_reward": risk_reward,
        "levels": levels,
    }


def build_key_signals(direction: str, signals: Dict, rsi: float, volume_ratio: float) -> List[str]:
    """Deterministic human-readable signals (Agent 3 may refine/replace these)."""
    out = []
    if signals["above_20"] and signals["above_50"]:
        out.append("Price trading above both 20d and 50d moving averages")
    elif not signals["above_20"] and not signals["above_50"]:
        out.append("Price trading below both 20d and 50d moving averages")

    out.append(
        f"20d/50d MA structure is {'bullish (golden)' if signals['ma_aligned_up'] else 'bearish (death)'}"
    )
    out.append(f"RSI(14) at {rsi:.1f}")
    if volume_ratio >= 1.3:
        out.append(f"Volume {volume_ratio:.2f}x its 30-day average — above the 1.3x confirmation threshold")
    elif volume_ratio > 0:
        out.append(f"Volume {volume_ratio:.2f}x its 30-day average — below the 1.3x confirmation threshold")

    if abs(signals["mom_7"]) >= 5:
        out.append(f"7-day momentum {signals['mom_7']:+.1f}%")
    return out


def run(*_args, **_kwargs) -> Dict:
    """Run Agent 2 over the top 25 coins by market cap.

    Returns:
    {
        "status": "success" | "error",
        "candidates": [ {symbol, name, category, price, rsi, volume_ratio,
                         technical_score, category_momentum, candidate_score,
                         direction, time_horizon, confidence_tier, key_signals}, ... ],
        "total_candidates": int,
        "low_signal_environment": bool,
        "duration_seconds": float
    }
    Extra positional/keyword args are ignored for backward compatibility with
    the old Agent 1 -> Agent 2 call signature.
    """
    start_time = time.time()

    try:
        log_info(f"Agent 2 starting: analyzing top {TOP_N} non-stablecoin coins by market cap")

        markets = fetch_coingecko("/coins/markets", {
            "vs_currency": "usd",
            "order": "market_cap_desc",
            "per_page": FETCH_N,
            "page": 1,
            "sparkline": "false",
        })

        # Drop stablecoins, then keep the top TOP_N remaining by market cap
        stablecoin_ids = load_stablecoin_ids()
        universe = [c for c in markets if not is_stablecoin(c, stablecoin_ids)][:TOP_N]
        log_info(f"  {len(markets)} fetched, {len(universe)} after removing stablecoins")

        candidates = []
        for coin in universe:
            coin_id = coin.get("id")
            symbol = coin.get("symbol", "").upper()
            try:
                chart = fetch_market_chart(coin_id, days=HISTORY_DAYS)
                prices = [p[1] for p in chart.get("prices", [])]
                volumes = [v[1] for v in chart.get("volumes", [])]

                if not has_sufficient_data(prices, volumes):
                    log_info(f"  {symbol}: skip (insufficient history: {len(prices)} pts)")
                    continue

                price = coin.get("current_price") or (prices[-1] if prices else 0)
                rsi = round(calculate_rsi(prices, period=14), 2)
                volume_ratio = _volume_ratio(volumes)

                direction, directional_score, signals = analyze_direction(price, prices, rsi, volume_ratio)
                time_horizon = assign_timeframe(direction, rsi, volume_ratio, signals)
                confidence_tier = assign_confidence(direction, symbol, signals)
                candidate_score = compute_candidate_score(directional_score, volume_ratio)
                technical_score = calculate_technical_score(price, prices, rsi, volume_ratio)
                key_signals = build_key_signals(direction, signals, rsi, volume_ratio)
                trade_plan = compute_trade_plan(direction, price, prices, rsi)

                candidates.append({
                    "symbol": symbol,
                    "name": coin.get("name", ""),
                    "category": None,
                    "market_cap": coin.get("market_cap") or 0,
                    "price": price,
                    "rsi": rsi,
                    "volume_ratio": volume_ratio,
                    "technical_score": technical_score,
                    "category_momentum": 0,
                    "candidate_score": candidate_score,
                    "directional_score": directional_score,
                    "direction": direction,
                    "time_horizon": time_horizon,
                    "confidence_tier": confidence_tier,
                    "key_signals": key_signals,
                    "trade_plan": trade_plan,
                })

                log_info(f"  {symbol}: {direction} / {time_horizon} / {confidence_tier} (score {candidate_score})")

            except Exception as e:
                log_error(f"Error analyzing {coin_id}", e)
                continue

        # Rank by conviction strength (most actionable first)
        candidates.sort(key=lambda x: x["candidate_score"], reverse=True)

        log_info(f"Agent 2 complete: {len(candidates)} coins analyzed")

        return {
            "status": "success",
            "candidates": candidates,
            "total_candidates": len(candidates),
            "low_signal_environment": len(candidates) < 5,
            "duration_seconds": round(time.time() - start_time, 2),
        }

    except Exception as e:
        log_error("Agent 2 failed", e)
        return {
            "status": "error",
            "error": str(e),
            "candidates": [],
            "total_candidates": 0,
            "low_signal_environment": True,
            "duration_seconds": round(time.time() - start_time, 2),
        }
