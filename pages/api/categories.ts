import { NextApiRequest, NextApiResponse } from 'next';

type Category = {
  name: string;
  momentum_score: number;
  macro_adjustment: number;
  updated_at?: string;
};

type ResponseData = {
  status: string;
  categories?: Category[];
  error?: string;
};

/**
 * GET /api/categories
 *
 * Returns latest category momentum scores from Supabase or empty list.
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
      // Return empty categories if Supabase not configured
      return res.status(200).json({
        status: 'success',
        categories: [],
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
          'Content-Type': 'application/json',
        },
      }
    );

    if (!response.ok) {
      const error = await response.text();
      console.error('Supabase error:', error);
      return res.status(200).json({
        status: 'success',
        categories: [],
      });
    }

    const categories: Category[] = await response.json();

    return res.status(200).json({
      status: 'success',
      categories: categories || [],
    });
  } catch (error) {
    console.error('Categories query error:', error);
    return res.status(200).json({
      status: 'success',
      categories: [],
    });
  }
}
