"use client";

import { Candidate, BearishView } from "@/app/types";
import { useEffect, useRef } from "react";
import { ConfidenceBadge } from "@/app/components/shared/ConfidenceBadge";
import { HorizonBadge } from "@/app/components/shared/HorizonBadge";
import { DirectionBadge } from "@/app/components/shared/DirectionBadge";
import { ScoreRing } from "@/app/components/shared/ScoreRing";
import { TradePlanDetail } from "@/app/components/trade/TradePlan";

// Assets widely treated as commodities (not securities) — others get an extra
// regulatory-status caveat since their classification is unsettled.
const CLEAR_COMMODITY = new Set(["BTC", "ETH"]);

interface CandidateDetailDrawerProps {
  candidate: Candidate | null;
  isOpen: boolean;
  bearishView: BearishView;
  onClose: () => void;
}

export function CandidateDetailDrawer({
  candidate,
  isOpen,
  bearishView,
  onClose,
}: CandidateDetailDrawerProps) {
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (isOpen && closeButtonRef.current) {
      closeButtonRef.current.focus();
    }

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) onClose();
    };

    if (isOpen) {
      document.addEventListener("keydown", handleEscape);
      document.body.style.overflow = "hidden";
    }

    return () => {
      document.removeEventListener("keydown", handleEscape);
      document.body.style.overflow = "";
    };
  }, [isOpen, onClose]);

  if (!candidate) return null;

  const directionBg =
    candidate.direction === "Bullish"
      ? "var(--bullish-bg)"
      : candidate.direction === "Bearish"
      ? "var(--bearish-bg)"
      : "var(--neutral-dir-bg)";

  const directionBorder =
    candidate.direction === "Bullish"
      ? "var(--bullish-border)"
      : candidate.direction === "Bearish"
      ? "var(--bearish-border)"
      : "var(--neutral-dir-border)";

  return (
    <>
      {isOpen && (
        <div
          className="fixed inset-0 z-40 transition-opacity"
          style={{ backgroundColor: 'rgba(0,0,0,0.55)', backdropFilter: 'blur(4px)', WebkitBackdropFilter: 'blur(4px)' }}
          onClick={onClose}
        />
      )}

      <div
        className={`fixed inset-y-0 right-0 z-50 w-full md:w-[480px] lg:w-[540px] overflow-y-auto transition-transform duration-300 md:border-l ${
          isOpen ? "translate-x-0" : "translate-x-full"
        }`}
        style={{ backgroundColor: 'var(--bg-surface)', borderLeftColor: 'var(--border)' }}
      >
        <div className="space-y-6 p-6">
          {/* Header */}
          <div className="flex items-start justify-between gap-4">
            <div>
              <h2 className="font-mono text-2xl font-bold text-[--text-primary]">
                {candidate.symbol}
              </h2>
              <p className="text-sm text-[--text-secondary] mt-0.5">{candidate.name}</p>
            </div>
            <button
              ref={closeButtonRef}
              onClick={onClose}
              className="flex h-8 w-8 items-center justify-center rounded hover:bg-[--bg-raised] text-[--text-secondary] hover:text-[--text-primary] transition-colors flex-shrink-0"
              aria-label="Close detail panel"
            >
              ×
            </button>
          </div>

          {/* Direction Hero */}
          {candidate.direction && (
            <div
              className="rounded-xl p-4 border"
              style={{ backgroundColor: directionBg, borderColor: directionBorder }}
            >
              <p className="text-xs font-semibold uppercase tracking-wider text-[--text-muted] mb-2">
                Price Direction
              </p>
              <DirectionBadge direction={candidate.direction} size="lg" />
              <p className="text-sm text-[--text-secondary] mt-3">
                <span className="font-semibold text-[--text-primary]">
                  {Math.round(candidate.candidate_score)}/100
                </span>{" "}
                conviction in this {candidate.direction.toLowerCase()} reading
              </p>
            </div>
          )}

          {/* Horizon + Confidence + Conviction */}
          <div className="flex items-center justify-between gap-4">
            <div className="flex flex-wrap gap-2">
              {candidate.time_horizon && <HorizonBadge horizon={candidate.time_horizon} />}
              {candidate.confidence_tier && <ConfidenceBadge tier={candidate.confidence_tier} />}
            </div>
            <ScoreRing score={candidate.candidate_score} size={64} label="Conviction" />
          </div>
          <p className="text-xs text-[--text-muted] -mt-2">
            <span className="font-semibold text-[--text-secondary]">Conviction</span> — signal strength of the
            predicted direction. <span className="font-semibold text-[--text-secondary]">Confidence</span> — how
            many indicators agree.
          </p>

          {/* Trade Plan */}
          <TradePlanDetail plan={candidate.trade_plan} view={bearishView} />

          {/* Rationale */}
          {candidate.rationale && (
            <div className="space-y-2 border-t border-[--border] pt-6">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-[--text-secondary]">
                AI Analysis
              </h3>
              <p className="text-sm leading-relaxed text-[--text-primary]">
                {candidate.rationale}
              </p>
              <p className="text-xs text-[--text-muted] italic">
                Not investment advice. AI-generated analysis may contain inaccuracies.
              </p>
            </div>
          )}

          {/* Catalyst / News (fundamental analysis) */}
          {candidate.catalyst && candidate.catalyst !== "none" && candidate.fa_summary && (
            <div className="space-y-2 border-t border-[--border] pt-6">
              <div className="flex items-center justify-between gap-3">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-[--text-secondary]">
                  Catalyst / News
                </h3>
                {typeof candidate.sentiment === "number" && (
                  <span
                    className="text-xs font-semibold font-mono"
                    style={{
                      color: candidate.sentiment > 0.05 ? "var(--bullish)"
                        : candidate.sentiment < -0.05 ? "var(--bearish)" : "var(--text-muted)",
                    }}
                    title="News sentiment (−1 bearish … +1 bullish)"
                  >
                    {candidate.sentiment > 0 ? "+" : ""}{candidate.sentiment.toFixed(2)}
                  </span>
                )}
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <span
                  className="inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold"
                  style={{ backgroundColor: "var(--bg-raised)", borderColor: "var(--border)", color: "var(--text-secondary)" }}
                >
                  {candidate.catalyst}
                </span>
                {candidate.fa_confidence && <ConfidenceBadge tier={candidate.fa_confidence} size="sm" />}
              </div>
              <p className="text-sm leading-relaxed text-[--text-primary]">{candidate.fa_summary}</p>
              {candidate.fa_sources && candidate.fa_sources.length > 0 && (
                <div className="space-y-1 pt-1">
                  {candidate.fa_sources.slice(0, 3).map((s, i) => (
                    <a
                      key={i}
                      href={s.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block truncate text-xs text-[--accent] hover:underline"
                      onClick={(e) => e.stopPropagation()}
                    >
                      ↗ {s.title || s.url}
                    </a>
                  ))}
                </div>
              )}
              <p className="text-xs text-[--text-muted] italic">
                News-based signal; complements the technical read. Not investment advice.
              </p>
            </div>
          )}

          {/* Scanned, but no notable catalyst (directional coins only — Neutral
              coins aren't scanned, so they show nothing here). */}
          {(!candidate.catalyst || candidate.catalyst === "none") &&
            typeof candidate.fa_score === "number" && (
              <div className="space-y-2 border-t border-[--border] pt-6">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-[--text-secondary]">
                  Catalyst / News
                </h3>
                <p className="text-sm text-[--text-muted] italic">
                  No major news catalyst found in recent headlines.
                </p>
              </div>
            )}

          {/* Technical Signals */}
          <div className="space-y-3 border-t border-[--border] pt-6">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-[--text-secondary]">
              Technical Signals
            </h3>
            <div className="space-y-2 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-[--text-secondary]">RSI (14d)</span>
                <span className="font-mono font-semibold text-[--text-primary]">
                  {candidate.rsi.toFixed(1)}
                </span>
              </div>
              <div className="h-1 w-full rounded-full bg-[--bg-raised]">
                <div
                  className="h-full rounded-full bg-[--medium]"
                  style={{ width: `${Math.min(candidate.rsi, 100)}%` }}
                />
              </div>

              <div className="flex items-center justify-between pt-2">
                <span className="text-[--text-secondary]">Volume Ratio</span>
                <span className="font-mono font-semibold text-[--text-primary]">
                  {candidate.volume_ratio.toFixed(2)}×
                </span>
              </div>

              <div className="flex items-center justify-between pt-2">
                <span className="text-[--text-secondary]" title="Direction-agnostic setup strength: how clean and well-confirmed the move is, bull or bear.">Technical Strength</span>
                <span className="font-mono font-semibold text-[--text-primary]">
                  {candidate.technical_score.toFixed(1)}/58
                </span>
              </div>
            </div>
          </div>

          {/* Key Signals */}
          {candidate.key_signals && candidate.key_signals.length > 0 && (
            <div className="space-y-2 border-t border-[--border] pt-6">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-[--text-secondary]">
                Key Signals
              </h3>
              <div className="space-y-1">
                {candidate.key_signals.map((signal, i) => (
                  <div key={i} className="flex items-start gap-2 text-sm text-[--text-primary]">
                    <span
                      className="mt-0.5"
                      style={{
                        color: candidate.direction === "Bullish"
                          ? 'var(--bullish)'
                          : candidate.direction === "Bearish"
                          ? 'var(--bearish)'
                          : 'var(--accent)'
                      }}
                    >
                      •
                    </span>
                    <span>{signal}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Price & Market Cap */}
          <div className="space-y-3 border-t border-[--border] pt-6">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-[--text-secondary]">Price</h3>
              <span className="font-mono text-lg font-semibold text-[--text-primary]">
                {candidate.price && typeof candidate.price === 'number' && candidate.price > 0
                  ? `$${candidate.price.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
                  : 'N/A'}
              </span>
            </div>
            {candidate.market_cap && candidate.market_cap > 0 && (
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-[--text-secondary]">Market Cap</h3>
                <span className="font-mono text-sm font-semibold text-[--text-secondary]">
                  ${(candidate.market_cap / 1e9).toLocaleString('en-US', { maximumFractionDigits: 2 })}B
                </span>
              </div>
            )}
          </div>

          {/* Disclaimer */}
          <div className="border-t border-[--border] pt-6 text-xs text-[--text-muted] space-y-2">
            <p className="italic">
              This analysis is for educational purposes only and should not be construed as
              investment advice. Sentics is not a registered investment adviser or broker-dealer.
              Always conduct your own research before making any decisions.
            </p>
            {!CLEAR_COMMODITY.has(candidate.symbol) && (
              <p className="italic">
                The legal classification of {candidate.symbol} is unsettled and it may be deemed a
                security by regulators or courts, which can affect its availability, value, and
                legality in your jurisdiction.
              </p>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
