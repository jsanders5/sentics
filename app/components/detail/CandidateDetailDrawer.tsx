"use client";

import { Candidate } from "@/app/types";
import { useEffect, useRef } from "react";
import { ConfidenceBadge } from "@/app/components/shared/ConfidenceBadge";
import { HorizonBadge } from "@/app/components/shared/HorizonBadge";
import { ScoreDisplay } from "@/app/components/shared/ScoreDisplay";

interface CandidateDetailDrawerProps {
  candidate: Candidate | null;
  isOpen: boolean;
  onClose: () => void;
}

export function CandidateDetailDrawer({
  candidate,
  isOpen,
  onClose,
}: CandidateDetailDrawerProps) {
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (isOpen && closeButtonRef.current) {
      closeButtonRef.current.focus();
    }

    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
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

  return (
    <>
      {/* Backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 transition-opacity"
          onClick={onClose}
        />
      )}

      {/* Drawer */}
      <div
        className={`fixed right-0 top-0 z-50 h-full w-96 overflow-y-auto bg-[--bg-surface] border-l border-[--border] transition-transform duration-300 ${
          isOpen ? "translate-x-0" : "translate-x-full"
        }`}
      >
        <div className="space-y-6 p-6">
          {/* Header */}
          <div className="flex items-start justify-between gap-4">
            <div className="space-y-2 flex-1">
              <div className="flex items-center gap-2">
                <h2 className="font-mono text-2xl font-bold text-[--text-primary]">
                  {candidate.symbol}
                </h2>
              </div>
              <p className="text-sm text-[--text-secondary]">{candidate.name}</p>
              <p className="text-xs text-[--text-muted]">{candidate.category}</p>
            </div>
            <button
              ref={closeButtonRef}
              onClick={onClose}
              className="flex h-8 w-8 items-center justify-center rounded hover:bg-[--bg-raised] text-[--text-secondary] hover:text-[--text-primary] transition-colors"
              aria-label="Close detail panel"
            >
              ×
            </button>
          </div>

          {/* Badges and Score */}
          <div className="space-y-3">
            <div className="flex flex-wrap gap-2">
              {candidate.time_horizon && (
                <HorizonBadge horizon={candidate.time_horizon} />
              )}
              {candidate.confidence_tier && (
                <ConfidenceBadge tier={candidate.confidence_tier} />
              )}
            </div>
            <div>
              <p className="text-xs text-[--text-secondary] mb-1">Overall Score</p>
              <ScoreDisplay score={candidate.candidate_score} />
            </div>
          </div>

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
                  style={{ width: `${Math.min((candidate.rsi / 100) * 100, 100)}%` }}
                />
              </div>

              <div className="flex items-center justify-between pt-2">
                <span className="text-[--text-secondary]">Volume Ratio</span>
                <span className="font-mono font-semibold text-[--text-primary]">
                  {candidate.volume_ratio.toFixed(2)}×
                </span>
              </div>

              <div className="flex items-center justify-between pt-2">
                <span className="text-[--text-secondary]">Technical Score</span>
                <span className="font-mono font-semibold text-[--text-primary]">
                  {candidate.technical_score.toFixed(1)}/58
                </span>
              </div>

              <div className="flex items-center justify-between pt-2">
                <span className="text-[--text-secondary]">Category Momentum</span>
                <span className="font-mono font-semibold text-[--text-primary]">
                  {candidate.category_momentum.toFixed(1)}/100
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
                    <span className="text-[--accent] mt-0.5">•</span>
                    <span>{signal}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Price Info */}
          <div className="space-y-2 border-t border-[--border] pt-6">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-[--text-secondary]">
              Price
            </h3>
            <div className="font-mono text-lg font-semibold text-[--text-primary]">
              ${candidate.price.toFixed(2)}
            </div>
          </div>

          {/* Disclaimer */}
          <div className="border-t border-[--border] pt-6 text-xs text-[--text-muted]">
            <p className="italic">
              This analysis is for educational purposes only and should not be construed as investment
              advice. Always conduct your own research before making any investment decisions.
            </p>
          </div>
        </div>
      </div>
    </>
  );
}
