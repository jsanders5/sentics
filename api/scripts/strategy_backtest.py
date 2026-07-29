#!/usr/bin/env python3
"""
Single-coin mechanical strategy backtest — does a "pick one rule and stick to it"
strategy actually BEAT BUY-AND-HOLD after costs?

Tests four classic long/flat strategies on daily closes:
  1. MA crossover     — long when fast SMA > slow SMA
  2. RSI mean-revert  — enter long when RSI < lo, exit when RSI > hi
  3. Trend filter     — long when close > its N-day SMA
  4. Breakout (Donchian) — enter on N-day-high breakout, exit on M-day-low

Honesty guards (this is where amateur backtests lie):
  • BUY-AND-HOLD is the benchmark — beating "profitable" is trivial in a bull run.
  • Transaction cost on every position change (default 10 bps/side).
  • Risk-adjusted: Sharpe + max drawdown, not just total return.
  • OUT-OF-SAMPLE: parameters are chosen on the early in-sample slice, then judged
    on the later out-of-sample slice the rule never saw. Reported next to the full
    period so overfitting is visible.

Data: LunarCrush daily time-series (OHLC + close), cached to disk.
Needs LUNARCRUSH_API_KEY (from env / .env.local).

    python3 api/scripts/strategy_backtest.py --coin btc --cost-bps 10 --oos 0.35
"""

import argparse
import json
import math
import os
import sys
import urllib.request

_HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(_HERE, ".strategy_cache")


def _load_env():
    p = os.path.join(os.path.dirname(os.path.dirname(_HERE)), ".env.local")
    if os.path.exists(p):
        for line in open(p):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def load_closes(coin, refresh=False):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, f"{coin.lower()}.json")
    if not refresh and os.path.exists(path):
        rows = json.load(open(path))
    else:
        req = urllib.request.Request(
            f"https://lunarcrush.com/api4/public/coins/{coin.lower()}/time-series/v2?bucket=day&interval=all",
            headers={"Authorization": f"Bearer {os.environ['LUNARCRUSH_API_KEY']}", "User-Agent": "Mozilla/5.0"},
        )
        rows = json.load(urllib.request.urlopen(req, timeout=60)).get("data", [])
        json.dump(rows, open(path, "w"))
    closes = []
    for r in rows:
        c = r.get("close")
        try:
            c = float(c)
        except (TypeError, ValueError):
            c = None
        if c and c > 0:
            closes.append(c)
    return closes


# ── indicators ──────────────────────────────────────────────────────────────
def sma(closes, i, n):
    return sum(closes[i - n + 1:i + 1]) / n if i >= n - 1 else None


def rsi_series(closes, period=14):
    out = [None] * len(closes)
    if len(closes) <= period:
        return out
    gains = losses = 0.0
    for i in range(1, period + 1):
        d = closes[i] - closes[i - 1]
        gains += max(d, 0); losses += max(-d, 0)
    ag, al = gains / period, losses / period
    out[period] = 100 - 100 / (1 + (ag / al if al else 999))
    for i in range(period + 1, len(closes)):
        d = closes[i] - closes[i - 1]
        ag = (ag * (period - 1) + max(d, 0)) / period
        al = (al * (period - 1) + max(-d, 0)) / period
        out[i] = 100 - 100 / (1 + (ag / al if al else 999))
    return out


# ── position series (0/1), decided at close i using data through i (no look-ahead) ──
def pos_ma(closes, fast, slow):
    p = [0] * len(closes)
    for i in range(len(closes)):
        f, s = sma(closes, i, fast), sma(closes, i, slow)
        if f is not None and s is not None:
            p[i] = 1 if f > s else 0
    return p


def pos_trend(closes, length):
    p = [0] * len(closes)
    for i in range(len(closes)):
        s = sma(closes, i, length)
        if s is not None:
            p[i] = 1 if closes[i] > s else 0
    return p


def pos_rsi(closes, period, lo, hi):
    r = rsi_series(closes, period)
    p = [0] * len(closes); state = 0
    for i in range(len(closes)):
        if r[i] is None:
            continue
        if state == 0 and r[i] < lo:
            state = 1
        elif state == 1 and r[i] > hi:
            state = 0
        p[i] = state
    return p


def pos_breakout(closes, entry_n, exit_m):
    p = [0] * len(closes); state = 0
    for i in range(len(closes)):
        if i < entry_n:
            continue
        prior_high = max(closes[i - entry_n:i])
        prior_low = min(closes[i - exit_m:i]) if i >= exit_m else None
        if state == 0 and closes[i] > prior_high:
            state = 1
        elif state == 1 and prior_low is not None and closes[i] < prior_low:
            state = 0
        p[i] = state
    return p


# ── engine + metrics ────────────────────────────────────────────────────────
def run(closes, pos, cost_bps):
    """Position pos[i] is held from close i into close i+1 (decided at close i)."""
    eq = 1.0; equity = [1.0]; trades = []; entry = None; exposure = 0
    prev = 0
    for i in range(len(closes) - 1):
        if pos[i] != prev:
            eq *= (1 - cost_bps / 1e4)
            if pos[i] == 1:
                entry = closes[i]
            elif entry is not None:
                trades.append(closes[i] / entry - 1); entry = None
        eq *= (1 + pos[i] * (closes[i + 1] / closes[i] - 1))
        equity.append(eq); exposure += pos[i]; prev = pos[i]
    if entry is not None:
        trades.append(closes[-1] / entry - 1)
    return equity, trades, exposure / max(1, len(closes) - 1)


