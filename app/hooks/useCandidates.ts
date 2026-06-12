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
        console.log("[useCandidates] Fetching candidates...");
        const response = await fetch("/api/candidates");
        console.log("[useCandidates] Response status:", response.status);
        if (!response.ok) {
          const text = await response.text();
          console.error("[useCandidates] Error response:", text);
          throw new Error(`API error: ${response.status}`);
        }
        const data = await response.json();
        console.log("[useCandidates] Data loaded:", data.candidates?.length || 0, "candidates");
        setCandidates(data.candidates || []);
        setTimestamp(data.timestamp || new Date().toISOString());
        setError(null);
      } catch (err) {
        const errMsg = err instanceof Error ? err.message : "Failed to load candidates";
        console.error("[useCandidates] Error:", errMsg);
        setError(errMsg);
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
