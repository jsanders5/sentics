import { NextApiRequest, NextApiResponse } from 'next';

type Candidate = {
  symbol: string;
  name: string;
  category: string;
  price: number;
  rsi: number;
  volume_ratio: number;
  technical_score: number;
  category_momentum: number;
  candidate_score: number;
  time_horizon?: string;
  confidence_tier?: string;
  rationale?: string;
  entry_type?: string;
  entry_quality?: string;
  key_signals?: string[];
  updated_at?: string;
};

type ResponseData = {
  status: string;
  candidates?: Candidate[];
  timestamp?: string;
  error?: string;
};

/**
 * GET /api/candidates
 *
 * Returns latest candidates from Supabase or mock data.
 *
 * Query params:
 * - limit: number (default: 50)
 * - category: string (filter by category, optional)
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
      // Return empty candidates if Supabase not configured
      return res.status(200).json({
        status: 'success',
        candidates: [],
        timestamp: new Date().toISOString(),
      });
    }

    const limit = parseInt((req.query.limit as string) || '50', 10);
    const category = req.query.category as string | undefined;
    const confidence = req.query.confidence as string | undefined;

    // Build query string
    let queryStr = `order=score.desc&limit=${limit}`;

    if (category && category !== 'All') {
      queryStr += `&category=eq.${encodeURIComponent(category)}`;
    }

    if (confidence && confidence !== 'All') {
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
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      const error = await response.text();
      console.error('Supabase error:', error);
      return res.status(200).json({
        status: 'success',
        candidates: [],
        timestamp: new Date().toISOString(),
      });
    }

    const candidates: Candidate[] = await response.json();

    return res.status(200).json({
      status: 'success',
      candidates: candidates || [],
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error('Candidates query error:', error);
    return res.status(200).json({
      status: 'success',
      candidates: [],
      timestamp: new Date().toISOString(),
    });
  }
}
