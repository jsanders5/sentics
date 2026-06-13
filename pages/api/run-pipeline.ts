import { NextApiRequest, NextApiResponse } from "next";

type ResponseData = {
  status: string;
  message?: string;
  run_id?: string;
  error?: string;
};

/**
 * POST /api/run-pipeline
 *
 * Same-origin proxy that triggers the Python agent pipeline on the backend
 * (sentics-agents). Keeps the backend URL server-side and avoids browser CORS.
 *
 * The pipeline is long-running (CoinGecko + Claude calls), so this can take a
 * while; the client should show a pending state.
 */
export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<ResponseData>
) {
  if (req.method !== "POST") {
    return res.status(405).json({ status: "error", error: "Method not allowed" });
  }

  const backend =
    process.env.AGENTS_API_URL?.replace(/\/$/, "") || "https://sentics-agents.vercel.app";

  try {
    const upstream = await fetch(`${backend}/api/run-pipeline?trigger_type=manual`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    });

    const data = await upstream.json().catch(() => ({}));

    if (!upstream.ok) {
      return res.status(upstream.status).json({
        status: "error",
        error: data?.error || `Pipeline backend returned ${upstream.status}`,
      });
    }

    return res.status(200).json({
      status: data?.status || "success",
      message: data?.message,
      run_id: data?.run_id,
    });
  } catch (err) {
    const msg = err instanceof Error ? err.message : "Failed to reach pipeline backend";
    console.error("[run-pipeline proxy] error:", msg);
    return res.status(502).json({ status: "error", error: msg });
  }
}
