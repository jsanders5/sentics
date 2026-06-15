#!/usr/bin/env python3
"""
Backtest harness for the Agent 2 scoring model.

Purpose
-------
The scoring constants in `agent2.py` (W_TREND/W_MOM/W_RSI, K_TREND/K_MOM,
RSI_PEAK/RSI_WIDTH, DIR_THRESHOLD, the conviction bands, timeframe thresholds)
are analytically sound but UN-BACKTESTED. This harness replays the REAL scoring
functions over historical daily closes and measures whether the model's calls
actually predict forward returns — so the constants can be calibrated against
evidence instead of intuition.

What it measures
----------------
For each coin, it walks forward day by day (stride configurable). At each step it
computes the model on the trailing window (exactly as the live pipeline would),
then looks `horizon` days into the future and records the realized return.

Reported metrics:
  - Directional EDGE = mean of (forward_return * directional_sign). Positive means
    the model's Bullish/Bearish calls are right on average.
  - Hit rate (sign correct) for directional calls.
  - Edge broken down by confidence tier (High should beat Low) and conviction
    bucket (higher conviction should mean higher edge — that's the whole premise).
  - Neutral baseline (mean |return|).
  - Pearson corr(conviction, signed forward return) for directional calls.

This does NOT tune constants automatically — it gives you the evaluation signal to
tune them by hand (or to wrap in a sweep). It is intentionally dependency-free
(stdlib only) so it runs anywhere.

Usage
-----
    python3 api/scripts/backtest.py                          # default coin set, 365d
    python3 api/scripts/backtest.py --coins bitcoin ethereum solana --days 365
    python3 api/scripts/backtest.py --stride 7 --horizon 30  # fixed 30d horizon

Notes
-----
  - Pulls daily closes from CoinGecko `market_chart` (free tier; ~365 days max of
    daily granularity per call). Honors COINGECKO_API_KEY if set. Throttles 1.5s
    between calls. A handful of coins over 365 days is plenty to see the signal.
  - `--horizon 0` (default) uses the timeframe-appropriate horizon per call
    (Short=7, Medium=30, Long=90). Pass a number to force a fixed horizon.
"""

import argparse
import json
import math
import os
import sys
import time
import types
import urllib.request
import urllib.error
from collections import defaultdict

# --- Make the real agent2 scoring importable without its infra deps -----------
# utils.py imports redis / sentry_sdk / requests and calls sentry_sdk.init() at
# module load. Stub those so we can import the genuine scoring functions; we fetch
# data ourselves with urllib (no requests dependency).
_HERE = os.path.dirname(os.path.abspath(__file__))
_API_DIR = os.path.dirname(_HERE)            # .../api
if _API_DIR not in sys.path:
    sys.path.insert(0, _API_DIR)

for _name in ("redis", "sentry_sdk", "requests"):
    if _name not in sys.modules:
        sys.modules[_name] = types.ModuleType(_name)
sys.modules["sentry_sdk"].init = lambda *a, **k: None
sys.modules["sentry_sdk"].capture_exception = lambda *a, **k: None
sys.modules["redis"].Redis = type("Redis", (), {"from_url": staticmethod(lambda *a, **k: None)})
for _attr in ("RequestException", "HTTPError"):
    setattr(sys.modules["requests"], _attr, type(_attr, (Exception,), {}))
sys.modules["requests"].get = lambda *a, **k: None

from lib.agents import agent2 as A          # noqa: E402  (real scoring functions)
from lib.agents.utils import calculate_rsi  # noqa: E402

DEFAULT_COINS = [
    "bitcoin", "ethereum", "solana", "ripple", "cardano",
    "dogecoin", "chainlink", "avalanche-2", "tron", "polkadot",
]
HORIZON_BY_TF = {"Short": 7, "Medium": 30, "Long": 90}
CG_BASE = "https://api.coingecko.com/api/v3"


def fetch_daily(coin_id, days):
    """Return (closes, volumes) daily lists from CoinGecko market_chart."""
    url = f"{CG_BASE}/coins/{coin_id}/market_chart?vs_currency=usd&days={days}&interval=daily"
    req = urllib.request.Request(url, headers={"accept": "application/json"})
    api_key = os.getenv("COINGECKO_API_KEY")
    if api_key:
        req.add_header("x-cg-demo-api-key", api_key)
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    closes = [p[1] for p in data.get("prices", [])]
    volumes = [v[1] for v in data.get("total_volumes", [])]
    return closes, volumes


def pearson(xs, ys):
    n = len(xs)
    if n < 2:
        return float("nan")
    mx, my = sum(xs) / n, sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    vy = math.sqrt(sum((y - my) ** 2 for y in ys))
    if vx == 0 or vy == 0:
        return float("nan")
    return cov / (vx * vy)


def conviction_bucket(c):
    if c < 50:
        return "neutral(<50)"
    if c < 70:
        return "50-70"
    if c < 85:
        return "70-85"
    return "85+"


