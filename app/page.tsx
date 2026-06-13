"use client";

import { useState } from "react";
import { ErrorBoundary } from "@/app/components/ErrorBoundary";
import { Header } from "@/app/components/layout/Header";
import { FilterBar } from "@/app/components/panels/FilterBar";
import { CandidatesGrid } from "@/app/components/cards/CandidatesGrid";
import { CandidateDetailDrawer } from "@/app/components/detail/CandidateDetailDrawer";
import { useCandidates } from "@/app/hooks/useCandidates";
import { useFilterState } from "@/app/hooks/useFilterState";
import { isStale, STALE_HOURS } from "@/app/lib/freshness";
import { Candidate } from "@/app/types";

export default function DashboardPage() {
  const { candidates, loading, error, timestamp, refetch } = useCandidates();
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
  const [refreshing, setRefreshing] = useState(false);
  const [toast, setToast] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const displayedCandidates = filteredAndSorted(candidates);

  const handleRefresh = async () => {
    setRefreshing(true);
    setToast(null);
    try {
      const res = await fetch("/api/run-pipeline", { method: "POST" });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || data.status === "error") {
        throw new Error(data.error || `Pipeline failed (${res.status})`);
      }
      await refetch();
      setToast({ type: "success", text: data.message || "Pipeline complete — data refreshed." });
    } catch (e) {
      setToast({ type: "error", text: e instanceof Error ? e.message : "Refresh failed." });
    } finally {
      setRefreshing(false);
      setTimeout(() => setToast(null), 6000);
    }
  };

  if (error && !loading) {
    return (
      <ErrorBoundary>
        <div className="flex h-screen flex-col" style={{ backgroundColor: 'var(--bg-base)' }}>
          <Header timestamp={timestamp} onRefresh={handleRefresh} refreshing={refreshing} />
          <div className="flex flex-1 items-center justify-center p-6">
            <div className="max-w-md text-center space-y-4">
              <h2 className="text-xl font-semibold" style={{ color: 'var(--text-primary)' }}>Unable to Load Data</h2>
              <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>{error}</p>
              <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
                Please verify that Supabase environment variables are configured in Vercel:
                SUPABASE_URL and SUPABASE_SECRET_KEY
              </p>
              <button
                onClick={() => window.location.reload()}
                className="mt-4 rounded-lg px-4 py-2 font-semibold text-white hover:opacity-90 transition-opacity"
                style={{ backgroundColor: 'var(--accent)' }}
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
        <Header timestamp={timestamp} onRefresh={handleRefresh} refreshing={refreshing} />

        {/* Centered content column */}
        <div className="flex flex-1 flex-col overflow-hidden">
          <div className="w-full max-w-7xl mx-auto flex flex-col flex-1 overflow-hidden">

            {!loading && isStale(timestamp) && (
              <div
                className="px-4 md:px-6 py-3 text-sm flex items-center gap-2"
                style={{
                  backgroundColor: 'var(--stale-bg)',
                  borderBottom: '1px solid var(--stale-border)',
                  color: 'var(--stale)',
                }}
              >
                <span aria-hidden>⚠</span>
                <span>
                  This data is more than {STALE_HOURS} hours old. The analysis pipeline runs once daily
                  at 15:00 UTC — signals may no longer reflect current market conditions.
                </span>
              </div>
            )}

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
              <CandidatesGrid
                candidates={displayedCandidates}
                loading={loading}
                sortKey={sortKey}
                sortOrder={sortOrder}
                onSortChange={setSortKey}
                onSelectCandidate={setSelectedCandidate}
              />
            </div>

          </div>
        </div>

        <CandidateDetailDrawer
          candidate={selectedCandidate}
          isOpen={!!selectedCandidate}
          onClose={() => setSelectedCandidate(null)}
        />

        {/* Refresh result toast */}
        {toast && (
          <div
            role="status"
            className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 max-w-md px-4 py-3 rounded-lg text-sm shadow-lg border animate-card-in"
            style={{
              backgroundColor: 'var(--bg-raised)',
              borderColor: toast.type === 'error' ? 'var(--bearish-border)' : 'var(--bullish-border)',
              color: toast.type === 'error' ? 'var(--bearish)' : 'var(--text-primary)',
            }}
          >
            {toast.text}
          </div>
        )}
      </div>
    </ErrorBoundary>
  );
}