def metrics(equity, trades, exposure, dpy=365):
    rets = [equity[i + 1] / equity[i] - 1 for i in range(len(equity) - 1)]
    n = len(rets)
    mean = sum(rets) / n
    sd = math.sqrt(sum((r - mean) ** 2 for r in rets) / n) if n else 0
    peak = 1.0; mdd = 0.0
    for e in equity:
        peak = max(peak, e); mdd = min(mdd, e / peak - 1)
    return {
        "total": equity[-1] - 1,
        "cagr": equity[-1] ** (dpy / n) - 1 if n else 0,
        "sharpe": mean / sd * math.sqrt(dpy) if sd else float("nan"),
        "mdd": mdd,
        "trades": len(trades),
        "winrate": (sum(1 for t in trades if t > 0) / len(trades)) if trades else float("nan"),
        "exposure": exposure,
    }


def evaluate(closes, pos, cost_bps):
    return metrics(*run(closes, pos, cost_bps))


STRATEGIES = {
    "MA crossover": (pos_ma, [(10, 50), (20, 100), (50, 200), (20, 50), (50, 150)]),
    "RSI mean-revert": (pos_rsi, [(14, 30, 70), (14, 30, 50), (14, 25, 55), (7, 30, 70), (14, 35, 65)]),
    "Trend filter": (pos_trend, [(100,), (150,), (200,), (50,)]),
    "Breakout": (pos_breakout, [(20, 10), (55, 20), (20, 20), (40, 20), (30, 15)]),
}


def _fmt(m):
    return (f"tot {m['total']*100:+8.0f}%  CAGR {m['cagr']*100:+6.1f}%  Sharpe {m['sharpe']:+5.2f}  "
            f"maxDD {m['mdd']*100:5.0f}%  trades {m['trades']:3}  expo {m['exposure']*100:3.0f}%")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--coin", default="btc")
    ap.add_argument("--cost-bps", type=float, default=10.0)
    ap.add_argument("--oos", type=float, default=0.35, help="fraction held out as out-of-sample")
    ap.add_argument("--refresh", action="store_true")
    args = ap.parse_args()
    _load_env()
    if not os.getenv("LUNARCRUSH_API_KEY"):
        sys.exit("LUNARCRUSH_API_KEY not set (.env.local).")

    closes = load_closes(args.coin, args.refresh)
    if len(closes) < 400:
        sys.exit(f"Only {len(closes)} closes — too little history.")
    split = int(len(closes) * (1 - args.oos))
    IS, OOS = closes[:split], closes[split - 1:]  # OOS shares the boundary bar for continuity

    print("=" * 92)
    print(f"STRATEGY BACKTEST · {args.coin.upper()} · {len(closes)} daily bars · cost {args.cost_bps}bps/side")
    print(f"in-sample: first {split} bars · out-of-sample: last {len(closes)-split} bars ({args.oos*100:.0f}%)")
    print("=" * 92)
    print("Params are chosen on IN-SAMPLE (best Sharpe), then judged OUT-OF-SAMPLE.\n")

    bh_full = evaluate(closes, [1] * len(closes), 0)
    bh_oos = evaluate(OOS, [1] * len(OOS), 0)
    print("BUY & HOLD (benchmark):")
    print(f"  full   {_fmt(bh_full)}")
    print(f"  OOS    {_fmt(bh_oos)}\n")

    verdicts = []
    for name, (fn, grid) in STRATEGIES.items():
        # pick best params on in-sample by Sharpe
        best = None
        for params in grid:
            m = evaluate(IS, fn(IS, *params), args.cost_bps)
            if best is None or (m["sharpe"] if m["sharpe"] == m["sharpe"] else -9) > best[0]:
                best = (m["sharpe"] if m["sharpe"] == m["sharpe"] else -9, params)
        params = best[1]
        full = evaluate(closes, fn(closes, *params), args.cost_bps)
        oos = evaluate(OOS, fn(OOS, *params), args.cost_bps)
        print(f"{name}  (best IS params {params}):")
        print(f"  full   {_fmt(full)}")
        print(f"  OOS    {_fmt(oos)}")
        beat = (oos["total"] > bh_oos["total"], oos["sharpe"] > bh_oos["sharpe"], oos["mdd"] > bh_oos["mdd"])
        tags = []
        if beat[0]: tags.append("return")
        if beat[1]: tags.append("Sharpe")
        if beat[2]: tags.append("drawdown")
        print(f"  vs B&H OOS: {'beats on ' + ', '.join(tags) if tags else 'beats B&H on nothing'}\n")
        verdicts.append((name, tags, oos))

    print("-" * 92)
    winners = [v for v in verdicts if v[1]]
    beat_ret = [v for v in verdicts if "return" in v[1]]
    if beat_ret:
        print(f"Beat buy-and-hold on TOTAL RETURN out-of-sample: {', '.join(v[0] for v in beat_ret)}")
    else:
        print("NONE beat buy-and-hold on total return out-of-sample.")
    smoother = [v for v in verdicts if "drawdown" in v[1] and "Sharpe" in v[1]]
    if smoother:
        print(f"Gave a better RISK-ADJUSTED ride (higher Sharpe + smaller drawdown): {', '.join(v[0] for v in smoother)}")
    print("Reminder: one asset, ~6.5y, one OOS split. 'Beats on drawdown' usually means it sat")
    print("in cash through crashes — lower return, smoother ride. Beating B&H on RETURN is the hard part.")
    print("=" * 92)


if __name__ == "__main__":
    main()
