"use client";

import { Candidate } from "@/app/types";
import { ConfidenceBadge } from "@/app/components/shared/ConfidenceBadge";
import { HorizonBadge } from "@/app/components/shared/HorizonBadge";
import { ScoreDisplay } from "@/app/components/shared/ScoreDisplay";

interface CandidateRowProps {
  candidate: Candidate;
  rank: number;
  onSelect: () => void;
}

function getConfidenceLeftBorderColor(tier?: string): string {
  if (tier === "High") return "border-l-[--high]";
  if (tier === "Medium") return "border-l-[--medium]";
  return "border-l-[--low]";
}

export function CandidateRow({ candidate, rank, onSelect }: CandidateRowProps) {
  const isLowConfidence = candidate.confidence_tier === "Low";
  const borderColor = getConfidenceLeftBorderColor(candidate.confidence_tier);

  return (
    <tr
      onClick={onSelect}
      className={`cursor-pointer border-b border-[--border] transition-smooth group border-l-4 ${borderColor} ${
        isLowConfidence
          ? "bg-[--bg-surface] opacity-75 hover:opacity-100 hover:bg-[--bg-raised]"
          : "bg-[--bg-surface] hover:bg-[--bg-raised]"
      }`}
    >
      <td className="px-5 py-4 font-mono text-xs font-semibold text-[--text-muted] w-8">
        {rank}
      </td>
      <td className="px-5 py-4 font-mono font-bold text-[--text-primary] text-sm w-16">
        {candidate.symbol}
      </td>
      <td className="px-5 py-4 text-sm text-[--text-primary] truncate font-medium">
        {candidate.name}
      </td>
      <td className="px-5 py-4 text-xs text-[--text-secondary] w-24 font-medium">
        {candidate.category}
      </td>
      <td className="px-5 py-4 w-28">
        {candidate.time_horizon && <HorizonBadge horizon={candidate.time_horizon} size="sm" />}
      </td>
      <td className="px-5 py-4 w-32">
        {candidate.confidence_tier && <ConfidenceBadge tier={candidate.confidence_tier} size="sm" />}
      </td>
      <td className="px-5 py-4 w-24">
        <ScoreDisplay score={candidate.candidate_score} />
      </td>
    </tr>
  );
}
