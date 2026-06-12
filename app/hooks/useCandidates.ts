"use client";

import { useState, useEffect } from "react";
import { Candidate } from "@/app/types";

interface UseCandidatesResult {
  candidates: Candidate[];
  loading: boolean;
  error: string | null;
  timestamp: string | null;
}

export function useCandidates(): UseCandidatesResult {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timestamp, setTimestamp] = useState<string | null>(null);

  useEffect(() => {
    const fetchCandidates = async () => {
      try {
        setLoading(true);
        const response = await fetch("/api/candidates");
        if (!response.ok) {
          throw new Error(`API error: ${response.status}`);
        }
        const data = await response.json();
        setCandidates(data.candidates || []);
        setTimestamp(data.timestamp || new Date().toISOString());
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load candidates");
        setCandidates([]);
      } finally {
        setLoading(false);
      }
    };

    fetchCandidates();
    // Refresh every 5 minutes
    const interval = setInterval(fetchCandidates, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  return { candidates, loading, error, timestamp };
}
