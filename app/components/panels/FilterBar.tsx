"use client";

import { FilterState } from "@/app/types";

interface FilterBarProps {
  filters: FilterState;
  onDirectionChange: (value: string) => void;
  onHorizonChange: (value: string) => void;
  onConfidenceChange: (value: string) => void;
  onClearFilters: () => void;
  hasActiveFilters: boolean;
}

export function FilterBar({
  filters,
  onDirectionChange,
  onHorizonChange,
  onConfidenceChange,
  onClearFilters,
  hasActiveFilters,
}: FilterBarProps) {
  const selectClass = "rounded border px-2 md:px-3 py-1.5 text-xs md:text-sm hover:opacity-80 focus:outline-none whitespace-nowrap cursor-pointer";
  const selectStyle = {
    backgroundColor: 'var(--bg-raised)',
    borderColor: 'var(--border)',
    color: 'var(--text-primary)'
  };

  return (
    <div
      className="px-4 md:px-6 py-3 overflow-x-auto"
      style={{ backgroundColor: 'var(--bg-surface)', borderBottom: '1px solid var(--border)' }}
    >
      <div className="flex items-center gap-2 md:gap-3 min-w-max md:min-w-0">
        <select
          value={filters.direction || "All"}
          onChange={(e) => onDirectionChange(e.target.value)}
          className={selectClass}
          style={selectStyle}
        >
          <option value="All">Direction: All</option>
          <option value="Bullish">▲ Bullish</option>
          <option value="Bearish">▼ Bearish</option>
          <option value="Neutral">→ Neutral</option>
        </select>

        <select
          value={filters.horizon || "All"}
          onChange={(e) => onHorizonChange(e.target.value)}
          className={selectClass}
          style={selectStyle}
        >
          <option value="All">Horizon: All</option>
          <option value="Short">Short (1-7d)</option>
          <option value="Medium">Medium (1-4w)</option>
          <option value="Long">Long (1-3mo)</option>
        </select>

        <select
          value={filters.confidence || "All"}
          onChange={(e) => onConfidenceChange(e.target.value)}
          className={selectClass}
          style={selectStyle}
        >
          <option value="All">Confidence: All</option>
          <option value="High">High</option>
          <option value="Medium">Medium</option>
          <option value="Low">Low</option>
        </select>

        {hasActiveFilters && (
          <button
            onClick={onClearFilters}
            className="rounded border px-2 md:px-3 py-1.5 text-sm hover:opacity-80 transition-colors whitespace-nowrap"
            style={{ backgroundColor: 'var(--bg-raised)', borderColor: 'var(--border)', color: 'var(--text-secondary)' }}
            title="Clear all filters"
          >
            ✕ Clear
          </button>
        )}
      </div>
    </div>
  );
}
