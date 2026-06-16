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
import math
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
# Require a full 50-day window so MA50 / swing structure / persistence are always
# valid (the top-25 universe always has ~120 closes). Removes the corrupted
# short-history path.
MIN_PRICES = 50

# --- Scoring model constants (tunable; un-backtested hypotheses) ---------------
# directional_score = trend_factor[-45,45] + momentum_factor[-40,40] + rsi_factor[-15,15]
# → exact range [-100, +100]. Keep these as named constants so a future backtest
# can calibrate without touching the structure.
W_TREND = 45.0             # trend factor saturation
W_MOM = 40.0               # momentum factor saturation
W_RSI = 15.0               # rsi factor saturation
K_TREND = 0.10             # trend_metric (blended % deviation) scale for tanh
K_MOM = 12.0               # momentum blend (%) scale for tanh
RSI_PEAK = 57.0            # RSI directional sweet spot
RSI_WIDTH = 16.0           # RSI gaussian width
TREND_CAP_NO_MA50 = 30.0   # reduced trend cap when MA50 unavailable (degraded mode)

DIR_THRESHOLD = 20.0       # |directional_score| >= 20 → directional, else Neutral

# Conviction (candidate_score) mapping.
# Backtest finding (12 coins / 365d, stable across a coin train/test split):
# trend MAGNITUDE does not predict forward edge (corr ~ -0.07), but signal
# AGREEMENT does at the low end — Low-confidence calls are reliably worse. So
# conviction is a magnitude base TEMPERED by agreement (mainly a Low penalty),
# rather than pure magnitude. See api/scripts/backtest.py.
CONV_MAG_LO, CONV_MAG_HI = 50.0, 85.0    # magnitude base band (alone can't earn the top)
CONV_NEU_HI = 20.0                       # neutral band ceiling (< directional floor)
# Across 12- AND 30-coin backtests, Low-confidence calls are consistently worse,
# so they get penalized. A High *reward* did NOT hold up on the larger sample
# (High edge went negative), so High gets no bonus — only Low is acted on.
AGREEMENT_BONUS = {"High": 0.0, "Medium": 0.0, "Low": -18.0}
VOL_BUMP = 5.0
VOL_CONFIRM = 1.3

# Trade plan
RR_MIN, RR_MAX = 0.5, 5.0
MEASURED_MOVE = 0.618


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
    return len(prices) >= MIN_PRICES and len(volumes) >= MIN_PRICES


def _volume_ratio(volumes: List[float]) -> float:
    """Last completed day's volume vs 30-day average (ignores partial current day)."""
    completed = volumes[:-1] if len(volumes) > 1 else volumes
    last = completed[-1] if completed else 0
    avg = (
        statistics.mean(completed[-30:]) if len(completed) >= 30
        else statistics.mean(completed) if completed else 0
    )
    return round(last / avg, 2) if avg > 0 else 0.0


def calculate_technical_score(volume_ratio: float, trend_metric: float, mom_blend: float) -> float:
    """Direction-AGNOSTIC setup strength, 0-58 — how clean/confirmed the move is,
    regardless of bull vs bear (so it reads sensibly next to Bearish coins too).

    Reuses the exact trend_metric / mom_blend computed in analyze_direction so the
    two never drift. RSI is intentionally excluded here — it lives in the
    directional score and is shown as its own field; including it would
    re-introduce double-counting.
    """
    trend_strength = 25.0 * abs(math.tanh(trend_metric / K_TREND))   # 0-25
    mom_strength = 18.0 * abs(math.tanh(mom_blend / K_MOM))          # 0-18
    vol_strength = min(15.0, 15.0 * (volume_ratio / 2.0))           # 0-15 (saturates at 2.0x)
    return round(max(0.0, min(58.0, trend_strength + mom_strength + vol_strength)), 2)


