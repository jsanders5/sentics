"use client";

import { FilterState } from "@/app/types";

interface FilterBarProps {
  filters: FilterState;
  categories: string[];
  onHorizonChange: (value: string) => void;
  onCategoryChange: (value: string) => void;
  onConfidenceChange: (value: string) => void;
  onClearFilters: () => void;
  hasActiveFilters: boolean;
}

export function FilterBar({
  filters,
  categories,
  onHorizonChange,
  onCategoryChange,
  onConfidenceChange,
  onClearFilters,
  hasActiveFilters,
}: FilterBarProps) {
  return (
    <div className="border-b border-[--border] bg-[--bg-surface] px-6 py-3">
      <div className="flex items-center gap-3">
        <select
          value={filters.horizon || "All"}
          onChange={(e) => onHorizonChange(e.target.value)}
          className="rounded border border-[--border] bg-[--bg-raised] px-3 py-1.5 text-sm text-[--text-primary] hover:border-[--accent] focus:border-[--accent] focus:outline-none focus:ring-2 focus:ring-[--focus]"
        >
          <option value="All">Horizon: All</option>
          <option value="Short">Horizon: Short (1-7d)</option>
          <option value="Medium">Horizon: Medium (1-4w)</option>
          <option value="Long">Horizon: Long (1-3mo)</option>
        </select>

        <select
          value={filters.category || "All"}
          onChange={(e) => onCategoryChange(e.target.value)}
          className="rounded border border-[--border] bg-[--bg-raised] px-3 py-1.5 text-sm text-[--text-primary] hover:border-[--accent] focus:border-[--accent] focus:outline-none focus:ring-2 focus:ring-[--focus]"
        >
          <option value="All">Category: All</option>
          {categories.map((cat) => (
            <option key={cat} value={cat}>
              Category: {cat}
            </option>
          ))}
        </select>

        <select
          value={filters.confidence || "All"}
          onChange={(e) => onConfidenceChange(e.target.value)}
          className="rounded border border-[--border] bg-[--bg-raised] px-3 py-1.5 text-sm text-[--text-primary] hover:border-[--accent] focus:border-[--accent] focus:outline-none focus:ring-2 focus:ring-[--focus]"
        >
          <option value="All">Confidence: All</option>
          <option value="High">Confidence: High</option>
          <option value="Medium">Confidence: Medium</option>
          <option value="Low">Confidence: Low</option>
        </select>

        {hasActiveFilters && (
          <button
            onClick={onClearFilters}
            className="rounded border border-[--border] bg-[--bg-raised] px-3 py-1.5 text-sm text-[--text-secondary] hover:bg-[--bg-surface] hover:text-[--text-primary] transition-colors"
            title="Clear all filters"
          >
            ✕
          </button>
        )}
      </div>
    </div>
  );
}
