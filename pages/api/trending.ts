import { NextApiRequest, NextApiResponse } from "next";

/**
 * GET /api/trending
 *
 * Discovery list ranked by LunarCrush AltRank (price + social composite; lower =
 * hotter), excluding stablecoins and dust. Descriptive only — NOT the main
 * screener universe. Proxies LunarCrush server-side. Needs LUNARCRUSH_API_KEY.
 */
const URL = "https://lunarcrush.com/api4/public/coins/list/v2";
const UA = "Mozilla/5.0 (compatible; sentics/1.0)";
const STABLE = new Set([
  "USDT", "USDC", "DAI", "FDUSD", "TUSD", "USDE", "USDS", "PYUSD", "BUSD",
  "GUSD", "USDP", "FRAX", "LUSD",
]);

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== "GET") return res.status(405).json({ error: "Method not allowed" });
  const key = process.env.LUNARCRUSH_API_KEY;
  if (!key) return res.status(200).json({ coins: [], unavailable: true });

  const limit = Math.min(parseInt((req.query.limit as string) || "25", 10), 100);
  try {
    const r = await fetch(URL, { headers: { Authorization: `Bearer ${key}`, "User-Agent": UA } });
    if (!r.ok) throw new Error(`LunarCrush ${r.status}`);
    const rows: Record<string, unknown>[] = (await r.json())?.data ?? [];

    const coins = rows
      .filter((c) => {
        const s = String(c.symbol || "").toUpperCase();
        return s && !STABLE.has(s) && c.alt_rank && (Number(c.market_cap) || 0) > 1e7;
      })
      .sort((a, b) => Number(a.alt_rank) - Number(b.alt_rank))
      .slice(0, limit)
      .map((c) => ({
        symbol: String(c.symbol).toUpperCase(),
        name: c.name,
        price: c.price,
        market_cap: c.market_cap,
        percent_change_24h: c.percent_change_24h,
        alt_rank: c.alt_rank,
        alt_rank_delta:
          c.alt_rank != null && c.alt_rank_previous != null
            ? Number(c.alt_rank_previous) - Number(c.alt_rank)
            : undefined,
        galaxy_score: c.galaxy_score,
        sentiment: c.sentiment,
        social_dominance: c.social_dominance,
        social_volume_24h: c.social_volume_24h,
        logo: c.logo,
      }));

    return res.status(200).json({ coins });
  } catch (e) {
    console.error("[trending]", e);
    return res.status(200).json({ coins: [], error: "fetch failed" });
  }
}
