#!/usr/bin/env python3
"""
Cross-sectional backtest — market-neutral factor strategies.

Why this exists
---------------
Single-asset directional TA on the top-25 (backtest.py) showed no skill — its
"edge" was mostly beta (net-short in a down year). This harness tests the place
documented crypto edges actually live: RANK the universe each period and go
LONG the top / SHORT the bottom. That book is (roughly) dollar-neutral, so it
STRIPS BETA — the long-short spread can't hide behind "everything went down."
We judge the spread against ZERO, not against buy-and-hold.

Signals tested
--------------
  • Momentum   — long recent winners / short recent losers (trailing return).
  • Reversal   — the opposite (fade recent moves) over a short window.

Honesty
-------
  • Net-of-cost is reported alongside gross (long-short rebalancing has real
    turnover; default 10 bps/side, entry+exit, both legs ⇒ ~0.4%/rebalance).
  • Single ~365d window and a small cached universe → treat as a SCREEN, not
    proof. Broaden the universe (populate more coins into the cache) for a real
    read; a positive net long-short t-stat here just says "worth pursuing".

Data: reuses api/scripts/.backtest_cache (populate via backtest.py first). Uses
EVERY coin cached for the chosen --days, reverse-aligned to a common recent window.

    python3 api/scripts/xsec_backtest.py                 # zero API calls if cached
    python3 api/scripts/xsec_backtest.py --stride 7 --horizon 7 --q 0.3 --cost-bps 10
"""

import argparse
import json
import math
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CACHE = os.path.join(_HERE, ".backtest_cache")


def load_universe(cache_dir, days, min_history):
    suffix = f"_{days}.json"
    series = {}
    if not os.path.isdir(cache_dir):
        sys.exit(f"No cache at {cache_dir}. Populate it first: python3 api/scripts/backtest.py --days {days} --sleep 8")
    for fn in os.listdir(cache_dir):
        if fn.endswith(suffix):
            coin = fn[:-len(suffix)]
            with open(os.path.join(cache_dir, fn)) as f:
                closes = (json.load(f).get("closes") or [])
            if len(closes) >= min_history and all(c > 0 for c in closes[-min_history:]):
                series[coin] = closes
    return series


def align(series):
    """Reverse-align every series to a common recent window (index -1 = latest)."""
    n = min(len(v) for v in series.values())
    return {k: v[-n:] for k, v in series.items()}, n


def momentum(px, t, lookback):
    if t - lookback < 0 or px[t - lookback] <= 0:
        return None
    return px[t] / px[t - lookback] - 1


def reversal(px, t, lookback):
    m = momentum(px, t, lookback)
    return None if m is None else -m


def eval_signal(aligned, n, signal_fn, lookback, horizon, stride, q, cost_bps):
    coins = list(aligned)
    periods = []
    for t in range(lookback + 1, n - horizon, stride):
        rows = []
        for c in coins:
            sig = signal_fn(aligned[c], t, lookback)
            if sig is None:
                continue
            fwd = aligned[c][t + horizon] / aligned[c][t] - 1
            rows.append((sig, fwd))
        if len(rows) < 6:
            continue
        rows.sort(key=lambda r: r[0])
        k = max(1, int(len(rows) * q))
        short_r = sum(r[1] for r in rows[:k]) / k          # lowest signal
        long_r = sum(r[1] for r in rows[-k:]) / k           # highest signal
        ew = sum(r[1] for r in rows) / len(rows)            # basket (beta)
        ls = long_r - short_r
        # cost: both legs, entry+exit ≈ 4 × per-side bps of notional per rebalance
        ls_net = ls - 4 * (cost_bps / 1e4)
        periods.append({"ls": ls, "ls_net": ls_net, "long": long_r, "short": short_r, "ew": ew})
    return periods


