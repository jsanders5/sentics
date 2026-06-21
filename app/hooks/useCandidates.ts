"use client";

import { useState, useEffect, useCallback, useMemo, useRef } from "react";
import { Candidate } from "@/app/types";

// Poll fast while a run's FA is still landing, slow when idle.
const POLL_ACTIVE_MS = 30 * 1000;
const POLL_IDLE_MS = 5 * 60 * 1000;
// Only treat "directional coins missing fa_score" as in-progress if the run is
// recent — otherwise a stalled/partial FA run would show the badge indefinitely.
const FA_FRESH_MS = 15 * 60 * 1000;

export interface FaProgress {
  active: boolean; // a run's news analysis is currently in flight
  scanned: number; // directional coins with an FA result so far
  total: number; // directional coins to scan
}

interface UseCandidatesResult {
  candidates: Candidate[];
  loading: boolean;
  error: string | null;
  timestamp: string | null;
  faProgress: FaProgress;
  refetch: () => Promise<void>;
}

export function useCandidates(): UseCandidatesResult {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timestamp, setTimestamp] = useState<string | null>(null);

  // silent = background refresh: update in place (no skeleton flash / animation
  // replay = no "blink"), and don't blank the grid on a transient failure.
  const fetchCandidates = useCallback(async (opts?: { silent?: boolean }) => {
    const silent = opts?.silent === true;
    try {
      if (!silent) setLoading(true);
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
      if (!silent) {
        setError(errMsg);
        setCandidates([]);
      }
    } finally {
      if (!silent) setLoading(false);
    }
  }, []);

  // FA lands coin-by-coin after TA: directional coins start with fa_score = null
  // and fill in. While a recent run still has unscanned directional coins, news
  // analysis is in progress — regardless of who triggered the run (cron/manual).
  const faProgress = useMemo<FaProgress>(() => {
    const directional = candidates.filter(
      (c) => c.direction === "Bullish" || c.direction === "Bearish"
    );
    const total = directional.length;
    const scanned = directional.filter((c) => typeof c.fa_score === "number").length;
    const recent = timestamp
      ? Date.now() - new Date(timestamp).getTime() < FA_FRESH_MS
      : false;
    return { active: total > 0 && scanned < total && recent, scanned, total };
  }, [candidates, timestamp]);

  // Keep the latest active flag readable inside the self-scheduling poll closure.
  const activeRef = useRef(false);
  activeRef.current = faProgress.active;

  useEffect(() => {
    fetchCandidates(); // initial load shows the skeleton
    // Self-scheduling poll: ~30s while FA is landing (so the badge updates live),
    // 5 min when idle. Silent = no blink.
    let timer: ReturnType<typeof setTimeout>;
    const schedule = () => {
      const delay = activeRef.current ? POLL_ACTIVE_MS : POLL_IDLE_MS;
      timer = setTimeout(async () => {
        await fetchCandidates({ silent: true });
        schedule();
      }, delay);
    };
    schedule();
    return () => clearTimeout(timer);
  }, [fetchCandidates]);

  return {
    candidates,
    loading,
    error,
    timestamp,
    faProgress,
    refetch: () => fetchCandidates({ silent: true }),
  };
}
