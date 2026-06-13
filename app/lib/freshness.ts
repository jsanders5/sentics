// Shared helpers for communicating data freshness honestly.
// The pipeline runs once daily (15:00 UTC cron) — this is NOT real-time data.

export const STALE_HOURS = 7;

export function getHoursAgo(iso?: string | null): number | null {
  if (!iso) return null;
  const t = new Date(iso).getTime();
  if (Number.isNaN(t)) return null;
  return (Date.now() - t) / 3_600_000;
}

export function formatAgo(iso?: string | null): string {
  const h = getHoursAgo(iso);
  if (h === null) return "No data yet";
  if (h < 1) {
    const m = Math.max(1, Math.round(h * 60));
    return `Updated ${m}m ago`;
  }
  if (h < 24) return `Updated ${Math.round(h)}h ago`;
  const d = Math.round(h / 24);
  return `Updated ${d}d ago`;
}

export function isStale(iso?: string | null): boolean {
  const h = getHoursAgo(iso);
  return h !== null && h >= STALE_HOURS;
}
