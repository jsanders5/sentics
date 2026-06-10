import { NextApiRequest, NextApiResponse } from 'next';

type Candidate = {
  symbol: string;
  name: string;
  category: string;
  price: number;
  time_horizon: string;
  confidence_tier: string;
  score: number;
  rationale: string;
  entry_type: string;
  entry_quality: string;
  updated_at: string;
};

type ResponseData = {
  status: string;
  candidates?: Candidate[];
  count?: number;
  last_updated?: string;
  error?: string;
};

/**
 * GET /api/candidates
 *
 * Returns latest candidates from Supabase via REST API.
 *
 * Query params:
 * - limit: number (default: 50)
 * - category: string (filter by category, optional)
 * - time_horizon: string (Short|Medium|Long, optional)
 * - confidence: string (High|Medium|Low, optional)
 */
export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<ResponseData>
) {
  if (req.method !== 'GET') {
    return res.status(405).json({ status: 'error', error: 'Method not allowed' });
  }

  try {
    const supabaseUrl = process.env.SUPABASE_URL;
    const supabaseKey = process.env.SUPABASE_SECRET_KEY;

    if (!supabaseUrl || !supabaseKey) {
      return res.status(500).json({
        status: 'error',
        error: 'Supabase configuration missing',
      });
    }

    const limit = parseInt((req.query.limit as string) || '50', 10);
    const category = req.query.category as string | undefined;
    const time_horizon = req.query.time_horizon as string | undefined;
    const confidence = req.query.confidence as string | undefined;

    // Build query string
    let queryStr = `order=score.desc&limit=${limit}`;

    if (category) {
      queryStr += `&category=eq.${encodeURIComponent(category)}`;
    }

    if (time_horizon) {
      queryStr += `&time_horizon=eq.${encodeURIComponent(time_horizon)}`;
    }

    if (confidence) {
      queryStr += `&confidence_tier=eq.${encodeURIComponent(confidence)}`;
    }

    // Call Supabase REST API
    const response = await fetch(
      `${supabaseUrl}/rest/v1/candidates?${queryStr}`,
      {
        method: 'GET',
        headers: {
          apikey: supabaseKey,
          Authorization: `Bearer ${supabaseKey}`,
        },
      }
    );

    if (!response.ok) {
      const error = await response.text();
      console.error('Supabase error:', error);
      return res.status(response.status).json({
        status: 'error',
        error: `Supabase API error: ${response.status}`,
      });
    }

    const candidates: Candidate[] = await response.json();

    const last_updated =
      candidates.length > 0
        ? candidates[0].updated_at
        : new Date().toISOString();

    return res.status(200).json({
      status: 'success',
      candidates,
      count: candidates.length,
      last_updated,
    });
  } catch (error) {
    console.error('Candidates query error:', error);
    return res.status(500).json({
      status: 'error',
      error: error instanceof Error ? error.message : 'Unknown error',
    });
  }
}
