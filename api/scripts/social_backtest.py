#!/usr/bin/env python3
"""
Backtest LunarCrush SOCIAL signals — do they predict forward returns, and (the
real question) do they ADD edge over price alone?

Data: LunarCrush /coins/{sym}/time-series/v2 returns a year of DAILY rows with
both social (sentiment, galaxy_score, alt_rank, posts, interactions, contributors,
social_dominance, spam) AND price (close). One aligned series per coin — no
external join, no look-ahead.

Method (mirrors the honest discipline of backtest.py / xsec_backtest.py):
  • Cross-sectional, MARKET-NEUTRAL: each rebalance, rank the universe by a signal,
    long the top quantile / short the bottom, judge the spread vs ZERO (beta
    stripped — a long-short book can't hide behind "everything went up/down").
  • Net of costs, with Sharpe/t-stat/hit/drawdown and a %long tilt column.
  • A price-momentum signal is included as the baseline: a social signal only
    "adds" if it beats price_mom AND beats zero.
  • Pooled corr(signal, forward_return) as a standalone-predictiveness check.

Honesty: single ~1y window; treat a positive net t-stat as a GREEN LIGHT to wire
in + validate live, not proof. Caches series to disk so re-runs are instant.

    python3 api/scripts/social_backtest.py                 # fetch (spaced) + report
    python3 api/scripts/social_backtest.py --universe 40 --horizon 7 --stride 7
Needs LUNARCRUSH_API_KEY (read from env / .env.local).
"""

import argparse
import json
import math
import os
import sys
import time
import urllib.request
import urllib.parse
from collections import defaultdict

_HERE = os.path.dirname(os.path.abspath(__file__))
BASE = "https://lunarcrush.com/api4/public"
UA = "Mozilla/5.0 (compatible; sentics/1.0)"
DEFAULT_CACHE = os.path.join(_HERE, ".social_cache")
STABLE = {"USDT", "USDC", "DAI", "FDUSD", "TUSD", "USDE", "USDS", "PYUSD", "BUSD", "GUSD", "USDP"}


def _load_env():
    p = os.path.join(os.path.dirname(os.path.dirname(_HERE)), ".env.local")
    if os.path.exists(p):
        for line in open(p):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def _get(path):
    req = urllib.request.Request(
        f"{BASE}/{path}",
        headers={"Authorization": f"Bearer {os.environ['LUNARCRUSH_API_KEY']}", "User-Agent": UA},
    )
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.load(r)


def universe(n, cache_dir):
    """Top-n non-stablecoins by market cap → list of (symbol, id)."""
    path = os.path.join(cache_dir, "universe.json")
    if os.path.exists(path):
        rows = json.load(open(path))
    else:
        rows = _get("coins/list/v2").get("data", [])
        os.makedirs(cache_dir, exist_ok=True)
        json.dump(rows, open(path, "w"))
    cand = [r for r in rows if (r.get("symbol") or "").upper() not in STABLE and r.get("market_cap")]
    cand.sort(key=lambda r: -(r.get("market_cap") or 0))
    return [((r.get("symbol") or "").upper(), r.get("id")) for r in cand[:n]]


def fetch_series(sym, cache_dir, sleep, refresh):
    path = os.path.join(cache_dir, f"{sym}_1y.json")
    if not refresh and os.path.exists(path):
        return json.load(open(path)), True
    data = _get(f"coins/{urllib.parse.quote(sym.lower())}/time-series/v2?bucket=day&interval=1y")
    rows = data.get("data", []) or []
    os.makedirs(cache_dir, exist_ok=True)
    json.dump(rows, open(path, "w"))
    time.sleep(sleep)
    return rows, False


# ── signal primitives (all use only data up to index i) ──────────────────────
def val(s, i, f):
    v = s[i].get(f)
    if isinstance(v, (int, float)):
        return v
    try:
        return float(v)  # LunarCrush returns some numerics (e.g. close) as strings
    except (TypeError, ValueError):
        return None


def chg(s, i, k, f):
    a, b = val(s, i, f), (val(s, i - k, f) if i - k >= 0 else None)
    return None if a is None or b is None else a - b


