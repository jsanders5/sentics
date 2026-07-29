#!/usr/bin/env python3
"""
One-shot monitoring digest for the validation loop. Reports:
  1. Pipeline health   — is the daily run landing? how fresh is the data?
  2. Data accrual      — call_snapshots / social_snapshots growth (the corpus).
  3. Tilt activity     — how much the contrarian social tilt is moving convictions.
  4. Live edge readout — as calls mature, does conviction rank forward returns?
                         (reuses eval_calls.py — the leak-free ledger check.)

Run manually or on a schedule (see --help of your scheduler). Needs SUPABASE_URL
+ SUPABASE_SECRET_KEY (read from .env.local if present).

    python3 api/scripts/monitor.py
"""

import json
import os
import re
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

_HERE = os.path.dirname(os.path.abspath(__file__))


def _load_env():
    p = os.path.join(os.path.dirname(os.path.dirname(_HERE)), ".env.local")
    if os.path.exists(p):
        for line in open(p):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def _open(path, extra=None):
    base = os.environ["SUPABASE_URL"].rstrip("/")
    key = os.environ["SUPABASE_SECRET_KEY"]
    h = {"apikey": key, "Authorization": f"Bearer {key}"}
    req = urllib.request.Request(f"{base}/rest/v1/{path}", headers={**h, **(extra or {})})
    return urllib.request.urlopen(req, timeout=40)


def count(table, query=""):
    q = f"{table}?select=id" + (f"&{query}" if query else "")
    with _open(q, {"Prefer": "count=exact", "Range": "0-0"}) as r:
        cr = r.headers.get("Content-Range", "*/0")
    return int(cr.split("/")[-1]) if "/" in cr else 0


def rows(path):
    with _open(path) as r:
        return json.load(r)


def _iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def _parse(s):
    """Parse a Supabase timestamp → aware UTC datetime (assumes UTC if naive).
    Normalizes fractional seconds to 6 digits (py3.9 fromisoformat is strict)."""
    s = s.replace("Z", "+00:00")
    s = re.sub(r"\.(\d+)", lambda m: "." + (m.group(1) + "000000")[:6], s)
    dt = datetime.fromisoformat(s)
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def ago(iso_str, now):
    try:
        t = _parse(iso_str)
    except Exception:
        return "?"
    h = (now - t).total_seconds() / 3600
    return f"{h:.0f}h ago" if h < 48 else f"{h/24:.1f}d ago"


def main():
    _load_env()
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_SECRET_KEY"):
        sys.exit("SUPABASE_URL / SUPABASE_SECRET_KEY not set (add to .env.local).")
    now = datetime.now(timezone.utc)

    print("=" * 66)
    print(f"SENTICS MONITOR  ·  {_iso(now)}Z")
    print("=" * 66)

    # 1. Pipeline health
    cand = rows("candidates?select=symbol,direction,updated_at,score,social&order=score.desc")
    fresh = max((c.get("updated_at") for c in cand if c.get("updated_at")), default=None)
    directional = [c for c in cand if c.get("direction") in ("Bullish", "Bearish")]
    stale = fresh and (now - _parse(fresh)).total_seconds() > 36 * 3600
    print("\n1) PIPELINE HEALTH")
    print(f"   candidates: {len(cand)} ({len(directional)} directional) · "
          f"data {ago(fresh, now) if fresh else 'n/a'}"
          + ("   ⚠ STALE (>36h — cron may not be running)" if stale else "   ✓"))

    # 2. Data accrual
    cs, ss = count("call_snapshots"), count("social_snapshots")
    m7 = count("call_snapshots", f"captured_at=lt.{_iso(now - timedelta(days=7))}")
    m30 = count("call_snapshots", f"captured_at=lt.{_iso(now - timedelta(days=30))}")
    print("\n2) DATA ACCRUAL (the validation corpus)")
    print(f"   call_snapshots:   {cs:5}   ({m7} matured ≥7d, {m30} matured ≥30d)")
    print(f"   social_snapshots: {ss:5}   (social layer began recently)")

    # 3. Contrarian tilt activity
    tilted = [c for c in cand
              if isinstance((c.get("social") or {}).get("contrarian_adj"), (int, float))
              and c["social"]["contrarian_adj"] != 0]
    print("\n3) CONTRARIAN SOCIAL TILT")
    if tilted:
        adjs = [c["social"]["contrarian_adj"] for c in tilted]
        hot = max(tilted, key=lambda c: c["social"].get("heat_z") or 0)   # most crowded
        cool = min(tilted, key=lambda c: c["social"].get("heat_z") or 0)  # least crowded

        def desc(c):
            s = c["social"]
            return f"{c['symbol']} (heat_z {s.get('heat_z'):+.2f}, {c['direction'][:4]}, conv {s['contrarian_adj']:+.1f})"
        print(f"   tilted {len(tilted)}/{len(directional)} directional coins · "
              f"conviction adj range {min(adjs):+.1f}…{max(adjs):+.1f} pts")
        print(f"   hottest: {desc(hot)}")
        print(f"   coolest: {desc(cool)}")
    else:
        print("   no tilt applied yet (needs a run after the tilt shipped, ≥5 coins with sentiment)")

    # 4. Live edge readout (only meaningful once calls mature)
    print("\n4) LIVE EDGE READOUT (leak-free, from the call ledger)")
    if m7 < 20:
        print(f"   only {m7} calls matured at 7d — too few to read (need ~20+).")
        print("   → check back in ~1 week; 30d readout ~1 month out.")
    else:
        try:
            sys.path.insert(0, _HERE)
            import eval_calls as ec
            snaps = ec.fetch_snapshots()
            for h in (7, 30):
                s = ec.evaluate(snaps, h, 3)
                per_day = [((1 + x["forward_return"]) ** (1 / max(1, x["horizon"])) - 1) * x["sign"] for x in s]
                st = ec._stats(per_day) if s else None
                if st:
                    print(f"   h={h}d: {len(s)} matured · edge {sum(x['edge'] for x in s)/len(s)*100:+.2f}% · "
                          f"strategy t-stat {st['t']:+.2f}")
                else:
                    print(f"   h={h}d: not enough matured yet")
            print("   (run `python3 api/scripts/eval_calls.py` for the full conviction-bucket breakdown)")
        except Exception as e:  # noqa: BLE001
            print(f"   edge readout unavailable ({e}); run eval_calls.py directly.")

    print("\n" + "=" * 66)


if __name__ == "__main__":
    main()
