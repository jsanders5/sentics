"use client";

import { Candidate, Direction, BearishView } from "@/app/types";
import { ScoreRing } from "@/app/components/shared/ScoreRing";
import { DirectionBadge } from "@/app/components/shared/DirectionBadge";
import { ConfidenceBadge } from "@/app/components/shared/ConfidenceBadge";
import { HorizonBadge } from "@/app/components/shared/HorizonBadge";
import { TradePlanCompact } from "@/app/components/trade/TradePlan";
import { MiniCandlestick } from "@/app/components/charts/MiniCandlestick";
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

      {/* Mini candlestick — last ~30 daily candles. Click → full TradingView
          chart (new tab). Stop propagation so it doesn't also open the drawer. */}
      {candidate.ohlc && candidate.ohlc.length > 0 && (
        <a
          href={
            candidate.tv_symbol
              ? `https://www.tradingview.com/chart/?symbol=${encodeURIComponent(candidate.tv_symbol)}`
              : `https://www.tradingview.com/symbols/${encodeURIComponent(candidate.symbol.toUpperCase())}USD/`
          }
          target="_blank"
          rel="noopener noreferrer"
          onClick={(e) => e.stopPropagation()}
          onKeyDown={(e) => e.stopPropagation()}
          title={`Open ${candidate.symbol} chart on TradingView`}
          aria-label={`Open ${candidate.symbol} chart on TradingView`}
          className="group/chart relative mt-3 block rounded-md transition-opacity hover:opacity-90 focus:outline-none focus-visible:ring-2 focus-visible:ring-[--accent]"
        >
          <MiniCandlestick candles={candidate.ohlc} />
          <span
            className="pointer-events-none absolute right-1 top-1 flex items-center gap-0.5 rounded px-1.5 py-0.5 text-[10px] font-medium opacity-0 transition-opacity group-hover/chart:opacity-100"
            style={{ backgroundColor: "var(--bg-raised)", color: "var(--text-secondary)", border: "1px solid var(--border)" }}
          >
            TradingView <span aria-hidden>↗</span>
          </span>
        </a>
      )}

      {/* Badges */}
      <div className="mt-3 flex flex-wrap items-center gap-1.5">
        {candidate.confidence_tier && <ConfidenceBadge tier={candidate.confidence_tier} size="sm" />}
        {candidate.time_horizon && <HorizonBadge horizon={candidate.time_horizon} size="sm" />}
      </div>

      {/* News catalyst — sizes to its text, caps at the card width, wraps if long */}
      {candidate.catalyst && candidate.catalyst !== "none" && (
        <div className="mt-2">
          <span
            className="inline-flex max-w-full items-start gap-1.5 rounded-lg border px-2.5 py-1.5 text-xs font-medium align-top"
            style={{
              backgroundColor: "var(--bg-raised)",
              borderColor: "var(--border)",
              color: typeof candidate.sentiment === "number"
                ? (candidate.sentiment > 0.05 ? "var(--bullish)"
                  : candidate.sentiment < -0.05 ? "var(--bearish)" : "var(--text-secondary)")
                : "var(--text-secondary)",
            }}
            title={`News catalyst: ${candidate.catalyst}`}
          >
            <span aria-hidden>📰</span>
            <span className="min-w-0 break-words">{candidate.catalyst}</span>
          </span>
        </div>
      )}

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