def mom(s, i, k):
    a, b = val(s, i, "close"), (val(s, i - k, "close") if i - k >= 0 else None)
    return None if a is None or not b else a / b - 1


def velocity(s, i, k, f):
    cur = val(s, i, f)
    if cur is None or i - k < 0:
        return None
    hist = [val(s, j, f) for j in range(i - k, i)]
    hist = [x for x in hist if x is not None]
    if not hist:
        return None
    m = sum(hist) / len(hist)
    return None if m <= 0 else cur / m - 1


SIGNALS = {
    "sentiment (level)":        lambda s, i: val(s, i, "sentiment"),
    "sentiment Δ7":             lambda s, i: chg(s, i, 7, "sentiment"),
    "galaxy (level)":           lambda s, i: val(s, i, "galaxy_score"),
    "galaxy Δ7":                lambda s, i: chg(s, i, 7, "galaxy_score"),
    "altrank (inv level)":      lambda s, i: (-val(s, i, "alt_rank")) if val(s, i, "alt_rank") is not None else None,
    "altrank improve7":         lambda s, i: (-chg(s, i, 7, "alt_rank")) if chg(s, i, 7, "alt_rank") is not None else None,
    "posts velocity14":         lambda s, i: velocity(s, i, 14, "posts_active"),
    "interactions velocity14":  lambda s, i: velocity(s, i, 14, "interactions"),
    "contributors velocity14":  lambda s, i: velocity(s, i, 14, "contributors_active"),
    "social_dom Δ7":            lambda s, i: chg(s, i, 7, "social_dominance"),
    "[price_mom30 baseline]":   lambda s, i: mom(s, i, 30),
}


def _stats(rs):
    n = len(rs)
    if n < 2:
        return None
    m = sum(rs) / n
    sd = math.sqrt(sum((r - m) ** 2 for r in rs) / n)
    return {"n": n, "mean": m, "sharpe": (m / sd) if sd else float("nan"),
            "t": m / (sd / math.sqrt(n)) if sd else float("nan"),
            "hit": sum(1 for r in rs if r > 0) / n}


def _dd(rs):
    eq = peak = 1.0
    mdd = 0.0
    for r in rs:
        eq *= (1 + r)
        peak = max(peak, eq)
        mdd = min(mdd, eq / peak - 1)
    return eq - 1, mdd


def pearson(xs, ys):
    n = len(xs)
    if n < 2:
        return float("nan")
    mx, my = sum(xs) / n, sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    vy = math.sqrt(sum((y - my) ** 2 for y in ys))
    return cov / (vx * vy) if vx and vy else float("nan")


