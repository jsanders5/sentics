"use client";

import { useState } from "react";
import { ErrorBoundary } from "@/app/components/ErrorBoundary";
import { Header } from "@/app/components/layout/Header";
import { CategoryPanel } from "@/app/components/panels/CategoryPanel";
import { FilterBar } from "@/app/components/panels/FilterBar";
import { CandidatesTable } from "@/app/components/table/CandidatesTable";
import { CandidateDetailDrawer } from "@/app/components/detail/CandidateDetailDrawer";
import { useCandidates } from "@/app/hooks/useCandidates";
import { useCategories } from "@/app/hooks/useCategories";
import { useFilterState } from "@/app/hooks/useFilterState";
import { Candidate } from "@/app/types";

export default function DashboardPage() {
  const { candidates, loading: loadingCandidates, error: candidatesError, timestamp } = useCandidates();
  const { categories, loading: loadingCategories, error: categoriesError } = useCategories();
  const {
    filters,
    sortKey,
    sortOrder,
    filteredAndSorted,
    setHorizon,
    setCategory,
    setConfidence,
    setSortKey,
    clearFilters,
    hasActiveFilters,
  } = useFilterState();

  const [selectedCandidate, setSelectedCandidate] = useState<Candidate | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>("All");
  const [sidebarOpen, setSidebarOpen] = useState(false);

  // Get unique categories from candidates
  const uniqueCategories = Array.from(new Set(candidates.map((c) => c.category))).sort();

  // Filter by selected category and apply all filters
  const displayedCandidates = filteredAndSorted(
    selectedCategory === "All"
      ? candidates
      : candidates.filter((c) => c.category === selectedCategory)
  );

  const handleCategorySelect = (category: string) => {
    setSelectedCategory(category);
    setSidebarOpen(false);
    if (category !== "All") {
      setCategory(category);
    } else {
      setCategory("All");
    }
  };

  // Show error state if both data sources failed
  if ((candidatesError || categoriesError) && !loadingCandidates && !loadingCategories) {
    return (
      <ErrorBoundary>
        <div className="flex h-screen flex-col" style={{ backgroundColor: 'var(--bg-base)' }}>
          <Header timestamp={timestamp} />
          <div className="flex flex-1 items-center justify-center p-6">
            <div className="max-w-md text-center space-y-4">
              <h2 style={{ color: 'var(--text-primary)' }} className="text-xl font-semibold">Unable to Load Data</h2>
              <p style={{ color: 'var(--text-secondary)' }} className="text-sm">
                {candidatesError || categoriesError}
              </p>
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

        <div className="flex flex-1 overflow-hidden relative">
          {/* Mobile menu toggle */}
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="md:hidden fixed bottom-6 right-6 z-40 w-14 h-14 rounded-full flex items-center justify-center text-white font-bold text-xl hover:opacity-80 transition-opacity"
            style={{ backgroundColor: 'var(--accent)' }}
          >
            ☰
          </button>

          {/* Mobile overlay */}
          {sidebarOpen && (
            <div
              onClick={() => setSidebarOpen(false)}
              className="md:hidden fixed inset-0 z-30"
              style={{ backgroundColor: 'rgba(0, 0, 0, 0.5)' }}
            />
          )}

          {/* Category Panel - Desktop visible, Mobile as overlay */}
          <div className={`fixed md:static inset-y-[73px] left-0 z-40 w-56 transition-transform duration-300 md:transition-none ${
            sidebarOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
          }`}>
            <CategoryPanel
              categories={categories}
              loading={loadingCategories}
              selectedCategory={selectedCategory}
              onSelectCategory={handleCategorySelect}
            />
          </div>

          {/* Main Content */}
          <div className="flex flex-1 flex-col overflow-hidden w-full md:w-auto">
            {/* Filter Bar */}
            <FilterBar
              filters={filters}
              categories={uniqueCategories}
              onHorizonChange={setHorizon}
              onCategoryChange={(cat) => {
                setCategory(cat);
                setSelectedCategory(cat === "All" ? "All" : cat);
              }}
              onConfidenceChange={setConfidence}
              onClearFilters={() => {
                clearFilters();
                setSelectedCategory("All");
              }}
              hasActiveFilters={hasActiveFilters}
            />

            {/* Low Signal Banner */}
            {displayedCandidates.length > 0 && displayedCandidates.length < 5 && (
              <div
                className="px-4 md:px-6 py-3 text-sm"
                style={{
                  backgroundColor: 'var(--low-signal-bg)',
                  borderBottom: '1px solid var(--low-signal-text)',
                  color: 'var(--low-signal-text)'
                }}
              >
                Current market conditions have produced fewer candidates than usual. {displayedCandidates.length}{" "}
                {displayedCandidates.length === 1 ? "candidate" : "candidates"} meet current criteria.
              </div>
            )}

            {/* Table */}
            <div className="flex-1 overflow-y-auto">
              <CandidatesTable
                candidates={displayedCandidates}
                loading={loadingCandidates}
                sortKey={sortKey}
                sortOrder={sortOrder}
                onSortChange={setSortKey}
                onSelectCandidate={setSelectedCandidate}
              />
            </div>
          </div>

          {/* Detail Drawer */}
          <CandidateDetailDrawer
            candidate={selectedCandidate}
            isOpen={!!selectedCandidate}
            onClose={() => setSelectedCandidate(null)}
          />
        </div>
      </div>
    </ErrorBoundary>
  );
}
