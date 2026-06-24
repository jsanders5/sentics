"use client";

import { Candidate, SortKey, SortOrder, BearishView } from "@/app/types";
import { CandidateCard } from "./CandidateCard";

interface CandidatesGridProps {
  candidates: Candidate[];
  loading: boolean;
  sortKey: SortKey;
  sortOrder: SortOrder;
  bearishView: BearishView;
  onBearishViewChange: (view: BearishView) => void;
  onSortChange: (key: SortKey) => void;
  onSelectCandidate: (candidate: Candidate) => void;
}

const sortOptions: { key: SortKey; label: string }[] = [
  { key: "score", label: "Signal strength" },
  { key: "market_cap", label: "Market cap" },
  { key: "symbol", label: "Symbol" },
  { key: "direction", label: "Direction" },
  { key: "confidence", label: "Confidence" },
  { key: "horizon", label: "Horizon" },
];

function GridShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 p-4 md:p-6">
      {children}
    </div>
  );
}

export function CandidatesGrid({
  candidates,
  loading,
  sortKey,
  sortOrder,
  bearishView,
  onBearishViewChange,
  onSortChange,
  onSelectCandidate,
}: CandidatesGridProps) {
  if (loading) {
    return (
      <GridShell>
        {Array.from({ length: 8 }).map((_, i) => (
          <div key={i} className="card h-44 animate-pulse" style={{ opacity: 0.6 }} />
        ))}
      </GridShell>
    );
  }

  if (candidates.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <div className="text-2xl font-light text-[--text-muted] mb-2">No candidates found</div>
        <p className="text-sm text-[--text-muted]">Try adjusting your filters or check back later.</p>
      </div>
    );
  }

  return (
    <div>
      {/* Toolbar */}
      <div className="flex items-center justify-between gap-3 px-4 md:px-6 pt-4 md:pt-6">
        <div className="flex items-center gap-3">
          <p className="text-sm text-[--text-secondary]">
            <span className="font-semibold text-[--text-primary]">{candidates.length}</span> assets
          </p>
          {/* Bearish view toggle */}
          <div
            className="flex items-center rounded-lg border p-0.5"
            style={{ backgroundColor: "var(--bg-raised)", borderColor: "var(--border)" }}
            title="How bearish setups are framed"
          >
            {(["spot", "short"] as BearishView[]).map((v) => (
              <button
                key={v}
                onClick={() => onBearishViewChange(v)}
                className="px-2.5 py-1 rounded-md text-xs font-medium capitalize transition-colors"
                style={{
                  backgroundColor: bearishView === v ? "var(--accent)" : "transparent",
                  color: bearishView === v ? "#fff" : "var(--text-secondary)",
                }}
              >
                {v}
              </button>
            ))}
          </div>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-xs text-[--text-muted] hidden sm:block">Sort by</label>
          <select
            value={sortKey}
            onChange={(e) => onSortChange(e.target.value as SortKey)}
            className="rounded-lg border px-2.5 py-1.5 text-xs md:text-sm cursor-pointer"
            style={{ backgroundColor: "var(--bg-raised)", borderColor: "var(--border)", color: "var(--text-primary)" }}
          >
            {sortOptions.map((o) => (
              <option key={o.key} value={o.key}>{o.label}</option>
            ))}
          </select>
          <button
            onClick={() => onSortChange(sortKey)}
            title="Toggle sort order"
            aria-label="Toggle sort order"
            className="rounded-lg border w-8 h-8 flex items-center justify-center text-sm hover:border-[--accent] transition-colors"
            style={{ backgroundColor: "var(--bg-raised)", borderColor: "var(--border)", color: "var(--text-secondary)" }}
          >
            {sortOrder === "asc" ? "↑" : "↓"}
          </button>
        </div>
      </div>

      <GridShell>
        {candidates.map((candidate, i) => (
          <CandidateCard
            key={candidate.symbol}
            candidate={candidate}
            index={i}
            bearishView={bearishView}
            onSelect={() => onSelectCandidate(candidate)}
          />
        ))}
      </GridShell>
    </div>
  );
}
