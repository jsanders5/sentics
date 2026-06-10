import { NextApiRequest, NextApiResponse } from 'next';
import { Pool } from 'pg';

type Category = {
  name: string;
  momentum_score: number;
  macro_adjustment: number;
  updated_at: string;
};

type ResponseData = {
  status: string;
  categories?: Category[];
  count?: number;
  last_updated?: string;
  error?: string;
};

/**
 * GET /api/categories
 *
 * Returns latest category momentum scores from database.
 *
 * Response:
 * {
 *   "status": "success",
 *   "categories": [
 *     {
 *       "name": "Layer 1",
 *       "momentum_score": 72.5,
 *       "macro_adjustment": -5,
 *       "updated_at": "2026-06-10T15:02:30Z"
 *     },
 *     ...
 *   ],
 *   "count": 12,
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
    const result = await pool.query(
      'SELECT name, momentum_score, macro_adjustment, updated_at FROM categories ORDER BY momentum_score DESC'
    );

    const categories: Category[] = result.rows.map((row) => ({
      name: row.name,
      momentum_score: parseFloat(row.momentum_score),
      macro_adjustment: parseFloat(row.macro_adjustment || 0),
      updated_at: row.updated_at.toISOString(),
    }));

    // Get last updated timestamp
    const last_updated = categories.length > 0
      ? categories[0].updated_at
      : new Date().toISOString();

    return res.status(200).json({
      status: 'success',
      categories,
      count: categories.length,
      last_updated,
    });
  } catch (error) {
    console.error('Categories query error:', error);
    return res.status(500).json({
      status: 'error',
      error: error instanceof Error ? error.message : 'Unknown error',
    });
  } finally {
    await pool.end();
  }
}
