"use client";

import { Candidate } from "@/app/types";
import { ConfidenceBadge } from "@/app/components/shared/ConfidenceBadge";
import { HorizonBadge } from "@/app/components/shared/HorizonBadge";
import { DirectionBadge } from "@/app/components/shared/DirectionBadge";
import { ScoreDisplay } from "@/app/components/shared/ScoreDisplay";

interface CandidateRowProps {
  candidate: Candidate;
  rank: number;
  onSelect: () => void;
}

function getDirectionBorderColor(direction?: string): string {
  if (direction === "Bullish") return "border-l-[--bullish]";
  if (direction === "Bearish") return "border-l-[--bearish]";
  return "border-l-[--neutral-dir]";
}

export function CandidateRow({ candidate, rank, onSelect }: CandidateRowProps) {
  const borderColor = getDirectionBorderColor(candidate.direction);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTableRowElement>) => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onSelect();
    }
  };

  const ariaLabel = `${candidate.name} (${candidate.symbol})` +
    (candidate.direction ? `, ${candidate.direction}` : "") +
    (candidate.confidence_tier ? `, ${candidate.confidence_tier} confidence` : "") +
    `, score ${candidate.candidate_score.toFixed(1)}. View details.`;

  return (
    <tr
      onClick={onSelect}
      onKeyDown={handleKeyDown}
      tabIndex={0}
      role="button"
      aria-label={ariaLabel}
      className={`cursor-pointer border-b border-[--border] transition-smooth group border-l-4 ${borderColor} bg-[--bg-surface] hover:bg-[--bg-raised] focus:outline-none focus-visible:ring-2 focus-visible:ring-[--accent] focus-visible:ring-inset`}
    >
      <td className="px-5 py-4 font-mono text-xs font-semibold text-[--text-muted] w-8">
        {rank}
      </td>
      <td className="px-5 py-4 font-mono font-bold text-[--text-primary] text-sm w-16">
        {candidate.symbol}
      </td>
      <td className="hidden md:table-cell px-5 py-4 text-sm text-[--text-secondary] truncate font-medium max-w-[160px]">
        {candidate.name}
      </td>
      <td className="px-5 py-4 w-32">
        {candidate.direction ? (
          <DirectionBadge direction={candidate.direction} size="sm" />
        ) : (
          <span className="text-xs text-[--text-muted]">—</span>
        )}
      </td>
      <td className="hidden sm:table-cell px-5 py-4 w-28">
        {candidate.time_horizon && <HorizonBadge horizon={candidate.time_horizon} size="sm" />}
      </td>
      <td className="hidden sm:table-cell px-5 py-4 w-32">
        {candidate.confidence_tier && <ConfidenceBadge tier={candidate.confidence_tier} size="sm" />}
      </td>
      <td className="px-5 py-4 w-24">
        <ScoreDisplay score={candidate.candidate_score} />
      </td>
    </tr>
  );
}
