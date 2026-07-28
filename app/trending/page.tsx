"use client";

import { useEffect, useState } from "react";
import { ErrorBoundary } from "@/app/components/ErrorBoundary";
import { Header } from "@/app/components/layout/Header";
import { formatPrice } from "@/app/lib/format";
import { tip } from "@/app/lib/metrics";

interface TrendingCoin {
  symbol: string;
  name?: string;
  price?: number;
  percent_change_24h?: number;
  alt_rank?: number;
  alt_rank_delta?: number;
  galaxy_score?: number;
  sentiment?: number;
  social_volume_24h?: number;
}

function sentColor(v?: number): string {
  if (typeof v !== "number") return "var(--text-muted)";
  return v >= 60 ? "var(--bullish)" : v <= 40 ? "var(--bearish)" : "var(--text-secondary)";
}
function fmtNum(n?: number): string {
  if (typeof n !== "number") return "—";
  if (n >= 1e6) return `${(n / 1e6).toFixed(1)}M`;
  if (n >= 1e3) return `${(n / 1e3).toFixed(1)}K`;
  return `${n}`;
}

export default function TrendingPage() {
  const [coins, setCoins] = useState<TrendingCoin[]>([]);
  const [loading, setLoading] = useState(true);
  const [unavailable, setUnavailable] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetch("/api/trending")
      .then((r) => r.json())
      .then((d) => {
        if (cancelled) return;
        setCoins(d.coins || []);
        setUnavailable(!!d.unavailable);
      })
      .catch(() => !cancelled && setCoins([]))
      .finally(() => !cancelled && setLoading(false));
    return () => { cancelled = true; };
  }, []);

  return (
    <ErrorBoundary>
      <div className="flex h-screen flex-col" style={{ backgroundColor: "var(--bg-base)" }}>
        <Header />
        <div className="flex flex-1 flex-col overflow-hidden">
          <div className="w-full max-w-5xl mx-auto flex flex-col flex-1 overflow-hidden">
            <div className="px-4 md:px-6 pt-4">
              <h2 className="text-lg font-bold text-[--text-primary]">Trending</h2>
              <p className="text-xs leading-snug mt-1" style={{ color: "var(--text-muted)" }}>
                Ranked by LunarCrush <span className="font-semibold">AltRank</span> (social + price momentum).
                This is a <span className="font-semibold">discovery list, not the screener</span> — these coins
                are often small, highly volatile, and prone to manipulation. Not trade signals or advice.
              </p>
            </div>

            <div className="flex-1 overflow-y-auto p-4 md:p-6">
              {loading ? (
                <div className="space-y-2">
                  {Array.from({ length: 10 }).map((_, i) => (
                    <div key={i} className="card h-14 animate-pulse" style={{ opacity: 0.6 }} />
                  ))}
                </div>
              ) : unavailable ? (
                <p className="text-sm text-[--text-muted]">Social data unavailable (LunarCrush key not configured).</p>
              ) : coins.length === 0 ? (
                <p className="text-sm text-[--text-muted]">No trending coins right now.</p>
              ) : (
                <div className="space-y-1.5">
                  {/* header row */}
                  <div className="hidden sm:grid grid-cols-[2.5rem_1fr_6rem_5rem_5rem_5rem] gap-3 px-3 text-[10px] uppercase tracking-wider text-[--text-muted]">
                    <span className="cursor-help" title={tip("alt_rank")}>#</span>
                    <span>Asset</span>
                    <span className="text-right cursor-help" title={tip("price")}>Price</span>
                    <span className="text-right">24h</span>
                    <span className="text-right cursor-help" title={tip("galaxy_score")}>Galaxy</span>
                    <span className="text-right cursor-help" title={tip("sentiment")}>Sent.</span>
                  </div>
                  {coins.map((c, i) => (
                    <a
                      key={c.symbol}
                      href={`https://www.tradingview.com/symbols/${encodeURIComponent(c.symbol)}USD/`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="card card-interactive grid grid-cols-[2.5rem_1fr_6rem_5rem_5rem_5rem] items-center gap-3 !py-2.5"
                      title={`Open ${c.symbol} on TradingView`}
                    >
                      <span className="font-mono text-sm font-semibold text-[--text-muted]">{i + 1}</span>
                      <div className="min-w-0">
                        <span className="font-mono font-bold text-[--text-primary]">{c.symbol}</span>
                        <span className="ml-2 truncate text-xs text-[--text-secondary]">{c.name}</span>
                      </div>
                      <span className="text-right font-mono text-sm text-[--text-primary]">{formatPrice(c.price)}</span>
                      <span
                        className="text-right font-mono text-sm"
                        style={{ color: (c.percent_change_24h || 0) >= 0 ? "var(--bullish)" : "var(--bearish)" }}
                      >
                        {(c.percent_change_24h || 0) >= 0 ? "+" : ""}{(c.percent_change_24h || 0).toFixed(1)}%
                      </span>
                      <span className="text-right font-mono text-sm text-[--text-secondary]">
                        {typeof c.galaxy_score === "number" ? c.galaxy_score : "—"}
                      </span>
                      <span className="text-right font-mono text-sm font-semibold" style={{ color: sentColor(c.sentiment) }}>
                        {typeof c.sentiment === "number" ? Math.round(c.sentiment) : "—"}
                      </span>
                    </a>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </ErrorBoundary>
  );
}
