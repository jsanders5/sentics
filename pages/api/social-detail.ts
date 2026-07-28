import { NextApiRequest, NextApiResponse } from "next";

/**
 * GET /api/social-detail?topic=<lunarcrush topic>
 *
 * Lazy-loaded evidence behind a coin's sentiment: platform sentiment breakdown +
 * top news + top social posts. Proxies LunarCrush server-side (keeps the key off
 * the client, avoids CORS). Needs LUNARCRUSH_API_KEY in the env.
 */
const BASE = "https://lunarcrush.com/api4/public";
const UA = "Mozilla/5.0 (compatible; sentics/1.0)";

// `path` must already be URL-safe (encode dynamic segments at the call site) —
// encoding the whole path would escape the slashes and 404.
async function lc(path: string, key: string) {
  const r = await fetch(`${BASE}/${path}`, {
    headers: { Authorization: `Bearer ${key}`, "User-Agent": UA },
  });
  if (!r.ok) throw new Error(`LunarCrush ${path} → ${r.status}`);
  const body = await r.json();
  return body?.data ?? body;
}

function clean(items: unknown, n: number) {
  if (!Array.isArray(items)) return [];
  return items.slice(0, n).map((it: Record<string, unknown>) => ({
    title: it.post_title,
    link: it.post_link,
    type: it.post_type,
    sentiment: it.post_sentiment,
    creator: it.creator_display_name || it.creator_name,
    interactions: it.interactions_24h,
  }));
}

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  if (req.method !== "GET") {
    return res.status(405).json({ error: "Method not allowed" });
  }
  const topic = (req.query.topic as string || "").trim();
  if (!topic) return res.status(400).json({ error: "topic required" });

  const key = process.env.LUNARCRUSH_API_KEY;
  if (!key) return res.status(200).json({ unavailable: true });

  const t = encodeURIComponent(topic); // encode ONLY the topic segment (may contain spaces)
  try {
    const [detail, news, posts] = await Promise.all([
      lc(`topic/${t}/v1`, key).catch(() => ({})),
      lc(`topic/${t}/news/v1`, key).catch(() => []),
      lc(`topic/${t}/posts/v1`, key).catch(() => []),
    ]);
    return res.status(200).json({
      trend: detail?.trend,
      num_posts: detail?.num_posts,
      num_contributors: detail?.num_contributors,
      types_sentiment: detail?.types_sentiment,
      news: clean(news, 6),
      posts: clean(posts, 6),
    });
  } catch (e) {
    console.error("[social-detail]", e);
    return res.status(200).json({ error: "fetch failed" });
  }
}
