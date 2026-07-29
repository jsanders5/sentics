#!/usr/bin/env python3
"""
Evaluate the LIVE trade-call ledger (call_snapshots) — leak-free forward tracking.

The pipeline appends one immutable row per directional call per run, including the
price at call time. Because price is recorded every run, we can measure realized
forward returns FROM THE LEDGER ITSELF: join each call to the same coin's later
snapshot ~horizon days out. No external API, no look-ahead — the realized price was
genuinely unknown when the call was made.

    python3 api/scripts/eval_calls.py                 # per-timeframe horizon (S=7/M=30/L=90)
    python3 api/scripts/eval_calls.py --horizon 7      # fixed 7-day horizon
    python3 api/scripts/eval_calls.py --tolerance 3    # accept a match within h..h+3 days

Needs SUPABASE_URL and SUPABASE_SECRET_KEY in the environment (read from .env.local
if present). Results only appear once calls have MATURED (≥ horizon days of history),
so the first Medium/Long readings are weeks out — that's the nature of forward tracking.
"""

import argparse
import json
import math
import os
import re
import sys
import urllib.request
import urllib.error
from collections import defaultdict
from datetime import datetime, timedelta

HORIZON_BY_TF = {"Short": 7, "Medium": 30, "Long": 90}


def _load_env():
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env.local")
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())


def fetch_snapshots():
    base = os.environ.get("SUPABASE_URL", "").rstrip("/")
    key = os.environ.get("SUPABASE_SECRET_KEY", "")
    if not base or not key:
        sys.exit("SUPABASE_URL / SUPABASE_SECRET_KEY not set (add them to .env.local).")
    url = (f"{base}/rest/v1/call_snapshots"
           "?select=captured_at,symbol,direction,candidate_score,confidence_tier,time_horizon,price"
           "&order=symbol.asc,captured_at.asc&limit=100000")
    req = urllib.request.Request(url, headers={"apikey": key, "Authorization": f"Bearer {key}"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            sys.exit("call_snapshots table not found — apply migrations/008_add_call_snapshots.sql first.")
        raise


def _ts(s):
    s = s.replace("Z", "+00:00")
    # Normalize fractional seconds to exactly 6 digits — Postgres emits variable
    # precision (e.g. .18786) and py3.9's fromisoformat only accepts 3 or 6.
    s = re.sub(r"\.(\d+)", lambda m: "." + (m.group(1) + "000000")[:6], s)
    return datetime.fromisoformat(s)


def _stats(returns):
    n = len(returns)
    if n == 0:
        return None
    mean = sum(returns) / n
    std = math.sqrt(sum((r - mean) ** 2 for r in returns) / n) if n > 1 else 0.0
    return {
        "n": n, "mean": mean, "std": std,
        "sharpe": mean / std if std > 0 else float("nan"),
        "t": mean / (std / math.sqrt(n)) if std > 0 else float("nan"),
        "pos": sum(1 for r in returns if r > 0) / n,
    }


def evaluate(rows, fixed_horizon, tol):
    by_sym = defaultdict(list)
    for r in rows:
        if r.get("price") and r.get("direction") in ("Bullish", "Bearish"):
            by_sym[r["symbol"]].append(r)

    samples = []
    for sym, snaps in by_sym.items():
        snaps.sort(key=lambda r: r["captured_at"])
        for i, call in enumerate(snaps):
            h = fixed_horizon or HORIZON_BY_TF.get(call.get("time_horizon") or "Medium", 30)
            t0 = _ts(call["captured_at"])
            want = t0 + timedelta(days=h)
            # earliest later snapshot at/after the horizon, within tolerance
            realized = next((s for s in snaps[i + 1:]
                             if want <= _ts(s["captured_at"]) <= want + timedelta(days=tol)), None)
            if not realized or not realized.get("price"):
                continue
            fwd = (realized["price"] - call["price"]) / call["price"]
            sign = 1 if call["direction"] == "Bullish" else -1
            samples.append({
                "symbol": sym, "direction": call["direction"], "horizon": h,
                "conviction": call.get("candidate_score") or 0,
                "confidence": call.get("confidence_tier") or "?",
                "forward_return": fwd, "edge": fwd * sign, "sign": sign,
            })
    return samples


def _line(label, rows):
    if not rows:
        return f"  {label:22} n=0"
    e = [r["edge"] for r in rows]
    return (f"  {label:22} n={len(rows):4}  edge={sum(e)/len(e)*100:+6.2f}%  "
            f"hit={sum(1 for r in rows if r['edge']>0)/len(rows)*100:5.1f}%")


def report(samples):
    print("\n" + "=" * 60)
    print(f"LIVE CALL LEDGER — {len(samples)} matured calls")
    print("=" * 60)
    if not samples:
        print("\nNo calls have matured yet. Re-run after enough days of snapshots\n"
              "have accrued (Short=7d, Medium=30d, Long=90d).")
        print("=" * 60)
        return

    print(_line("ALL directional", samples))
    print("\nBy confidence tier:")
    by_c = defaultdict(list)
    for s in samples:
        by_c[s["confidence"]].append(s)
    for t in ("High", "Medium", "Low"):
        print(_line(t, by_c.get(t, [])))

    print("\nBy conviction bucket:")
    bucket = lambda c: "85+" if c >= 85 else "70-85" if c >= 70 else "50-70" if c >= 50 else "<50"
    by_b = defaultdict(list)
    for s in samples:
        by_b[bucket(s["conviction"])].append(s)
    for b in ("50-70", "70-85", "85+"):
        print(_line(b, by_b.get(b, [])))

    # Honest baseline: strategy (long bull/short bear) vs buy&hold (always long).
    def per_day(s):
        return (1 + s["forward_return"]) ** (1.0 / max(1, s["horizon"])) - 1
    strat = [per_day(s) * s["sign"] for s in samples]
    hold = [per_day(s) for s in samples]
    skill = [a - b for a, b in zip(strat, hold)]
    sa, sk = _stats(strat), _stats(skill)
    bull_pct = sum(1 for s in samples if s["sign"] == 1) / len(samples) * 100
    print("\nBaselines (per-day return):")
    print(f"  Strategy abs return: t-stat {sa['t']:+.2f}  ({'POSITIVE' if sa['t']>2 else 'NEGATIVE' if sa['t']<-2 else '~zero'})")
    print(f"  vs Buy&Hold (Skill): t-stat {sk['t']:+.2f}  (book {bull_pct:.0f}% long)")
    if len(samples) < 100:
        print("  ⚠ small sample — treat as provisional until more calls mature.")
    print("=" * 60)


def main():
    ap = argparse.ArgumentParser(description="Evaluate the live trade-call ledger.")
    ap.add_argument("--horizon", type=int, default=0, help="0 = per-timeframe (S=7/M=30/L=90)")
    ap.add_argument("--tolerance", type=int, default=3, help="days of slack when matching the horizon snapshot")
    args = ap.parse_args()
    _load_env()
    rows = fetch_snapshots()
    print(f"Loaded {len(rows)} call snapshots.", file=sys.stderr)
    report(evaluate(rows, args.horizon, args.tolerance))


if __name__ == "__main__":
    main()