def build(series_by_sym):
    """Per coin: ordered rows + {day_index: position}. Aligns coins by calendar day."""
    coins = {}
    for sym, rows in series_by_sym.items():
        rows = [r for r in rows if r.get("time") and r.get("close")]
        rows.sort(key=lambda r: r["time"])
        if len(rows) < 60:
            continue
        daymap = {int(r["time"] // 86400): idx for idx, r in enumerate(rows)}
        coins[sym] = (rows, daymap)
    return coins


def run(coins, horizon, stride, q, cost_bps):
    days = sorted({d for _, dm in coins.values() for d in dm})
    results = {}
    pooled = defaultdict(lambda: ([], []))  # signal -> (signal_vals, fwd_rets)
    for name, fn in SIGNALS.items():
        periods = []
        for D in range(days[0], days[-1] + 1, stride):
            rows = []
            for sym, (series, dm) in coins.items():
                if D not in dm or (D + horizon) not in dm:
                    continue
                i = dm[D]
                sig = fn(series, i)
                if sig is None:
                    continue
                c0, c1 = val(series, i, "close"), val(series, dm[D + horizon], "close")
                if not c0 or c1 is None:
                    continue
                fwd = c1 / c0 - 1
                rows.append((sig, fwd))
                sv, fv = pooled[name]
                sv.append(sig); fv.append(fwd)
            if len(rows) < 8:
                continue
            rows.sort(key=lambda r: r[0])
            k = max(1, int(len(rows) * q))
            short_r = sum(r[1] for r in rows[:k]) / k
            long_r = sum(r[1] for r in rows[-k:]) / k
            ls = long_r - short_r
            periods.append(ls - 4 * (cost_bps / 1e4))  # net of cost
        results[name] = periods
    return results, pooled, len(days)


def main():
    ap = argparse.ArgumentParser(description="Backtest LunarCrush social signals.")
    ap.add_argument("--universe", type=int, default=40)
    ap.add_argument("--horizon", type=int, default=7)
    ap.add_argument("--stride", type=int, default=7)
    ap.add_argument("--q", type=float, default=0.25)
    ap.add_argument("--cost-bps", type=float, default=10.0)
    ap.add_argument("--sleep", type=float, default=0.8)
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--cache-dir", default=DEFAULT_CACHE)
    args = ap.parse_args()
    _load_env()
    if not os.getenv("LUNARCRUSH_API_KEY"):
        sys.exit("LUNARCRUSH_API_KEY not set (add to .env.local).")

    uni = universe(args.universe, args.cache_dir)
    print(f"Fetching {len(uni)} coins' 1y daily social+price series…", file=sys.stderr)
    series_by_sym = {}
    for sym, _id in uni:
        try:
            rows, cached = fetch_series(sym, args.cache_dir, args.sleep, args.refresh)
            series_by_sym[sym] = rows
            print(f"  · {sym}: {len(rows)} rows ({'cache' if cached else 'fetched'})", file=sys.stderr)
        except Exception as e:  # noqa: BLE001
            print(f"  ! {sym}: {e}", file=sys.stderr)

    coins = build(series_by_sym)
    results, pooled, ndays = run(coins, args.horizon, args.stride, args.q, args.cost_bps)

    print("\n" + "=" * 82)
    print(f"SOCIAL SIGNAL BACKTEST  ({len(coins)} coins, ~{ndays}d, rebalance {args.stride}d, "
          f"hold {args.horizon}d, q={args.q}, cost={args.cost_bps}bps/side)")
    print("=" * 82)
    print("Market-neutral long-short spread (net of cost), judged vs ZERO. corr = pooled")
    print("corr(signal, forward return). A social signal only ADDS value if it beats the")
    print("price_mom30 baseline AND beats zero.\n")
    print(f"  {'signal':26} {'n':>4} {'mean/reb':>9} {'Sharpe':>7} {'t':>6} {'hit':>5} {'cum':>8} {'maxDD':>6} {'corr':>6}")
    ranked = sorted(results.items(), key=lambda kv: -((_stats(kv[1]) or {}).get("t") or -9))
    for name, periods in ranked:
        st = _stats(periods)
        if not st:
            print(f"  {name:26} n<2"); continue
        cum, mdd = _dd(periods)
        sv, fv = pooled[name]
        corr = pearson(sv, fv) if len(sv) > 2 else float("nan")
        print(f"  {name:26} {st['n']:4} {st['mean']*100:+8.2f}% {st['sharpe']:+7.2f} {st['t']:+6.2f} "
              f"{st['hit']*100:4.0f}% {cum*100:+7.1f}% {mdd*100:5.0f}% {corr:+6.3f}")

    base = _stats(results.get("[price_mom30 baseline]", []))
    base_t = (base or {}).get("t") or 0
    winners = [n for n, p in results.items() if not n.startswith("[") and (_stats(p) or {}).get("t", -9) > 2
               and (_stats(p) or {}).get("t", -9) > base_t]
    print("\n" + "-" * 82)
    if winners:
        print(f"CANDIDATES that beat zero (t>2) AND the price baseline: {', '.join(winners)}")
        print("→ Worth wiring in (calibrated) + validating live. Still one window — not proof.")
    else:
        print("NO social signal beats both zero (t>2) and the price_mom baseline on this window.")
        print("→ Social does not add demonstrable edge here. Do NOT wire it into the calls yet.")
    print("=" * 82)


if __name__ == "__main__":
    main()
