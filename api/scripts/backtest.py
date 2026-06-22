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

Disk cache (the key to iterating)
---------------------------------
Historical series are cached to disk on first fetch. Subsequent runs read the
cache and make ZERO API calls, so you can change constants in agent2.py and
re-run instantly without tripping CoinGecko's rate limit. Populate the cache
once (spaced to avoid 429s), then tune freely:

    # 1) populate cache once (spaced; safe on the free tier)
    python3 api/scripts/backtest.py --days 365 --sleep 8
    # 2) tweak conviction constants in agent2.py, then re-run instantly (cache-only)
    python3 api/scripts/backtest.py --days 365            # no API calls if cached

Other flags
-----------
    --coins ...     CoinGecko coin IDs (default: a 12-coin set)
    --days N        history window, daily granularity (free tier ~365 max)
    --stride N      days between evaluation points (default 7)
    --horizon N     forward horizon days (0 = per-timeframe: S=7/M=30/L=90)
    --sleep S       seconds between *network* fetches (cache hits don't sleep)
    --refresh       ignore cache and re-fetch
    --cache-dir D   cache location (default: api/scripts/.backtest_cache)
    --dump FILE     write per-sample rows to CSV for offline analysis

Stdlib-only; stubs infra deps to import the genuine scoring functions.
"""

import argparse
import csv
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
    "litecoin", "stellar", "binancecoin", "bitcoin-cash", "uniswap",
    "near", "aptos", "cosmos", "ethereum-classic", "monero",
    "filecoin", "hedera-hashgraph", "internet-computer", "vechain",
    "algorand", "tezos", "aave", "the-graph", "render-token", "arbitrum",
]
HORIZON_BY_TF = {"Short": 7, "Medium": 30, "Long": 90}
CG_BASE = "https://api.coingecko.com/api/v3"
DEFAULT_CACHE = os.path.join(_HERE, ".backtest_cache")
RETRYABLE = {429, 500, 502, 503, 504}


def fetch_daily(coin_id, days, retries=5):
    """Fetch daily closes/volumes from CoinGecko with backoff on 429/5xx."""
    url = f"{CG_BASE}/coins/{coin_id}/market_chart?vs_currency=usd&days={days}&interval=daily"
    api_key = os.getenv("COINGECKO_API_KEY")
    for attempt in range(retries):
        req = urllib.request.Request(url, headers={"accept": "application/json"})
        if api_key:
            req.add_header("x-cg-demo-api-key", api_key)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.load(resp)
            closes = [p[1] for p in data.get("prices", [])]
            volumes = [v[1] for v in data.get("total_volumes", [])]
            return closes, volumes
        except urllib.error.HTTPError as e:
            if e.code in RETRYABLE and attempt < retries - 1:
                ra = e.headers.get("Retry-After")
                delay = float(ra) if (ra and str(ra).replace(".", "").isdigit()) else 5.0 * (2 ** attempt)
                print(f"  … {coin_id}: HTTP {e.code}; backoff {delay:.0f}s "
                      f"(attempt {attempt + 1}/{retries})", file=sys.stderr)
                time.sleep(delay)
                continue
            raise
        except urllib.error.URLError:
            if attempt < retries - 1:
                time.sleep(5.0 * (2 ** attempt))
                continue
            raise
    raise RuntimeError(f"exhausted retries for {coin_id}")


def cached_series(coin, days, cache_dir, refresh):
    """Return (closes, volumes, from_cache)."""
    path = os.path.join(cache_dir, f"{coin}_{days}.json")
    if not refresh and os.path.exists(path):
        with open(path) as f:
            d = json.load(f)
        return d["closes"], d["volumes"], True
    closes, volumes = fetch_daily(coin, days)
    os.makedirs(cache_dir, exist_ok=True)
    with open(path, "w") as f:
        json.dump({"closes": closes, "volumes": volumes}, f)
    return closes, volumes, False


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


def run_backtest(coins, days, stride, fixed_horizon, cache_dir, refresh, sleep):
    samples = []

    # Precompute the market regime (from BTC) at each index for the regime filter.
    # BTC and every coin share the same trailing 365d window, so index ≈ calendar.
    btc_regime = {}
    try:
        btc_closes, _, _ = cached_series("bitcoin", days, cache_dir, refresh)
        for i in range(A.MIN_PRICES, len(btc_closes)):
            btc_regime[i] = A.market_regime(btc_closes[:i + 1])
    except Exception as e:  # noqa: BLE001
        print(f"  ! could not load BTC for market regime ({e}); gate disabled", file=sys.stderr)

    for coin in coins:
        try:
            closes, volumes, from_cache = cached_series(coin, days, cache_dir, refresh)
        except Exception as e:  # noqa: BLE001 — harness, log and continue
            print(f"  ! {coin}: fetch failed ({e}); skipping", file=sys.stderr)
            continue
        n = len(closes)
        if n < A.MIN_PRICES + 30:
            print(f"  ! {coin}: only {n} closes; skipping", file=sys.stderr)
        else:
            for i in range(A.MIN_PRICES, n, stride):
                window = closes[:i + 1]
                vol_window = volumes[:i + 1]
                price = window[-1]
                rsi = round(calculate_rsi(window, 14), 2)
                vr = A._volume_ratio(vol_window)
                direction, dscore, signals = A.analyze_direction(price, window, rsi, vr)
                timeframe = A.assign_timeframe(direction, rsi, vr, signals)
                confidence = A.assign_confidence(direction, coin.upper(), signals)
                conviction = A.compute_candidate_score(direction, dscore, vr, confidence)

                horizon = fixed_horizon or HORIZON_BY_TF[timeframe]
                if i + horizon >= n:
                    continue
                fwd = (closes[i + horizon] - price) / price
                sign = 1 if direction == "Bullish" else -1 if direction == "Bearish" else 0
                market = btc_regime.get(i, "chop")
                samples.append({
                    "coin": coin, "index": i, "direction": direction,
                    "confidence": confidence, "conviction": conviction,
                    "directional_score": dscore, "timeframe": timeframe,
                    "horizon": horizon, "forward_return": round(fwd, 6),
                    "edge": round(fwd * sign, 6), "sign": sign,
                    "market": market,
                    "regime_ok": A.regime_allows(direction, market, signals),
                })
            tag = "cache" if from_cache else "fetched"
            print(f"  · {coin}: {n} closes ({tag})", file=sys.stderr)
        if not from_cache:
            time.sleep(sleep)  # throttle only real network calls
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

    # Sub-period / regime check: all coins share the same 365d window, so the
    # evaluation index maps to roughly the same calendar date across coins.
    # Splitting by index terciles ~ thirds of the window — reveals whether edge
    # is regime-dependent (a momentum model should have edge in trending thirds,
    # not chop).
    print("\nBy sub-period (index terciles ≈ oldest→newest thirds of the window):")
    idxs = [s["index"] for s in directional]
    if idxs:
        lo, hi = min(idxs), max(idxs)
        span = max(1, (hi - lo) / 3)
        for k, name in enumerate(("early", "mid", "late")):
            chunk = [s for s in directional if min(2, int((s["index"] - lo) / span)) == k]
            print("  " + _summary(name, chunk))

    if neutral:
        mean_abs = sum(abs(s["forward_return"]) for s in neutral) / len(neutral)
        print(f"\nNeutral baseline:        n={len(neutral):5}  mean|return|={mean_abs*100:5.2f}%")

    if directional:
        corr = pearson([s["conviction"] for s in directional], [s["edge"] for s in directional])
        print(f"\ncorr(conviction, edge) = {corr:+.3f}  "
              f"(want clearly positive — higher conviction → higher edge)")

    _baselines(directional)
    _bias_eval(directional)
    _regime_eval(directional)
    print("=" * 64)


def _stats(returns):
    """Per-trade mean/std/Sharpe-per-trade/%positive/t-stat for a return list."""
    n = len(returns)
    if n == 0:
        return None
    mean = sum(returns) / n
    var = sum((r - mean) ** 2 for r in returns) / n if n > 1 else 0.0
    std = math.sqrt(var)
    sharpe = mean / std if std > 0 else float("nan")
    t = mean / (std / math.sqrt(n)) if std > 0 else float("nan")
    pos = sum(1 for r in returns if r > 0) / n
    return {"n": n, "mean": mean, "std": std, "sharpe": sharpe, "t": t, "pos": pos}


def _equity(returns_in_order):
    """Compound an equal-weight, sequential book → (total_return, max_drawdown).
    Approximate (sample horizons overlap) — an illustrative curve, not a live P&L."""
    equity = peak = 1.0
    mdd = 0.0
    for r in returns_in_order:
        equity *= (1 + r)
        peak = max(peak, equity)
        if peak > 0:
            mdd = min(mdd, equity / peak - 1)
    return equity - 1, mdd


def _baselines(directional):
    """The money question: does following the calls beat just holding (beta) and a
    coin-flip (null), risk-adjusted? Normalizes each trade to a per-DAY return so
    mixed 7/30/90d horizons are comparable, then compares three books over the SAME
    samples:
      • Strategy  — long Bullish, short Bearish (what the app implies you'd do)
      • Buy&Hold  — long everything always (pure beta)
      • Skill     — Strategy − Buy&Hold per trade (what the calls ADD over holding)
    """
    if not directional:
        return

    def per_day(s):
        h = max(1, s["horizon"])
        return (1 + s["forward_return"]) ** (1.0 / h) - 1  # geometric daily

    strat = [per_day(s) * s["sign"] for s in directional]
    hold = [per_day(s) for s in directional]                      # always long = beta
    skill = [a - b for a, b in zip(strat, hold)]                  # strategy minus beta

    chron = sorted(directional, key=lambda s: s["index"])
    strat_chron = [per_day(s) * s["sign"] for s in chron]
    hold_chron = [per_day(s) for s in chron]

    print("\n" + "-" * 64)
    print("BASELINES — does following the calls beat holding? (per-DAY returns)")
    print("-" * 64)
    print(f"  {'book':10} {'n':>5} {'mean/day':>9} {'Sharpe/tr':>10} {'%pos':>6} {'t-stat':>7}")
    for label, rets in (("Strategy", strat), ("Buy&Hold", hold), ("Skill", skill)):
        st = _stats(rets)
        print(f"  {label:10} {st['n']:5d} {st['mean']*100:+8.3f}% {st['sharpe']:10.3f} "
              f"{st['pos']*100:5.1f}% {st['t']:+7.2f}")

    s_tot, s_mdd = _equity(strat_chron)
    h_tot, h_mdd = _equity(hold_chron)
    print("\n  Compounded (chronological, equal-weight, illustrative):")
    print(f"    Strategy : total {s_tot*100:+8.1f}%   maxDD {s_mdd*100:6.1f}%")
    print(f"    Buy&Hold : total {h_tot*100:+8.1f}%   maxDD {h_mdd*100:6.1f}%")

    st_abs = _stats(strat)
    sk = _stats(skill)
    n_bull = sum(1 for s in directional if s["direction"] == "Bullish")
    bull_pct = n_bull / len(directional) * 100
    tilt = abs(bull_pct - 50)

    # PRIMARY verdict = did the strategy make money in ABSOLUTE terms (vs 0)?
    abs_v = ("significantly POSITIVE" if st_abs["t"] > 2 else
             "significantly NEGATIVE" if st_abs["t"] < -2 else
             "indistinguishable from zero")
    print(f"\n  VERDICT (absolute return, vs 0): t-stat {st_abs['t']:+.2f} → {abs_v}.")
    print(f"  vs Buy&Hold: Skill t-stat {sk['t']:+.2f}  (book is {bull_pct:.0f}% long).")
    if tilt > 15 and s_tot < 0:
        print("  ⚠ BEATING BUY&HOLD HERE IS A MIRAGE: the book is heavily one-sided in a "
              "trending window, so 'Skill' is mostly being short in a down market (beta), "
              "not timing. The strategy still LOST money in absolute terms.")
    print("  (t>2 ≈ significant; mixed horizons/overlap → directional, not exact.)")


def _bias_eval(directional):
    """Separate skill from market beta: if the calls are one-sided and the sample
    window trended one way, raw 'edge' is mostly directional bias, not timing."""
    if not directional:
        return
    nb = [s for s in directional if s["direction"] == "Bullish"]
    ne = [s for s in directional if s["direction"] == "Bearish"]
    raw = sum(s["forward_return"] for s in directional) / len(directional)
    print("\n" + "-" * 64)
    print("DIRECTIONAL BIAS / BETA CHECK")
    print("-" * 64)
    print(f"  mix: Bullish {len(nb)} ({len(nb)/len(directional)*100:.0f}%) | "
          f"Bearish {len(ne)} ({len(ne)/len(directional)*100:.0f}%)")
    print("  " + _summary("Bullish edge", nb))
    print("  " + _summary("Bearish edge", ne))
    print(f"  mean RAW forward return (all calls) = {raw*100:+.2f}%  "
          f"(far from 0 ⇒ one-directional market sample; 'edge' may be beta)")
    print("  edge by direction × market regime:")
    for dr in ("Bullish", "Bearish"):
        for mk in ("up", "down", "chop"):
            sub = [s for s in directional if s["direction"] == dr and s.get("market") == mk]
            print("    " + _summary(f"{dr}/{mk}", sub))


def _regime_eval(directional):
    """Compare edge with vs without the regime filter (the prototype's verdict)."""
    if not any("regime_ok" in s for s in directional):
        return
    taken = [s for s in directional if s["regime_ok"]]
    blocked = [s for s in directional if not s["regime_ok"]]
    cov = len(taken) / len(directional) * 100 if directional else 0

    print("\n" + "-" * 64)
    print("REGIME FILTER (BTC market trend + per-coin trend quality)")
    print("-" * 64)
    print(_summary("all directional (no gate)", directional))
    print(_summary("TAKEN (gate passed)", taken) + f"   coverage={cov:.0f}%")
    print(_summary("BLOCKED (gate failed)", blocked))

    # Does the gate fix the losing late/chop third?
    print("\n  Sub-period — TAKEN only:")
    idxs = [s["index"] for s in taken]
    if idxs:
        lo, hi = min(idxs), max(idxs)
        span = max(1, (hi - lo) / 3)
        for k, name in enumerate(("early", "mid", "late")):
            chunk = [s for s in taken if min(2, int((s["index"] - lo) / span)) == k]
            print("    " + _summary(name, chunk))

    # Out-of-sample stability: coin train/test split on TAKEN
    coins = sorted({s["coin"] for s in taken})
    if len(coins) >= 4:
        half = len(coins) // 2
        train = [s for s in taken if s["coin"] in set(coins[:half])]
        test = [s for s in taken if s["coin"] in set(coins[half:])]
        print("\n  Out-of-sample (coin split) — TAKEN:")
        print("    " + _summary("train coins", train))
        print("    " + _summary("test coins", test))


def dump_samples(samples, path):
    cols = ["coin", "index", "direction", "confidence", "conviction",
            "directional_score", "timeframe", "horizon", "forward_return", "edge",
            "market", "regime_ok"]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for s in samples:
            w.writerow({k: s[k] for k in cols})
    print(f"\nWrote {len(samples)} sample rows -> {path}", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description="Backtest the Agent 2 scoring model.")
    ap.add_argument("--coins", nargs="+", default=DEFAULT_COINS)
    ap.add_argument("--days", type=int, default=365)
    ap.add_argument("--stride", type=int, default=7)
    ap.add_argument("--horizon", type=int, default=0, help="0 = per-timeframe")
    ap.add_argument("--sleep", type=float, default=8.0, help="seconds between network fetches")
    ap.add_argument("--refresh", action="store_true", help="ignore cache, re-fetch")
    ap.add_argument("--cache-dir", default=DEFAULT_CACHE)
    ap.add_argument("--dump", default=None, help="write per-sample CSV to this path")
    args = ap.parse_args()

    print(f"Backtesting {len(args.coins)} coins over {args.days}d (stride {args.stride}d); "
          f"cache={args.cache_dir}", file=sys.stderr)
    samples = run_backtest(args.coins, args.days, args.stride, args.horizon,
                           args.cache_dir, args.refresh, args.sleep)
    if not samples:
        print("No samples produced.", file=sys.stderr)
        sys.exit(1)
    report(samples, args.horizon)
    if args.dump:
        dump_samples(samples, args.dump)


if __name__ == "__main__":
    main()
