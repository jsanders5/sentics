"use client";

import { useState, useCallback } from "react";
import { Candidate, FilterState, SortKey, SortOrder } from "@/app/types";

interface UseFilterStateResult {
  filters: FilterState;
  sortKey: SortKey;
  sortOrder: SortOrder;
  filteredAndSorted: (candidates: Candidate[]) => Candidate[];
  setHorizon: (horizon: string) => void;
  setCategory: (category: string) => void;
  setConfidence: (confidence: string) => void;
  setSortKey: (key: SortKey) => void;
  clearFilters: () => void;
  hasActiveFilters: boolean;
}

export function useFilterState(): UseFilterStateResult {
  const [filters, setFilters] = useState<FilterState>({
    horizon: "All",
    category: "All",
    confidence: "All",
  });
  const [sortKey, setSortKey] = useState<SortKey>("score");
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc");

  const hasActiveFilters =
    filters.horizon !== "All" || filters.category !== "All" || filters.confidence !== "All";

  const setHorizon = useCallback((horizon: string) => {
    setFilters((prev) => ({ ...prev, horizon: horizon as any }));
  }, []);

  const setCategory = useCallback((category: string) => {
    setFilters((prev) => ({ ...prev, category }));
  }, []);

  const setConfidence = useCallback((confidence: string) => {
    setFilters((prev) => ({ ...prev, confidence: confidence as any }));
  }, []);

  const clearFilters = useCallback(() => {
    setFilters({ horizon: "All", category: "All", confidence: "All" });
  }, []);

  const filteredAndSorted = useCallback(
    (candidates: Candidate[]): Candidate[] => {
      let result = [...candidates];

      // Apply filters
      if (filters.horizon && filters.horizon !== "All") {
        result = result.filter((c) => c.time_horizon === filters.horizon);
      }

      if (filters.category && filters.category !== "All") {
        result = result.filter((c) => c.category === filters.category);
      }

      if (filters.confidence && filters.confidence !== "All") {
        result = result.filter((c) => c.confidence_tier === filters.confidence);
      }

      // Apply sort
      result.sort((a, b) => {
        let aVal: any;
        let bVal: any;

        switch (sortKey) {
          case "rank":
            return sortOrder === "asc" ? a.candidate_score - b.candidate_score : b.candidate_score - a.candidate_score;
          case "symbol":
            aVal = a.symbol;
            bVal = b.symbol;
            break;
          case "category":
            aVal = a.category;
            bVal = b.category;
            break;
          case "horizon":
            aVal = a.time_horizon || "";
            bVal = b.time_horizon || "";
            break;
          case "confidence":
            const confidenceOrder = { High: 3, Medium: 2, Low: 1 };
            aVal = confidenceOrder[a.confidence_tier as keyof typeof confidenceOrder] || 0;
            bVal = confidenceOrder[b.confidence_tier as keyof typeof confidenceOrder] || 0;
            break;
          case "score":
          default:
            aVal = a.candidate_score;
            bVal = b.candidate_score;
            break;
        }

        if (aVal < bVal) return sortOrder === "asc" ? -1 : 1;
        if (aVal > bVal) return sortOrder === "asc" ? 1 : -1;
        return 0;
      });

      return result;
    },
    [filters, sortKey, sortOrder]
  );

  const handleSortKeyChange = useCallback(
    (key: SortKey) => {
      if (sortKey === key) {
        setSortOrder(sortOrder === "asc" ? "desc" : sortOrder === "desc" ? null : "asc");
      } else {
        setSortKey(key);
        setSortOrder("desc");
      }
    },
    [sortKey, sortOrder]
  );

  return {
    filters,
    sortKey,
    sortOrder,
    filteredAndSorted,
    setHorizon,
    setCategory,
    setConfidence,
    setSortKey: handleSortKeyChange,
    clearFilters,
    hasActiveFilters,
  };
}
