"use client";

import { useState } from "react";
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
  const { candidates, loading: loadingCandidates, timestamp } = useCandidates();
  const { categories, loading: loadingCategories } = useCategories();
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
    if (category !== "All") {
      setCategory(category);
    } else {
      setCategory("All");
    }
  };

  return (
    <div className="flex h-screen flex-col bg-[--bg-base]">
      <Header timestamp={timestamp} />

      <div className="flex flex-1 overflow-hidden">
        {/* Category Panel - Desktop only */}
        <CategoryPanel
          categories={categories}
          loading={loadingCategories}
          selectedCategory={selectedCategory}
          onSelectCategory={handleCategorySelect}
        />

        {/* Main Content */}
        <div className="flex flex-1 flex-col overflow-hidden">
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
            <div className="border-b border-[--staleness-border] bg-[--low-signal-bg] px-6 py-3 text-sm text-[--low-signal-text]">
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
  );
}