def run_backtest(coins, days, stride, fixed_horizon):
    samples = []  # one dict per evaluated point
    for coin in coins:
        try:
            closes, volumes = fetch_daily(coin, days)
        except (urllib.error.URLError, urllib.error.HTTPError, ValueError) as e:
            print(f"  ! {coin}: fetch failed ({e}); skipping", file=sys.stderr)
            time.sleep(1.5)
            continue
        n = len(closes)
        if n < A.MIN_PRICES + 30:
            print(f"  ! {coin}: only {n} closes; skipping", file=sys.stderr)
            time.sleep(1.5)
            continue

        for i in range(A.MIN_PRICES, n, stride):
            window = closes[:i + 1]
            vol_window = volumes[:i + 1]
            price = window[-1]
            rsi = round(calculate_rsi(window, 14), 2)
            vr = A._volume_ratio(vol_window)
            direction, dscore, signals = A.analyze_direction(price, window, rsi, vr)
            timeframe = A.assign_timeframe(direction, rsi, vr, signals)
            confidence = A.assign_confidence(direction, coin.upper(), signals)
            conviction = A.compute_candidate_score(direction, dscore, vr)

            horizon = fixed_horizon or HORIZON_BY_TF[timeframe]
            if i + horizon >= n:
                continue
            fwd = (closes[i + horizon] - price) / price

            sign = 1 if direction == "Bullish" else -1 if direction == "Bearish" else 0
            samples.append({
                "coin": coin, "direction": direction, "confidence": confidence,
                "conviction": conviction, "timeframe": timeframe,
                "fwd": fwd, "edge": fwd * sign, "sign": sign,
            })
        print(f"  · {coin}: {n} closes processed", file=sys.stderr)
        time.sleep(1.5)
    return samples


def _summary(label, rows):
    if not rows:
        return f"{label:24} n=0"
    edges = [r["edge"] for r in rows]
    mean_edge = sum(edges) / len(edges)
    hits = sum(1 for r in rows if r["edge"] > 0) / len(rows)
    return f"{label:24} n={len(rows):5}  edge={mean_edge*100:+6.2f}%  hit={hits*100:5.1f}%"


def report(samples, fixed_horizon):
    directional = [s for s in samples if s["sign"] != 0]
    neutral = [s for s in samples if s["sign"] == 0]

    print("\n" + "=" * 64)
    print(f"BACKTEST REPORT  ({len(samples)} samples, "
          f"horizon={'per-timeframe' if not fixed_horizon else str(fixed_horizon)+'d'})")
    print("=" * 64)

    print("\nDirectional edge = mean(forward_return × direction sign); >0 = model is right.\n")
    print(_summary("ALL directional", directional))

    print("\nBy confidence tier:")
    by_conf = defaultdict(list)
    for s in directional:
        by_conf[s["confidence"]].append(s)
    for tier in ("High", "Medium", "Low"):
        print("  " + _summary(tier, by_conf.get(tier, [])))

    print("\nBy conviction bucket:")
    by_bucket = defaultdict(list)
    for s in directional:
        by_bucket[conviction_bucket(s["conviction"])].append(s)
    for b in ("50-70", "70-85", "85+"):
        print("  " + _summary(b, by_bucket.get(b, [])))

    print("\nBy timeframe:")
    by_tf = defaultdict(list)
    for s in directional:
        by_tf[s["timeframe"]].append(s)
    for tf in ("Short", "Medium", "Long"):
        print("  " + _summary(tf, by_tf.get(tf, [])))

    if neutral:
        mean_abs = sum(abs(s["fwd"]) for s in neutral) / len(neutral)
        print(f"\nNeutral baseline:        n={len(neutral):5}  mean|return|={mean_abs*100:5.2f}%")

    if directional:
        corr = pearson([s["conviction"] for s in directional], [s["edge"] for s in directional])
        print(f"\ncorr(conviction, edge) = {corr:+.3f}  "
              f"(want clearly positive — higher conviction → higher edge)")
    print("=" * 64)
    print("\nInterpretation: directional edge should be > 0 and rise with confidence")
    print("tier and conviction bucket. If it doesn't, tune the constants in agent2.py")
    print("(thresholds, weights) and re-run. This harness is the evaluation signal.\n")


def main():
    ap = argparse.ArgumentParser(description="Backtest the Agent 2 scoring model.")
    ap.add_argument("--coins", nargs="+", default=DEFAULT_COINS, help="CoinGecko coin IDs")
    ap.add_argument("--days", type=int, default=365, help="history window (daily granularity)")
    ap.add_argument("--stride", type=int, default=7, help="days between evaluation points")
    ap.add_argument("--horizon", type=int, default=0, help="forward horizon days (0 = per-timeframe)")
    args = ap.parse_args()

    print(f"Backtesting {len(args.coins)} coins over {args.days}d "
          f"(stride {args.stride}d)…", file=sys.stderr)
    samples = run_backtest(args.coins, args.days, args.stride, args.horizon)
    if not samples:
        print("No samples produced (all fetches failed?).", file=sys.stderr)
        sys.exit(1)
    report(samples, args.horizon)


if __name__ == "__main__":
    main()
