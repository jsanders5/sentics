"use client";

import { useState } from "react";
import { ErrorBoundary } from "@/app/components/ErrorBoundary";
import { Header } from "@/app/components/layout/Header";
import { FilterBar } from "@/app/components/panels/FilterBar";
import { CandidatesTable } from "@/app/components/table/CandidatesTable";
import { CandidateDetailDrawer } from "@/app/components/detail/CandidateDetailDrawer";
import { useCandidates } from "@/app/hooks/useCandidates";
import { useFilterState } from "@/app/hooks/useFilterState";
import { Candidate } from "@/app/types";

export default function DashboardPage() {
  const { candidates, loading, error, timestamp } = useCandidates();
  const {
    filters,
    sortKey,
    sortOrder,
    filteredAndSorted,
    setDirection,
    setHorizon,
    setConfidence,
    setSortKey,
    clearFilters,
    hasActiveFilters,
  } = useFilterState();

  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null);

  const displayedCandidates = filteredAndSorted(candidates);

  if (error && !loading) {
    return (
      <ErrorBoundary>
        <div className="flex h-screen flex-col" style={{ backgroundColor: 'var(--bg-base)' }}>
          <Header timestamp={timestamp} />
          <div className="flex flex-1 items-center justify-center p-6">
            <div className="max-w-md text-center space-y-4">
              <h2 style={{ color: 'var(--text-primary)' }} className="text-xl font-semibold">Unable to Load Data</h2>
              <p style={{ color: 'var(--text-secondary)' }} className="text-sm">{error}</p>
              <p style={{ color: 'var(--text-muted)' }} className="text-xs">
                Please verify that Supabase environment variables are configured in Vercel:
                SUPABASE_URL and SUPABASE_SECRET_KEY
              </p>
              <button
                onClick={() => window.location.reload()}
                style={{ backgroundColor: 'var(--accent)' }}
                className="mt-4 rounded-lg px-4 py-2 font-semibold text-white hover:opacity-90 transition-opacity"
              >
                Reload Page
              </button>
            </div>
          </div>
        </div>
      </ErrorBoundary>
    );
  }

  return (
    <ErrorBoundary>
      <div className="flex h-screen flex-col" style={{ backgroundColor: 'var(--bg-base)' }}>
        <Header timestamp={timestamp} />

        <div className="flex flex-1 flex-col overflow-hidden">
          <FilterBar
            filters={filters}
            onDirectionChange={setDirection}
            onHorizonChange={setHorizon}
            onConfidenceChange={setConfidence}
            onClearFilters={clearFilters}
            hasActiveFilters={hasActiveFilters}
          />

          {displayedCandidates.length > 0 && displayedCandidates.length < 5 && (
            <div
              className="px-4 md:px-6 py-3 text-sm"
              style={{
                backgroundColor: 'var(--neutral-dir-bg)',
                borderBottom: '1px solid var(--neutral-dir-border)',
                color: 'var(--text-secondary)'
              }}
            >
              Low signal environment — {displayedCandidates.length}{" "}
              {displayedCandidates.length === 1 ? "candidate" : "candidates"} match current filters.
            </div>
          )}

          <div className="flex-1 overflow-y-auto">
            <CandidatesTable
              candidates={displayedCandidates}
              loading={loading}
              sortKey={sortKey}
              sortOrder={sortOrder}
              onSortChange={setSortKey}
              onSelectCandidate={setSelectedCandidate}
            />
          </div>
        </div>

        <CandidateDetailDrawer
          candidate={selectedCandidate}
          isOpen={!!selectedCandidate}
          onClose={() => setSelectedCandidate(null)}
        />
      </div>
    </ErrorBoundary>
  );
}
