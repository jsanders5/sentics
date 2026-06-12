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
    <div
      className="px-4 md:px-6 py-3 overflow-x-auto"
      style={{
        backgroundColor: 'var(--bg-surface)',
        borderBottom: '1px solid var(--border)'
      }}
    >
      <div className="flex items-center gap-2 md:gap-3 min-w-max md:min-w-0">
        <select
          value={filters.horizon || "All"}
          onChange={(e) => onHorizonChange(e.target.value)}
          className="rounded border px-2 md:px-3 py-1.5 text-xs md:text-sm text-[--text-primary] hover:opacity-80 focus:outline-none whitespace-nowrap"
          style={{
            backgroundColor: 'var(--bg-raised)',
            borderColor: 'var(--border)',
            color: 'var(--text-primary)'
          }}
        >
          <option value="All">Horizon: All</option>
          <option value="Short">Horizon: Short (1-7d)</option>
          <option value="Medium">Horizon: Medium (1-4w)</option>
          <option value="Long">Horizon: Long (1-3mo)</option>
        </select>

        <select
          value={filters.category || "All"}
          onChange={(e) => onCategoryChange(e.target.value)}
          className="rounded border px-2 md:px-3 py-1.5 text-xs md:text-sm text-[--text-primary] hover:opacity-80 focus:outline-none whitespace-nowrap"
          style={{
            backgroundColor: 'var(--bg-raised)',
            borderColor: 'var(--border)',
            color: 'var(--text-primary)'
          }}
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
          className="rounded border px-2 md:px-3 py-1.5 text-xs md:text-sm text-[--text-primary] hover:opacity-80 focus:outline-none whitespace-nowrap"
          style={{
            backgroundColor: 'var(--bg-raised)',
            borderColor: 'var(--border)',
            color: 'var(--text-primary)'
          }}
        >
          <option value="All">Confidence: All</option>
          <option value="High">Confidence: High</option>
          <option value="Medium">Confidence: Medium</option>
          <option value="Low">Confidence: Low</option>
        </select>

        {hasActiveFilters && (
          <button
            onClick={onClearFilters}
            className="rounded border px-2 md:px-3 py-1.5 text-sm text-[--text-secondary] hover:opacity-80 transition-colors whitespace-nowrap"
            style={{
              backgroundColor: 'var(--bg-raised)',
              borderColor: 'var(--border)',
              color: 'var(--text-secondary)'
            }}
            title="Clear all filters"
          >
            ✕
          </button>
        )}
      </div>
    </div>
  );
}
