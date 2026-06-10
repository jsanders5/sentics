import { NextApiRequest, NextApiResponse } from 'next';

type ResponseData = {
  status: string;
  run_id?: string;
  message?: string;
  error?: string;
};

/**
 * POST /api/run-pipeline
 *
 * Proxy to the Python agent pipeline service.
 *
 * Query params:
 * - trigger_type: "scheduled" | "manual" (default: "manual")
 */
export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<ResponseData>
) {
  if (req.method !== 'POST' && req.method !== 'OPTIONS') {
    return res.status(405).json({ status: 'error', error: 'Method not allowed' });
  }

  if (req.method === 'OPTIONS') {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
    return res.status(200).end();
  }

  try {
    const { trigger_type = 'manual' } = req.query;
    const agentsUrl = process.env.AGENTS_SERVICE_URL;

    if (!agentsUrl) {
      return res.status(500).json({
        status: 'error',
        error: 'Agents service URL not configured',
      });
    }

    // Call the Python agents service
    const response = await fetch(
      `${agentsUrl}/api/run-pipeline?trigger_type=${encodeURIComponent(trigger_type as string)}`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    const data = await response.json();

    return res.status(response.status).json(data);
  } catch (error) {
    console.error('Pipeline proxy error:', error);
    return res.status(500).json({
      status: 'error',
      error: error instanceof Error ? error.message : 'Unknown error',
    });
  }
}