def analyze_direction(
    price: float, prices: List[float], rsi: float, volume_ratio: float
) -> Tuple[str, float, Dict]:
    """Return (direction, directional_score, signals).

    directional_score = trend_factor[-45,45] + momentum_factor[-40,40]
                        + rsi_factor[-15,15]  → exact range [-100, +100].
    The three collinear MA signals collapse into ONE trend factor (no
    double-counting); momentum and RSI carry independent weight.
    """
    ma20 = calculate_moving_average(prices, 20)
    ma50 = calculate_moving_average(prices, 50)
    mom_7 = calculate_momentum(prices, 7)
    mom_30 = calculate_momentum(prices, 30)
    vol = _volatility(prices)

    # --- Trend factor: one metric from the (collinear) deviations, saturated ---
    d20 = (price - ma20) / ma20 if ma20 else 0.0
    if ma50:
        d50 = (price - ma50) / ma50
        dstruct = (ma20 - ma50) / ma50 if ma20 else 0.0
        trend_metric = 0.5 * d20 + 0.3 * d50 + 0.2 * dstruct
        trend_cap = W_TREND
    else:
        trend_metric = d20
        trend_cap = TREND_CAP_NO_MA50
    trend_factor = trend_cap * math.tanh(trend_metric / K_TREND)

    # --- Momentum factor: blend 7d/30d, saturated ---
    mom_blend = 0.6 * mom_7 + 0.4 * mom_30
    momentum_factor = W_MOM * math.tanh(mom_blend / K_MOM)

    # --- RSI factor: smooth, signed, peaks at RSI_PEAK (no step discontinuities) ---
    rsi_factor = W_RSI * (2 * math.exp(-((rsi - RSI_PEAK) / RSI_WIDTH) ** 2) - 1)

    directional_score = round(trend_factor + momentum_factor + rsi_factor, 2)

    if directional_score >= DIR_THRESHOLD:
        direction = "Bullish"
    elif directional_score <= -DIR_THRESHOLD:
        direction = "Bearish"
    else:
        direction = "Neutral"

    # Directional consistency over the last 30 daily returns (0 choppy .. 1 one-way)
    rets = [
        (prices[i] - prices[i - 1]) / prices[i - 1]
        for i in range(1, len(prices))
        if prices[i - 1] > 0
    ]
    last_rets = rets[-30:]
    if last_rets:
        half = len(last_rets) / 2
        pos_days = sum(1 for r in last_rets if r > 0)
        directional_consistency = abs(pos_days - half) / half if half > 0 else 0.0
    else:
        directional_consistency = 0.0

    # Display / confidence inputs (no longer score inputs — double-counting removed)
    above_20 = (price > ma20) if ma20 else False
    above_50 = (price > ma50) if ma50 else False
    ma_aligned_up = (ma20 > ma50) if (ma20 and ma50) else False

    signals = {
        "above_20": above_20,
        "above_50": above_50,
        "ma_aligned_up": ma_aligned_up,
        "ma50_available": ma50 is not None,
        "mom_7": mom_7,
        "mom_30": mom_30,
        "vol": vol,
        "directional_consistency": directional_consistency,
        "trend_metric": trend_metric,
        "mom_blend": mom_blend,
        "rsi": rsi,
        "volume_ratio": volume_ratio,
    }
    return direction, directional_score, signals


def assign_timeframe(direction: str, rsi: float, volume_ratio: float, signals: Dict) -> str:
    """Short = fast/catalyst, Long = slow stable trend, else Medium.

    Fixes the old backwards rule: a large MA gap is a *recent sharp move*
    (Short), not a stable trend. Long now requires calm volatility AND
    one-directional persistence AND an established (but non-violent) move.
    """
    vol = signals["vol"]
    mom_7 = signals["mom_7"]
    mom_30 = signals["mom_30"]
    consistency = signals["directional_consistency"]

    # SHORT — spike, RSI extreme, sharp recent move, or high volatility
    if volume_ratio >= 2.0 or rsi >= 72 or rsi <= 28 or abs(mom_7) >= 15 or vol >= 0.07:
        return "Short"

    # LONG — calm + persistent one-way drift + a real but non-violent 30d move
    if vol <= 0.035 and consistency >= 0.40 and abs(mom_30) >= 5:
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


