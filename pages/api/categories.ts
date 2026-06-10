import { NextApiRequest, NextApiResponse } from 'next';

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
 * Returns latest category momentum scores from Supabase via REST API.
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

    // Call Supabase REST API
    const response = await fetch(
      `${supabaseUrl}/rest/v1/categories?order=momentum_score.desc`,
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

    const categories: Category[] = await response.json();

    const last_updated =
      categories.length > 0
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
  }
}
