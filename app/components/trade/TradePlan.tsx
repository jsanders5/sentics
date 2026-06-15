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
  const display = rr > 5 ? "5+" : rr.toFixed(1);
  return (
    <span
      className="inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-semibold"
      style={{ color: rrColor(rr), borderColor: "var(--border)", backgroundColor: "var(--bg-raised)" }}
      title="Reward-to-risk ratio (target distance ÷ stop distance)"
    >
      R/R {display}
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

  return (
    <div className="space-y-1">
      {isSpotExit ? (
        <div className="flex items-center justify-between gap-2 text-xs">
          <span className="text-[--bearish] font-semibold">Exit / avoid</span>
          <span className="text-[--text-muted] font-mono">↓ {formatPrice(plan.target)}</span>
        </div>
      ) : (
        <div className="flex items-center justify-between gap-2 text-xs">
          <span className="font-mono text-[--text-secondary]">
            {formatPrice(plan.entry)} <span className="text-[--text-muted]">{arrow}</span>{" "}
            <span className="text-[--text-primary]">{formatPrice(plan.target)}</span>
          </span>
          <RiskReward rr={plan.risk_reward} />
        </div>
      )}
      <p className="text-[10px] text-[--text-muted] italic">Technical levels, not advice. Can fail.</p>
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
      {isShort && !isSpotExit && (
        <p className="text-xs italic" style={{ color: "var(--bearish)" }}>
          Short selling carries risk of unlimited loss — losses are not capped and can exceed your
          initial capital. Shorting requires borrowing or a margin/derivatives account on a third-party
          venue, with borrow costs, margin calls, funding rates, and forced liquidation. Sentics does
          not offer, custody, or execute any position. These levels are illustrative only.
        </p>
      )}
      <p className="text-xs text-[--text-muted] italic">
        These entry, target, and stop levels are illustrative outputs of an automated technical model —
        not a recommendation, solicitation, or financial advice. Sentics is not a registered investment
        adviser or broker-dealer. Levels are derived from past price data, are not predictions, and
        frequently fail. You are solely responsible for your own trading decisions.
      </p>
    </div>
  );
}
