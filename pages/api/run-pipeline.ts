import { NextApiRequest, NextApiResponse } from "next";

type ResponseData = {
  status: string;
  message?: string;
  run_id?: string;
  error?: string;
};

/**
 * GET | POST /api/run-pipeline
 *
 * Fire-and-forget proxy: dispatches the backend pipeline (Stage 1) and returns
 * immediately, rather than waiting for the long run to finish (which timed the
 * client out before). The backend persists a freshness floor early and the FA
 * stage self-chains; the UI polls /api/candidates to reflect progress.
 *
 * Accepts BOTH methods on purpose: Vercel cron jobs invoke the path with a GET
 * (the daily scheduled run), while the dashboard Refresh button sends a POST.
 * Rejecting GET here is what silently broke the scheduled run.
 */
export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<ResponseData>
) {
  if (req.method !== "POST" && req.method !== "GET") {
    return res.status(405).json({ status: "error", error: "Method not allowed" });
  }

  // Honor the cron's ?trigger_type=scheduled; default to "manual" for the UI button.
  const triggerType =
    typeof req.query.trigger_type === "string" ? req.query.trigger_type : "manual";

  const backend =
    process.env.AGENTS_API_URL?.replace(/\/$/, "") || "https://sentics-agents.vercel.app";

  // Dispatch the run but don't wait for it to complete. We allow a few seconds to
  // ensure the request reaches the backend (so the function is invoked), then
  // abort the wait — the backend keeps running independently.
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 4000);
  try {
    await fetch(`${backend}/api/run-pipeline?trigger_type=${encodeURIComponent(triggerType)}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      signal: controller.signal,
    });
  } catch (err) {
    // AbortError is expected (we stopped waiting); anything else we log but still
    // report "started" because the request was very likely dispatched.
    if (!(err instanceof Error && err.name === "AbortError")) {
      console.error("[run-pipeline proxy] dispatch note:", err);
    }
  } finally {
    clearTimeout(timer);
  }

  return res.status(202).json({
    status: "started",
    message: "Pipeline started. Data will refresh as it completes.",
  });
}