def metrics(periods, key, stride):
    rs = [p[key] for p in periods]
    n = len(rs)
    if n < 2:
        return None
    mean = sum(rs) / n
    std = math.sqrt(sum((r - mean) ** 2 for r in rs) / n)
    ppy = 365.0 / stride
    eq = peak = 1.0
    mdd = 0.0
    for r in rs:
        eq *= (1 + r)
        peak = max(peak, eq)
        mdd = min(mdd, eq / peak - 1)
    return {
        "n": n, "mean": mean,
        "sharpe": (mean / std) * math.sqrt(ppy) if std > 0 else float("nan"),
        "t": mean / (std / math.sqrt(n)) if std > 0 else float("nan"),
        "hit": sum(1 for r in rs if r > 0) / n,
        "cum": eq - 1, "mdd": mdd,
    }


def _row(label, m):
    if not m:
        return f"  {label:22} n<2"
    return (f"  {label:22} n={m['n']:3}  mean/reb={m['mean']*100:+5.2f}%  "
            f"Sharpe={m['sharpe']:+5.2f}  t={m['t']:+5.2f}  hit={m['hit']*100:4.0f}%  "
            f"cum={m['cum']*100:+6.1f}%  DD={m['mdd']*100:5.0f}%")


def main():
    ap = argparse.ArgumentParser(description="Cross-sectional market-neutral backtest.")
    ap.add_argument("--days", type=int, default=365)
    ap.add_argument("--stride", type=int, default=7, help="days between rebalances")
    ap.add_argument("--horizon", type=int, default=7, help="holding period (days)")
    ap.add_argument("--q", type=float, default=0.3, help="long/short quantile fraction")
    ap.add_argument("--cost-bps", type=float, default=10.0, help="per-side transaction cost (bps)")
    ap.add_argument("--min-history", type=int, default=150)
    ap.add_argument("--cache-dir", default=DEFAULT_CACHE)
    args = ap.parse_args()

    series = load_universe(args.cache_dir, args.days, args.min_history)
    if len(series) < 6:
        sys.exit(f"Only {len(series)} coins cached — need ≥6 for a cross-section. "
                 f"Populate more: python3 api/scripts/backtest.py --days {args.days} --coins ... --sleep 8")
    aligned, n = align(series)

    print("=" * 78)
    print(f"CROSS-SECTIONAL BACKTEST  ({len(aligned)} coins, {n}d aligned window, "
          f"rebalance {args.stride}d, hold {args.horizon}d, q={args.q}, cost={args.cost_bps}bps/side)")
    print("=" * 78)
    print("Market-neutral long-short spread — judged vs ZERO (beta is stripped).\n")

    configs = ([("Momentum", momentum, lb) for lb in (14, 30, 60, 90)]
               + [("Reversal", reversal, lb) for lb in (3, 7, 14)])

    best = None
    for name, fn, lb in configs:
        periods = eval_signal(aligned, n, fn, lb, args.horizon, args.stride, args.q, args.cost_bps)
        g = metrics(periods, "ls", args.stride)
        net = metrics(periods, "ls_net", args.stride)
        print(f"{name} (lookback {lb}d):")
        print(_row("  long-short GROSS", g))
        print(_row("  long-short NET", net))
        if net and (best is None or (net["t"] or -9) > best[1]):
            best = (f"{name} {lb}d", net["t"], net["sharpe"])
        print()

    ew = metrics(eval_signal(aligned, n, momentum, 30, args.horizon, args.stride, args.q, args.cost_bps),
                 "ew", args.stride)
    print(_row("Equal-weight basket (beta)", ew))

    print("\n" + "-" * 78)
    if best:
        sig, t, sh = best
        verdict = ("WORTH PURSUING — positive net edge" if t and t > 2 else
                   "weak/inconclusive" if t and t > 1 else "NO net edge")
        print(f"Best net long-short: {sig}  (t={t:+.2f}, Sharpe={sh:+.2f}) → {verdict}.")
    print("Caveats: single ~365d window; small universe; costs approximate. A positive")
    print("net t-stat here is a GREEN LIGHT to broaden the universe + validate OOS, not proof.")
    print("=" * 78)


if __name__ == "__main__":
    main()
