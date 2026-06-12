"use client";

import { Candidate, SortKey, SortOrder } from "@/app/types";
import { CandidateRow } from "./CandidateRow";
import { Skeleton } from "@/app/components/shared/Skeleton";

interface CandidatesTableProps {
  candidates: Candidate[];
  loading: boolean;
  sortKey: SortKey;
  sortOrder: SortOrder;
  onSortChange: (key: SortKey) => void;
  onSelectCandidate: (candidate: Candidate) => void;
}

function SortButton({
  children,
  onClick,
  isActive,
  sortOrder,
}: {
  children: React.ReactNode;
  onClick: () => void;
  isActive: boolean;
  sortOrder: SortOrder;
}) {
  return (
    <button
      onClick={onClick}
      className="flex items-center gap-1 hover:text-[--text-primary] transition-colors"
    >
      {children}
      {isActive && (
        <span className="text-xs">{sortOrder === "asc" ? "↑" : sortOrder === "desc" ? "↓" : ""}</span>
      )}
    </button>
  );
}

export function CandidatesTable({
  candidates,
  loading,
  sortKey,
  sortOrder,
  onSortChange,
  onSelectCandidate,
}: CandidatesTableProps) {
  if (loading) {
    return (
      <div className="p-6 space-y-2">
        <Skeleton className="h-12 w-full" count={8} />
      </div>
    );
  }

  if (candidates.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="text-2xl font-light text-[--text-muted] mb-2">No candidates found</div>
        <p className="text-sm text-[--text-muted]">
          Try adjusting your filters or check back later.
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse">
        <thead className="sticky top-[73px] z-30 bg-[--bg-surface] border-b border-[--border]">
          <tr>
            <th className="px-5 py-4 text-left font-sans text-xs font-bold uppercase tracking-widest text-[--text-muted] w-8 bg-[--bg-surface]">
              <SortButton
                onClick={() => onSortChange("rank")}
                isActive={sortKey === "rank"}
                sortOrder={sortOrder}
              >
                #
              </SortButton>
            </th>
            <th className="px-5 py-4 text-left font-sans text-xs font-bold uppercase tracking-widest text-[--text-muted] w-16 bg-[--bg-surface]">
              <SortButton
                onClick={() => onSortChange("symbol")}
                isActive={sortKey === "symbol"}
                sortOrder={sortOrder}
              >
                Symbol
              </SortButton>
            </th>
            <th className="px-5 py-4 text-left font-sans text-xs font-bold uppercase tracking-widest text-[--text-muted] bg-[--bg-surface]">
              <SortButton
                onClick={() => onSortChange("symbol")}
                isActive={sortKey === "symbol"}
                sortOrder={sortOrder}
              >
                Name
              </SortButton>
            </th>
            <th className="px-5 py-4 text-left font-sans text-xs font-bold uppercase tracking-widest text-[--text-muted] w-24 bg-[--bg-surface]">
              <SortButton
                onClick={() => onSortChange("category")}
                isActive={sortKey === "category"}
                sortOrder={sortOrder}
              >
                Category
              </SortButton>
            </th>
            <th className="px-5 py-4 text-left font-sans text-xs font-bold uppercase tracking-widest text-[--text-muted] w-28 bg-[--bg-surface]">
              <SortButton
                onClick={() => onSortChange("horizon")}
                isActive={sortKey === "horizon"}
                sortOrder={sortOrder}
              >
                Horizon
              </SortButton>
            </th>
            <th className="px-5 py-4 text-left font-sans text-xs font-bold uppercase tracking-widest text-[--text-muted] w-32 bg-[--bg-surface]">
              <SortButton
                onClick={() => onSortChange("confidence")}
                isActive={sortKey === "confidence"}
                sortOrder={sortOrder}
              >
                Confidence
              </SortButton>
            </th>
            <th className="px-5 py-4 text-left font-sans text-xs font-bold uppercase tracking-widest text-[--text-muted] w-24 bg-[--bg-surface]">
              <SortButton
                onClick={() => onSortChange("score")}
                isActive={sortKey === "score"}
                sortOrder={sortOrder}
              >
                Score
              </SortButton>
            </th>
          </tr>
        </thead>
        <tbody>
          {candidates.map((candidate, index) => (
            <CandidateRow
              key={`${candidate.symbol}-${index}`}
              candidate={candidate}
              rank={index + 1}
              onSelect={() => onSelectCandidate(candidate)}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}
