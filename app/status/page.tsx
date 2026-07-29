"use client";

import { useEffect, useState, useCallback } from "react";
import { ErrorBoundary } from "@/app/components/ErrorBoundary";
import { Header } from "@/app/components/layout/Header";

interface Digest {
  generated_at: string;
  health: { candidates: number; directional: number; fresh?: string; hours_ago?: number; stale?: boolean };
  accrual: { call_snapshots: number; social_snapshots: number; matured_7d: number; matured_30d: number };
  tilt: {
    tilted: number; total_directional: number; adj_min?: number; adj_max?: number;
    hottest?: { symbol: string; direction: string; heat_z: number; adj: number } | null;
    coolest?: { symbol: string; direction: string; heat_z: number; adj: number } | null;
  };
  edge: { horizon: number; matured: number; edge_pct: number | null; t: number | null }[];
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-baseline justify-between gap-4 py-1.5 border-b border-[--border] last:border-0">
      <span className="text-sm text-[--text-secondary]">{label}</span>
      <span className="font-mono text-sm text-[--text-primary] text-right">{children}</span>
    </div>
  );
}

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-lg border p-4" style={{ backgroundColor: "var(--bg-surface)", borderColor: "var(--border)" }}>
      <h3 className="text-xs font-semibold uppercase tracking-wider text-[--text-secondary] mb-2">{title}</h3>
      {children}
    </div>
  );
}

export default function StatusPage() {
  const [token, setToken] = useState("");
  const [input, setInput] = useState("");
  const [digest, setDigest] = useState<Digest | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const saved = typeof window !== "undefined" ? localStorage.getItem("monitor_token") : null;
    if (saved) setToken(saved);
  }, []);

  const load = useCallback(async (tok: string) => {
    if (!tok) return;
    setLoading(true);
    setError(null);
    try {
      const r = await fetch(`/api/monitor?token=${encodeURIComponent(tok)}`);
      if (r.status === 401) { setError("Unauthorized — wrong token."); setDigest(null); return; }
      if (!r.ok) { setError((await r.json().catch(() => ({}))).error || `Error ${r.status}`); return; }
      setDigest(await r.json());
      localStorage.setItem("monitor_token", tok);
    } catch {
      setError("Failed to load.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { if (token) load(token); }, [token, load]);

  const tColor = (t: number | null) =>
    t == null ? "var(--text-muted)" : t > 2 ? "var(--bullish)" : t < -2 ? "var(--bearish)" : "var(--text-secondary)";

  return (
    <ErrorBoundary>
      <div className="flex h-screen flex-col" style={{ backgroundColor: "var(--bg-base)" }}>
        <Header />
        <div className="flex-1 overflow-y-auto">
          <div className="w-full max-w-2xl mx-auto p-4 md:p-6 space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-bold text-[--text-primary]">Status <span className="text-xs font-normal text-[--text-muted]">· admin</span></h2>
              {digest && (
                <button onClick={() => load(token)} className="text-xs rounded border px-2 py-1 text-[--accent]" style={{ borderColor: "var(--border)" }}>
                  Refresh
                </button>
              )}
            </div>

            {!digest && (
              <div className="rounded-lg border p-4 space-y-2" style={{ backgroundColor: "var(--bg-surface)", borderColor: "var(--border)" }}>
                <p className="text-sm text-[--text-secondary]">Enter the monitor token to view the validation digest.</p>
                <div className="flex gap-2">
                  <input
                    type="password" value={input} onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && setToken(input)}
                    placeholder="MONITOR_TOKEN"
                    className="flex-1 rounded border px-2 py-1.5 text-sm font-mono"
                    style={{ backgroundColor: "var(--bg-raised)", borderColor: "var(--border)", color: "var(--text-primary)" }}
                  />
                  <button onClick={() => setToken(input)} className="rounded px-3 py-1.5 text-sm font-semibold text-white" style={{ backgroundColor: "var(--accent)" }}>
                    View
                  </button>
                </div>
                {error && <p className="text-xs" style={{ color: "var(--bearish)" }}>{error}</p>}
              </div>
            )}

            {loading && <p className="text-sm text-[--text-muted]">Loading…</p>}

            {digest && (
              <>
                <Card title="Pipeline health">
                  <Row label="Candidates">{digest.health.candidates} ({digest.health.directional} directional)</Row>
                  <Row label="Data freshness">
                    <span style={{ color: digest.health.stale ? "var(--stale)" : "var(--bullish)" }}>
                      {digest.health.hours_ago != null ? `${digest.health.hours_ago.toFixed(0)}h ago` : "n/a"}
                      {digest.health.stale ? " ⚠ stale" : " ✓"}
                    </span>
                  </Row>
                </Card>

                <Card title="Data accrual (validation corpus)">
                  <Row label="Call snapshots">{digest.accrual.call_snapshots} ({digest.accrual.matured_7d} ≥7d, {digest.accrual.matured_30d} ≥30d)</Row>
                  <Row label="Social snapshots">{digest.accrual.social_snapshots}</Row>
                </Card>

                <Card title="Contrarian social tilt">
                  {digest.tilt.tilted > 0 ? (
                    <>
                      <Row label="Tilted coins">{digest.tilt.tilted}/{digest.tilt.total_directional} · adj {digest.tilt.adj_min?.toFixed(1)}…{digest.tilt.adj_max?.toFixed(1)} pts</Row>
                      {digest.tilt.hottest && <Row label="Hottest">{digest.tilt.hottest.symbol} (z {digest.tilt.hottest.heat_z?.toFixed(2)}, {digest.tilt.hottest.direction.slice(0,4)}, conv {digest.tilt.hottest.adj > 0 ? "+" : ""}{digest.tilt.hottest.adj})</Row>}
                      {digest.tilt.coolest && <Row label="Coolest">{digest.tilt.coolest.symbol} (z {digest.tilt.coolest.heat_z?.toFixed(2)}, conv {digest.tilt.coolest.adj > 0 ? "+" : ""}{digest.tilt.coolest.adj})</Row>}
                    </>
                  ) : <p className="text-sm text-[--text-muted]">No tilt applied yet.</p>}
                </Card>

                <Card title="Live edge readout (leak-free)">
                  {digest.edge.map((e) => (
                    <Row key={e.horizon} label={`h=${e.horizon}d`}>
                      {e.matured} matured{" "}
                      {e.edge_pct != null ? (
                        <>· edge {e.edge_pct > 0 ? "+" : ""}{e.edge_pct.toFixed(2)}% · <span style={{ color: tColor(e.t) }}>t {e.t! > 0 ? "+" : ""}{e.t!.toFixed(2)}</span></>
                      ) : "· too few"}
                    </Row>
                  ))}
                  <p className="text-xs italic text-[--text-muted] mt-2">
                    Directional edge of the calls, from the ledger. Negative = anti-predictive. The
                    contrarian tilt needs weeks of matured social calls before it shows here.
                  </p>
                </Card>

                <p className="text-[11px] text-[--text-muted]">Generated {new Date(digest.generated_at).toLocaleString()}</p>
              </>
            )}
          </div>
        </div>
      </div>
    </ErrorBoundary>
  );
}