def compute_candidate_score(
    direction: str, directional_score: float, volume_ratio: float,
    confidence_tier: str = "Medium",
) -> float:
    """Conviction (0-100). Neutral → [0,20) so it can never outrank a directional
    call. Directional: a magnitude base (|directional_score| in [20,100] → [50,85])
    TEMPERED by agreement (a small High nudge, a large Low penalty — agreement is
    the part that predicts edge out-of-sample) plus a +5 volume bump."""
    ds = abs(directional_score)
    if direction == "Neutral":
        return round(min(CONV_NEU_HI, ds / DIR_THRESHOLD * CONV_NEU_HI), 2)
    conv = CONV_MAG_LO + (ds - DIR_THRESHOLD) / (100.0 - DIR_THRESHOLD) * (CONV_MAG_HI - CONV_MAG_LO)
    conv += AGREEMENT_BONUS.get(confidence_tier, 0.0)
    if volume_ratio >= VOL_CONFIRM:
        conv += VOL_BUMP
    return round(max(0.0, min(100.0, conv)), 2)


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
    direction: str, price: float, prices: List[float], signals: Dict
) -> Dict:
    """Derive a concrete, data-backed trade plan: entry/target/stop + conditions + R/R.

    Long for Bullish, short for Bearish, no actionable plan for Neutral. Stops sit
    at real structural support/resistance (nearest MA50 / swing level), targets at
    the next swing level or a measured move; volatility only acts as a floor on
    each leg, and R/R is clamped to [0.5, 5] by adjusting the target — so R/R
    EMERGES from structure rather than being pinned near 2:1 by construction.
    """
    ma20 = calculate_moving_average(prices, 20)
    ma50 = calculate_moving_average(prices, 50)
    recent = prices[-30:] if len(prices) >= 30 else prices
    swing_high = max(recent)
    swing_low = min(recent)
    vol = signals.get("vol") if signals else None
    if vol is None:
        vol = _volatility(prices)

    levels = {
        "ma20": round(ma20, 6) if ma20 is not None else None,
        "ma50": round(ma50, 6) if ma50 is not None else None,
        "swing_high": round(swing_high, 6),
        "swing_low": round(swing_low, 6),
    }

    risk_floor = max(1.0 * vol, 0.02)
    reward_floor = max(1.0 * vol, 0.02)

    if direction == "Bullish":
        if price >= swing_high * 0.98:
            entry = swing_high
            entry_condition = f"Close above the recent high {_fmt(swing_high)} on volume > 1.3× average"
        elif ma20 and price >= ma20:
            entry = ma20
            entry_condition = f"Pullback holds the 20-day MA ({_fmt(ma20)}) with RSI staying above 50"
        else:
            entry = ma20 if ma20 else price
            entry_condition = f"Reclaim the 20-day MA ({_fmt(entry)}) on volume > 1.3× average"

        # Stop: nearest structural support below entry, then enforce the vol floor
        supports = [s for s in (ma50, swing_low) if s is not None and s < entry]
        struct_stop = max(supports) if supports else entry * (1 - max(2 * vol, 0.05))
        stop = min(struct_stop, entry * (1 - risk_floor))

        # Target: next resistance above entry, else a measured move on a breakout
        if swing_high > entry:
            struct_target = swing_high
        else:
            struct_target = swing_high + (swing_high - swing_low) * MEASURED_MOVE
        target = max(struct_target, entry * (1 + reward_floor))

        # Guardrails: clamp R/R into [RR_MIN, RR_MAX] by moving the target
        risk = entry - stop
        target = min(target, entry + RR_MAX * risk)
        target = max(target, entry + RR_MIN * risk)
        reward = target - entry
        target_condition = f"Illustrative upside level near {_fmt(target)} (prior resistance / +{(target/entry-1)*100:.0f}%)"
        stop_condition = f"Invalidated on a close below {_fmt(stop)} (structural support / volatility floor)"
        bias = "long"

    elif direction == "Bearish":
        if price <= swing_low * 1.02:
            entry = swing_low
            entry_condition = f"Breakdown below the recent low {_fmt(swing_low)} on rising volume"
        elif ma20 and price <= ma20:
            entry = ma20
            entry_condition = f"Failed bounce into the 20-day MA ({_fmt(ma20)}) with RSI below 50"
        else:
            entry = ma20 if ma20 else price
            entry_condition = f"Loss of the 20-day MA ({_fmt(entry)}) on volume > 1.3× average"

        # Stop: nearest structural resistance above entry, then vol floor
        resistances = [r for r in (ma50, swing_high) if r is not None and r > entry]
        struct_stop = min(resistances) if resistances else entry * (1 + max(2 * vol, 0.05))
        stop = max(struct_stop, entry * (1 + risk_floor))

        # Target: next support below entry, else a measured move on a breakdown
        if swing_low < entry:
            struct_target = swing_low
        else:
            struct_target = swing_low - (swing_high - swing_low) * MEASURED_MOVE
        target = min(struct_target, entry * (1 - reward_floor))

        risk = stop - entry
        target = max(target, entry - RR_MAX * risk)
        target = min(target, entry - RR_MIN * risk)
        reward = entry - target
        target_condition = f"Illustrative downside level near {_fmt(target)} (prior support / {(target/entry-1)*100:.0f}%)"
        stop_condition = f"Invalidated on a close above {_fmt(stop)} (structural resistance / volatility floor)"
        bias = "short"

    else:  # Neutral
        ma20_str = _fmt(ma20) if ma20 is not None else "n/a"
        return {
            "bias": "none",
            "summary": (
                f"No clear setup — wait for a break of the 20-day MA ({ma20_str}) "
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
                candidate_score = compute_candidate_score(direction, directional_score, volume_ratio, confidence_tier)
                technical_score = calculate_technical_score(volume_ratio, signals["trend_metric"], signals["mom_blend"])
                key_signals = build_key_signals(direction, signals, rsi, volume_ratio)
                trade_plan = compute_trade_plan(direction, price, prices, signals)

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

        # Rank by conviction (Neutrals map to <20 so they sink to the bottom);
        # keep the full universe so the DB prune and the dashboard count stay correct.
        candidates.sort(key=lambda x: x["candidate_score"], reverse=True)

        directional_count = sum(1 for c in candidates if c["direction"] != "Neutral")
        log_info(f"Agent 2 complete: {len(candidates)} coins analyzed ({directional_count} directional)")

        return {
            "status": "success",
            "candidates": candidates,
            "total_candidates": len(candidates),
            "low_signal_environment": directional_count < 5,
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
