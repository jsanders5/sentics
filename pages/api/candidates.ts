import { NextApiRequest, NextApiResponse } from 'next';
import { Pool } from 'pg';

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
 * Returns latest candidates from database.
 *
 * Query params:
 * - limit: number (default: 50)
 * - category: string (filter by category, optional)
 * - time_horizon: string (Short|Medium|Long, optional)
 * - confidence: string (High|Medium|Low, optional)
 *
 * Response:
 * {
 *   "status": "success",
 *   "candidates": [...],
 *   "count": 47,
 *   "last_updated": "2026-06-10T15:02:30Z"
 * }
 */
export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<ResponseData>
) {
  // Only allow GET
  if (req.method !== 'GET') {
    return res.status(405).json({ status: 'error', error: 'Method not allowed' });
  }

  const pool = new Pool({
    connectionString: process.env.DATABASE_URL,
  });

  try {
    const limit = parseInt((req.query.limit as string) || '50', 10);
    const category = req.query.category as string | undefined;
    const time_horizon = req.query.time_horizon as string | undefined;
    const confidence = req.query.confidence as string | undefined;

    // Build query
    let query = 'SELECT * FROM candidates WHERE 1=1';
    const params: any[] = [];
    let paramIndex = 1;

    if (category) {
      query += ` AND category = $${paramIndex++}`;
      params.push(category);
    }

    if (time_horizon) {
      query += ` AND time_horizon = $${paramIndex++}`;
      params.push(time_horizon);
    }

    if (confidence) {
      query += ` AND confidence_tier = $${paramIndex++}`;
      params.push(confidence);
    }

    query += ` ORDER BY score DESC LIMIT $${paramIndex++}`;
    params.push(limit);

    const result = await pool.query(query, params);
    const candidates: Candidate[] = result.rows;

    // Get last updated timestamp
    const tsResult = await pool.query('SELECT MAX(updated_at) as last_updated FROM candidates');
    const last_updated = tsResult.rows[0]?.last_updated?.toISOString() || new Date().toISOString();

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
  } finally {
    await pool.end();
  }
}
