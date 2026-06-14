"use client";

import { Candidate, Direction, BearishView } from "@/app/types";
import { ScoreRing } from "@/app/components/shared/ScoreRing";
import { DirectionBadge } from "@/app/components/shared/DirectionBadge";
import { ConfidenceBadge } from "@/app/components/shared/ConfidenceBadge";
import { HorizonBadge } from "@/app/components/shared/HorizonBadge";
import { TradePlanCompact } from "@/app/components/trade/TradePlan";
import { formatPrice } from "@/app/lib/format";

interface CandidateCardProps {
  candidate: Candidate;
  index: number;
  bearishView: BearishView;
  onSelect: () => void;
}

const accentByDirection: Record<Direction, { bar: string; glow: string }> = {
  Bullish: { bar: "var(--bullish)", glow: "var(--shadow-glow-bull)" },
  Bearish: { bar: "var(--bearish)", glow: "var(--shadow-glow-bear)" },
  Neutral: { bar: "var(--neutral-dir)", glow: "var(--shadow-card)" },
};

export function CandidateCard({ candidate, index, bearishView, onSelect }: CandidateCardProps) {
  const direction: Direction = candidate.direction ?? "Neutral";
  const accent = accentByDirection[direction];

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onSelect();
    }
  };

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={onSelect}
      onKeyDown={handleKeyDown}
      aria-label={`${candidate.name} (${candidate.symbol}), ${direction}, score ${candidate.candidate_score.toFixed(0)}. View details.`}
      className="card card-interactive animate-card-in relative overflow-hidden"
      style={{ animationDelay: `${Math.min(index * 35, 420)}ms` }}
    >
      {/* Direction accent bar */}
      <div className="absolute inset-x-0 top-0 h-1" style={{ backgroundColor: accent.bar }} />

      <div className="flex items-start justify-between gap-3 pt-1">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-mono text-lg font-bold text-[--text-primary]">{candidate.symbol}</span>
            <DirectionBadge direction={direction} size="sm" />
          </div>
          <p className="truncate text-sm text-[--text-secondary] mt-0.5">{candidate.name}</p>
        </div>
        <ScoreRing
          score={candidate.candidate_score}
          label="Conviction"
          title="Conviction — signal strength of the predicted direction (0–100). Higher means the technical signals agree more strongly on the move, up or down."
        />
      </div>

      {/* Price */}
      <div className="mt-4 font-mono text-2xl font-semibold text-[--text-primary]">
        {formatPrice(candidate.price)}
      </div>

      {/* Badges */}
      <div className="mt-3 flex flex-wrap gap-1.5">
        {candidate.confidence_tier && <ConfidenceBadge tier={candidate.confidence_tier} size="sm" />}
        {candidate.time_horizon && <HorizonBadge horizon={candidate.time_horizon} size="sm" />}
      </div>

      {/* Trade plan summary */}
      <div className="mt-3 border-t border-[--border] pt-3">
        <TradePlanCompact plan={candidate.trade_plan} view={bearishView} />
      </div>

      {/* Metrics footer */}
      <div className="mt-3 flex items-center gap-4 border-t border-[--border] pt-3 text-xs">
        <div className="flex flex-col">
          <span className="text-[--text-muted]">RSI</span>
          <span className="font-mono font-semibold text-[--text-primary]">{candidate.rsi.toFixed(0)}</span>
        </div>
        <div className="flex flex-col">
          <span className="text-[--text-muted]">Vol</span>
          <span className="font-mono font-semibold text-[--text-primary]">{candidate.volume_ratio.toFixed(2)}×</span>
        </div>
        <div className="ml-auto flex items-center gap-1 text-[--text-muted] group-hover:text-[--accent]">
          <span>Details</span>
          <span aria-hidden>→</span>
        </div>
      </div>
    </div>
  );
}
