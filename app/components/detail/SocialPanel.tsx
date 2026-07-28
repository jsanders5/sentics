"use client";

import { useEffect, useState } from "react";
import { Social, SocialEvidence, SocialItem } from "@/app/types";
import { tip } from "@/app/lib/metrics";

// LunarCrush aggregate sentiment is 0–100 (≈50 neutral).
function sentColor(v?: number): string {
  if (typeof v !== "number") return "var(--text-muted)";
  return v >= 60 ? "var(--bullish)" : v <= 40 ? "var(--bearish)" : "var(--text-secondary)";
}
// Per-post sentiment is a 1–5 scale (3 ≈ neutral).
function postColor(v?: number | string): string {
  const n = typeof v === "string" ? parseFloat(v) : v;
  if (typeof n !== "number" || Number.isNaN(n)) return "var(--text-muted)";
  return n > 3 ? "var(--bullish)" : n < 3 ? "var(--bearish)" : "var(--text-muted)";
}
function fmtNum(n?: number): string {
  if (typeof n !== "number") return "—";
  if (n >= 1e6) return `${(n / 1e6).toFixed(1)}M`;
  if (n >= 1e3) return `${(n / 1e3).toFixed(1)}K`;
  return `${n}`;
}

function Metric({ label, value, delta, color, title }: { label: string; value: string; delta?: number; color?: string; title?: string }) {
  return (
    <div className="flex flex-col cursor-help" title={title}>
      <span className="text-[10px] uppercase tracking-wider text-[--text-muted]">{label}</span>
      <span className="font-mono text-sm font-semibold" style={{ color: color || "var(--text-primary)" }}>
        {value}
        {typeof delta === "number" && delta !== 0 && (
          <span className="ml-1 text-[10px]" style={{ color: delta > 0 ? "var(--bullish)" : "var(--bearish)" }}>
            {delta > 0 ? "▲" : "▼"}{Math.abs(delta) < 1 ? delta.toFixed(1) : Math.round(Math.abs(delta))}
          </span>
        )}
      </span>
    </div>
  );
}

function ItemList({ title, items }: { title: string; items?: SocialItem[] }) {
  if (!items || items.length === 0) return null;
  return (
    <div className="space-y-1.5">
      <p className="text-[10px] font-semibold uppercase tracking-wider text-[--text-muted]">{title}</p>
      {items.map((it, i) => (
        <a
          key={i}
          href={it.link}
          target="_blank"
          rel="noopener noreferrer"
          onClick={(e) => e.stopPropagation()}
          className="flex items-start gap-2 text-xs hover:underline"
          style={{ color: "var(--text-primary)" }}
        >
          <span className="cursor-help" title={tip("post_sentiment")} style={{ color: postColor(it.sentiment) }}>●</span>
          <span className="min-w-0">
            <span className="line-clamp-2">{it.title || it.link}</span>
            {it.creator && <span className="text-[--text-muted]"> — {it.creator}</span>}
          </span>
        </a>
      ))}
    </div>
  );
}

export function SocialPanel({ social, symbol }: { social?: Social; symbol: string }) {
  const [evidence, setEvidence] = useState<SocialEvidence | null>(null);
  const [loading, setLoading] = useState(false);

  const topic = social?.topic;
  useEffect(() => {
    if (!topic) return;
    let cancelled = false;
    setLoading(true);
    setEvidence(null);
    fetch(`/api/social-detail?topic=${encodeURIComponent(topic)}`)
      .then((r) => r.json())
      .then((d) => { if (!cancelled) setEvidence(d); })
      .catch(() => { if (!cancelled) setEvidence({}); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [topic]);

  if (!social) return null;

  const platforms = evidence?.types_sentiment
    ? Object.entries(evidence.types_sentiment).sort((a, b) => b[1] - a[1])
    : [];

  return (
    <div className="space-y-3 border-t border-[--border] pt-6">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-[--text-secondary]">
          Social &amp; Sentiment
        </h3>
        <span className="text-[10px] text-[--text-muted]">LunarCrush</span>
      </div>

      {/* Summary metrics */}
      <div className="grid grid-cols-3 gap-3">
        <Metric label="Sentiment" value={typeof social.sentiment === "number" ? `${Math.round(social.sentiment)}` : "—"} color={sentColor(social.sentiment)} title={tip("sentiment")} />
        <Metric label="Galaxy" value={typeof social.galaxy_score === "number" ? `${social.galaxy_score}` : "—"} delta={social.galaxy_delta} title={tip("galaxy_score")} />
        <Metric label="AltRank" value={typeof social.alt_rank === "number" ? `#${Math.round(social.alt_rank)}` : "—"} delta={social.alt_rank_delta} title={tip("alt_rank")} />
        <Metric label="Soc. Dom." value={typeof social.social_dominance === "number" ? `${social.social_dominance.toFixed(1)}%` : "—"} title={tip("social_dominance")} />
        <Metric label="Soc. Vol." value={fmtNum(social.social_volume_24h)} title={tip("social_volume_24h")} />
        <Metric label="Interactions" value={fmtNum(social.interactions_24h)} title={tip("interactions_24h")} />
      </div>

      {/* Platform breakdown (the "why") */}
      {platforms.length > 0 && (
        <div className="space-y-1 pt-1">
          <p className="text-[10px] font-semibold uppercase tracking-wider text-[--text-muted] cursor-help" title={tip("platform_sentiment")}>
            Sentiment by platform{evidence?.trend ? ` · trend ${evidence.trend}` : ""}
          </p>
          {platforms.map(([name, val]) => (
            <div key={name} className="flex items-center gap-2 text-xs">
              <span className="w-20 shrink-0 text-[--text-muted] capitalize">{name.replace("-", " ")}</span>
              <div className="h-1.5 flex-1 rounded-full" style={{ backgroundColor: "var(--bg-raised)" }}>
                <div className="h-full rounded-full" style={{ width: `${Math.min(100, val)}%`, backgroundColor: sentColor(val) }} />
              </div>
              <span className="w-7 text-right font-mono" style={{ color: sentColor(val) }}>{val}</span>
            </div>
          ))}
        </div>
      )}

      {loading && <p className="text-xs italic text-[--text-muted]">Loading posts & news…</p>}
      <ItemList title="Top news" items={evidence?.news} />
      <ItemList title="Top posts" items={evidence?.posts} />

      <p className="text-xs text-[--text-muted] italic">
        Social data is descriptive context, not a signal to trade. Sentiment can be noisy, lagging, and gamed.
      </p>
    </div>
  );
}
