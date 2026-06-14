import { NextApiRequest, NextApiResponse } from 'next';

type Candidate = {
  symbol: string;
  name: string;
  category: string;
  market_cap?: number;
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

    const rows: any[] = await response.json();

    // Real data freshness = most recent row update time (not request time),
    // so the dashboard's "Updated Xh ago" / staleness banner are honest.
    const updatedTimes = rows
      .map((c) => (c.updated_at ? new Date(c.updated_at).getTime() : NaN))
      .filter((t) => !Number.isNaN(t));
    const dataTimestamp = updatedTimes.length
      ? new Date(Math.max(...updatedTimes)).toISOString()
      : null;

    // Map database fields to frontend schema
    let candidates: any[] = rows.map((c) => ({
      symbol: c.symbol,
      name: c.name,
      category: c.category,
      market_cap: typeof c.market_cap === 'number' ? c.market_cap : 0,
      price: typeof c.price === 'number' && c.price > 0 ? c.price : 0,
      rsi: typeof c.rsi === 'number' ? c.rsi : 0,
      volume_ratio: typeof c.volume_ratio === 'number' ? c.volume_ratio : 0,
      technical_score: typeof c.technical_score === 'number' ? c.technical_score : 0,
      category_momentum: typeof c.category_momentum === 'number' ? c.category_momentum : 0,
      candidate_score: typeof c.score === 'number' ? c.score : 0,
      direction: c.direction,
      time_horizon: c.time_horizon,
      confidence_tier: c.confidence_tier,
      rationale: c.rationale,
      entry_type: c.entry_type,
      entry_quality: c.entry_quality,
      key_signals: c.key_signals,
      trade_plan: c.trade_plan,
    }));

    return res.status(200).json({
      status: 'success',
      candidates: candidates || [],
      timestamp: dataTimestamp ?? undefined,
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
