"use client";

import { TradePlan, BearishView } from "@/app/types";
import { formatPrice } from "@/app/lib/format";

function rrColor(rr?: number | null): string {
  if (!rr) return "var(--text-muted)";
  if (rr >= 2) return "var(--bullish)";
  if (rr >= 1) return "var(--medium)";
  return "var(--text-muted)";
}

function RiskReward({ rr }: { rr?: number | null }) {
  if (!rr || rr <= 0) return null;
  return (
    <span
      className="inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-semibold"
      style={{ color: rrColor(rr), borderColor: "var(--border)", backgroundColor: "var(--bg-raised)" }}
      title="Reward-to-risk ratio (target distance ÷ stop distance)"
    >
      R/R {rr.toFixed(1)}
    </span>
  );
}

/** Compact one-line plan for cards. */
export function TradePlanCompact({ plan, view }: { plan?: TradePlan; view: BearishView }) {
  if (!plan || plan.bias === "none") {
    return <span className="text-xs text-[--text-muted]">No setup — wait for a signal</span>;
  }

  const isSpotExit = plan.bias === "short" && view === "spot";
  const arrow = plan.bias === "short" ? "↓" : "↑";

  if (isSpotExit) {
    return (
      <div className="flex items-center justify-between gap-2 text-xs">
        <span className="text-[--bearish] font-semibold">Exit / avoid</span>
        <span className="text-[--text-muted] font-mono">↓ {formatPrice(plan.target)}</span>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-between gap-2 text-xs">
      <span className="font-mono text-[--text-secondary]">
        {formatPrice(plan.entry)} <span className="text-[--text-muted]">{arrow}</span>{" "}
        <span className="text-[--text-primary]">{formatPrice(plan.target)}</span>
      </span>
      <RiskReward rr={plan.risk_reward} />
    </div>
  );
}

function PlanRow({
  label,
  price,
  condition,
  color,
}: {
  label: string;
  price?: number;
  condition?: string;
  color?: string;
}) {
  return (
    <div className="space-y-0.5">
      <div className="flex items-center justify-between gap-3">
        <span className="text-xs uppercase tracking-wider text-[--text-muted]">{label}</span>
        <span className="font-mono text-sm font-semibold" style={{ color: color || "var(--text-primary)" }}>
          {formatPrice(price)}
        </span>
      </div>
      {condition && <p className="text-xs text-[--text-secondary] leading-snug">{condition}</p>}
    </div>
  );
}

/** Full plan for the detail drawer. */
export function TradePlanDetail({ plan, view }: { plan?: TradePlan; view: BearishView }) {
  if (!plan) return null;

  if (plan.bias === "none") {
    return (
      <div className="space-y-2 border-t border-[--border] pt-6">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-[--text-secondary]">Trade Plan</h3>
        <p className="text-sm text-[--text-secondary]">{plan.summary}</p>
      </div>
    );
  }

  const isShort = plan.bias === "short";
  const isSpotExit = isShort && view === "spot";

  const title = isSpotExit
    ? "Bearish · Exit / Avoid"
    : isShort
    ? "Trade Plan · Short"
    : "Trade Plan · Long";

  const entryLabel = isSpotExit ? "Bearish trigger" : "Entry";
  const targetLabel = isSpotExit ? "Downside target" : isShort ? "Cover target" : "Target";
  const stopLabel = isSpotExit ? "Invalidated above" : "Stop";

  return (
    <div className="space-y-3 border-t border-[--border] pt-6">
      <div className="flex items-center justify-between gap-3">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-[--text-secondary]">{title}</h3>
        <RiskReward rr={plan.risk_reward} />
      </div>

      <div className="space-y-3 rounded-xl border border-[--border] p-4" style={{ backgroundColor: "var(--bg-raised)" }}>
        <PlanRow label={entryLabel} price={plan.entry} condition={plan.entry_condition} />
        <div className="border-t border-[--border]" />
        <PlanRow
          label={targetLabel}
          price={plan.target}
          condition={plan.target_condition}
          color="var(--bullish)"
        />
        <div className="border-t border-[--border]" />
        <PlanRow label={stopLabel} price={plan.stop} condition={plan.stop_condition} color="var(--bearish)" />
      </div>

      {isSpotExit && (
        <p className="text-xs text-[--text-muted] italic">
          Spot view: shown as risk levels to watch, not a short-trade recommendation.
        </p>
      )}
      <p className="text-xs text-[--text-muted] italic">
        Educational only — not financial advice. Levels are derived from technical indicators and can fail.
      </p>
    </div>
  );
}
