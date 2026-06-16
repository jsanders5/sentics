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
import { Candidate, BearishView } from "@/app/types";

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
  const [bearishView, setBearishView] = useState<BearishView>("spot");
  const [refreshing, setRefreshing] = useState(false);
  const [toast, setToast] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const displayedCandidates = filteredAndSorted(candidates);

  const handleRefresh = async () => {
    setRefreshing(true);
    setToast(null);
    const before = timestamp;
    try {
      const res = await fetch("/api/run-pipeline", { method: "POST" });
      if (!res.ok && res.status !== 202) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.error || `Couldn't start the run (${res.status})`);
      }
    } catch (e) {
      setRefreshing(false);
      setToast({ type: "error", text: e instanceof Error ? e.message : "Couldn't start the run." });
      setTimeout(() => setToast(null), 6000);
      return;
    }
    setToast({ type: "success", text: "Run started — data refreshes as it completes." });

    // The run is async (TA persists fast; FA enriches in self-chaining batches).
    // Poll the candidates timestamp; when it advances, refresh the UI.
    const deadline = Date.now() + 4 * 60 * 1000;
    const poll = async () => {
      try {
        const r = await fetch("/api/candidates");
        const d = await r.json();
        if (d.timestamp && d.timestamp !== before) {
          await refetch();
          setRefreshing(false);
          setToast({ type: "success", text: "Data updated. Catalysts may keep filling in for a minute." });
          setTimeout(() => setToast(null), 6000);
          return;
        }
      } catch {
        /* transient — keep polling */
      }
      if (Date.now() < deadline) {
        setTimeout(poll, 20000);
      } else {
        setRefreshing(false);
        setToast({ type: "success", text: "Still processing — data will update shortly." });
        setTimeout(() => setToast(null), 6000);
      }
    };
    setTimeout(poll, 20000);
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
                bearishView={bearishView}
                onBearishViewChange={setBearishView}
                onSortChange={setSortKey}
                onSelectCandidate={setSelectedCandidate}
              />
            </div>

          </div>
        </div>

        {/* Persistent disclaimer footer (always visible, not modal-gated) */}
        <footer
          className="px-4 md:px-6 py-2 text-center text-[11px] leading-snug"
          style={{ backgroundColor: 'var(--bg-surface)', borderTop: '1px solid var(--border)', color: 'var(--text-muted)' }}
        >
          Educational analysis only — not financial advice. Sentics is not a registered investment
          adviser or broker-dealer. Trade-plan levels are illustrative and can fail. Open
          “Disclaimer” for full terms.
        </footer>

        <CandidateDetailDrawer
          candidate={selectedCandidate}
          isOpen={!!selectedCandidate}
          bearishView={bearishView}
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
