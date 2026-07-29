import { NextApiRequest, NextApiResponse } from "next";

/**
 * GET /api/monitor?token=<MONITOR_TOKEN>
 *
 * Admin-only validation digest (pipeline health, data accrual, contrarian-tilt
 * activity, live edge readout from the call ledger). Backs the /status page and
 * the scheduled monitoring agent. Gated by the MONITOR_TOKEN env var — exposes
 * internal metrics, so it must not be public.
 */
const REST = () => (process.env.SUPABASE_URL || "").replace(/\/$/, "") + "/rest/v1";
const H = () => {
  const k = process.env.SUPABASE_SECRET_KEY || "";
  return { apikey: k, Authorization: `Bearer ${k}` };
};

async function count(table: string, query = ""): Promise<number> {
  const q = `${table}?select=id${query ? "&" + query : ""}`;
  const r = await fetch(`${REST()}/${q}`, { headers: { ...H(), Prefer: "count=exact", Range: "0-0" } });
  const cr = r.headers.get("content-range") || "*/0";
  const n = cr.split("/").pop();
  return n && n !== "*" ? parseInt(n, 10) : 0;
}

async function rows(path: string): Promise<Record<string, unknown>[]> {
  const r = await fetch(`${REST()}/${path}`, { headers: H() });
  return r.ok ? r.json() : [];
}

const ts = (s: string) => new Date(s.replace(" ", "T")).getTime();

// Leak-free edge readout: join each call to the same coin's later snapshot ~horizon
// days out (mirrors eval_calls.evaluate).
function edge(snaps: Record<string, unknown>[], hDays: number, tolDays = 3) {
  const bySym: Record<string, Record<string, unknown>[]> = {};
  for (const r of snaps) {
    const d = r.direction;
    if (!r.price || (d !== "Bullish" && d !== "Bearish")) continue;
    (bySym[r.symbol as string] ||= []).push(r);
  }
  const edges: number[] = [];
  for (const sym in bySym) {
    const s = bySym[sym].sort((a, b) => ts(a.captured_at as string) - ts(b.captured_at as string));
    for (let i = 0; i < s.length; i++) {
      const want = ts(s[i].captured_at as string) + hDays * 86400000;
      const realized = s.slice(i + 1).find((x) => {
        const t = ts(x.captured_at as string);
        return t >= want && t <= want + tolDays * 86400000;
      });
      if (!realized || !realized.price) continue;
      const fwd = ((realized.price as number) - (s[i].price as number)) / (s[i].price as number);
      const sign = s[i].direction === "Bullish" ? 1 : -1;
      edges.push(fwd * sign);
    }
  }
  const n = edges.length;
  if (n < 2) return { horizon: hDays, matured: n, edge_pct: null, t: null };
  const mean = edges.reduce((a, b) => a + b, 0) / n;
  const sd = Math.sqrt(edges.reduce((a, b) => a + (b - mean) ** 2, 0) / n);
  return { horizon: hDays, matured: n, edge_pct: mean * 100, t: sd ? mean / (sd / Math.sqrt(n)) : null };
}

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const expected = process.env.MONITOR_TOKEN;
  if (!expected) return res.status(500).json({ error: "MONITOR_TOKEN not configured" });
  const token = req.query.token || req.headers["x-monitor-token"];
  if (token !== expected) return res.status(401).json({ error: "unauthorized" });
  if (!process.env.SUPABASE_URL || !process.env.SUPABASE_SECRET_KEY) {
    return res.status(500).json({ error: "Supabase not configured" });
  }

  try {
    const now = Date.now();
    const iso = (ms: number) => new Date(ms).toISOString().slice(0, 19);
    const cand = await rows(
      "candidates?select=symbol,direction,updated_at,score,social&order=score.desc"
    );
    const directional = cand.filter((c) => c.direction === "Bullish" || c.direction === "Bearish");
    const fresh = cand
      .map((c) => c.updated_at as string)
      .filter(Boolean)
      .sort()
      .pop();
    const hoursAgo = fresh ? (now - ts(fresh)) / 3.6e6 : null;

    const [cs, ss, m7, m30] = await Promise.all([
      count("call_snapshots"),
      count("social_snapshots"),
      count("call_snapshots", `captured_at=lt.${iso(now - 7 * 864e5)}`),
      count("call_snapshots", `captured_at=lt.${iso(now - 30 * 864e5)}`),
    ]);

    const tilted = directional.filter((c) => {
      const s = c.social as Record<string, unknown> | undefined;
      return s && typeof s.contrarian_adj === "number" && s.contrarian_adj !== 0;
    });
    const heatOf = (c: Record<string, unknown>) => ((c.social as Record<string, number>).heat_z as number) || 0;
    const tiltPick = (c?: Record<string, unknown>) => {
      if (!c) return null;
      const s = c.social as Record<string, number>;
      return { symbol: c.symbol, direction: c.direction, heat_z: s.heat_z, adj: s.contrarian_adj };
    };
    const sortedByHeat = [...tilted].sort((a, b) => heatOf(a) - heatOf(b));

    const snaps = await rows(
      "call_snapshots?select=captured_at,symbol,direction,price&order=symbol.asc,captured_at.asc&limit=100000"
    );

    return res.status(200).json({
      generated_at: new Date(now).toISOString(),
      health: {
        candidates: cand.length,
        directional: directional.length,
        fresh,
        hours_ago: hoursAgo,
        stale: hoursAgo != null && hoursAgo > 36,
      },
      accrual: { call_snapshots: cs, social_snapshots: ss, matured_7d: m7, matured_30d: m30 },
      tilt: {
        tilted: tilted.length,
        total_directional: directional.length,
        adj_min: tilted.length ? Math.min(...tilted.map((c) => (c.social as Record<string, number>).contrarian_adj)) : null,
        adj_max: tilted.length ? Math.max(...tilted.map((c) => (c.social as Record<string, number>).contrarian_adj)) : null,
        hottest: tiltPick(sortedByHeat[sortedByHeat.length - 1]),
        coolest: tiltPick(sortedByHeat[0]),
      },
      edge: [edge(snaps, 7), edge(snaps, 30)],
    });
  } catch (e) {
    console.error("[monitor]", e);
    return res.status(500).json({ error: "digest failed" });
  }
}
