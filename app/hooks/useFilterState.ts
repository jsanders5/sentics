"use client";

import { useState, useCallback } from "react";
import { Candidate, FilterState, SortKey, SortOrder } from "@/app/types";

interface UseFilterStateResult {
  filters: FilterState;
  sortKey: SortKey;
  sortOrder: SortOrder;
  filteredAndSorted: (candidates: Candidate[]) => Candidate[];
  setDirection: (direction: string) => void;
  setHorizon: (horizon: string) => void;
  setConfidence: (confidence: string) => void;
  setSortKey: (key: SortKey) => void;
  clearFilters: () => void;
  hasActiveFilters: boolean;
}

export function useFilterState(): UseFilterStateResult {
  const [filters, setFilters] = useState<FilterState>({
    direction: "All",
    horizon: "All",
    confidence: "All",
  });
  const [sortKey, setSortKey] = useState<SortKey>("score");
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc");

  const hasActiveFilters =
    filters.direction !== "All" || filters.horizon !== "All" || filters.confidence !== "All";

  const setDirection = useCallback((direction: string) => {
    setFilters((prev) => ({ ...prev, direction: direction as any }));
  }, []);

  const setHorizon = useCallback((horizon: string) => {
    setFilters((prev) => ({ ...prev, horizon: horizon as any }));
  }, []);

  const setConfidence = useCallback((confidence: string) => {
    setFilters((prev) => ({ ...prev, confidence: confidence as any }));
  }, []);

  const clearFilters = useCallback(() => {
    setFilters({ direction: "All", horizon: "All", confidence: "All" });
  }, []);

  const filteredAndSorted = useCallback(
    (candidates: Candidate[]): Candidate[] => {
      let result = [...candidates];

      if (filters.direction && filters.direction !== "All") {
        result = result.filter((c) => c.direction === filters.direction);
      }

      if (filters.horizon && filters.horizon !== "All") {
        result = result.filter((c) => c.time_horizon === filters.horizon);
      }

      if (filters.confidence && filters.confidence !== "All") {
        result = result.filter((c) => c.confidence_tier === filters.confidence);
      }

      result.sort((a, b) => {
        let aVal: any;
        let bVal: any;

        switch (sortKey) {
          case "symbol":
            aVal = a.symbol;
            bVal = b.symbol;
            break;
          case "direction":
            const dirOrder = { Bullish: 3, Neutral: 2, Bearish: 1 };
            aVal = dirOrder[a.direction as keyof typeof dirOrder] || 0;
            bVal = dirOrder[b.direction as keyof typeof dirOrder] || 0;
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
          case "market_cap":
            aVal = a.market_cap || 0;
            bVal = b.market_cap || 0;
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
    setDirection,
    setHorizon,
    setConfidence,
    setSortKey: handleSortKeyChange,
    clearFilters,
    hasActiveFilters,
  };
}
