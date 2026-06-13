"use client";

import { useState, useEffect, useCallback } from "react";
import { Candidate } from "@/app/types";

interface UseCandidatesResult {
  candidates: Candidate[];
  loading: boolean;
  error: string | null;
  timestamp: string | null;
  refetch: () => Promise<void>;
}

export function useCandidates(): UseCandidatesResult {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timestamp, setTimestamp] = useState<string | null>(null);

  const fetchCandidates = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch("/api/candidates");
      if (!response.ok) {
        const text = await response.text();
        console.error("[useCandidates] Error response:", text);
        throw new Error(`API error: ${response.status}`);
      }
      const data = await response.json();
      setCandidates(data.candidates || []);
      setTimestamp(data.timestamp || null);
      setError(null);
    } catch (err) {
      const errMsg = err instanceof Error ? err.message : "Failed to load candidates";
      console.error("[useCandidates] Error:", errMsg);
      setError(errMsg);
      setCandidates([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCandidates();
    // Auto-refresh every 5 minutes
    const interval = setInterval(fetchCandidates, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [fetchCandidates]);

  return { candidates, loading, error, timestamp, refetch: fetchCandidates };
}
