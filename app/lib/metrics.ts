// Single source of truth for every number/KPI the app displays. Feeds both the
// inline tooltips and the /glossary page, so definitions never drift.

export type MetricGroup = "Technical" | "Trade levels" | "Social" | "Market";

export interface MetricDef {
  key: string;
  label: string;
  group: MetricGroup;
  scale?: string;   // range / units
  source: string;   // where the number comes from
  short: string;    // tooltip (1 sentence)
  full: string;     // glossary definition
  caveat?: string;  // honest limitation
}

export const METRICS: MetricDef[] = [
  // ── Technical (Sentics) ──────────────────────────────────────────────
  {
    key: "signal_strength",
    label: "Signal strength",
    group: "Technical",
    scale: "0–100",
    source: "Sentics (technical)",
    short: "How strongly the technical indicators currently agree on the direction — a description of the indicators, not a forecast or recommendation.",
    full: "A 0–100 measure of how strongly the technical indicators (trend, momentum, RSI) agree on the current directional read. Higher means more agreement, up or down.",
    caveat: "It describes the indicators; it does not predict returns. Backtests show it does not rank forward performance.",
  },
  {
    key: "direction",
    label: "Direction",
    group: "Technical",
    scale: "Bullish / Bearish / Neutral",
    source: "Sentics (technical)",
    short: "The technical read of the current trend and momentum — not a call to buy or sell.",
    full: "The direction the technical model currently reads from price: Bullish (up), Bearish (down), or Neutral (no clear directional signal).",
    caveat: "A reading of past price, not a prediction. It has no demonstrated timing edge.",
  },
  {
    key: "confidence",
    label: "Confidence",
    group: "Technical",
    scale: "High / Medium / Low",
    source: "Sentics (technical)",
    short: "How many of the technical indicators agree with each other (breadth of agreement).",
    full: "How broadly the individual indicators agree. High = most indicators point the same way; Low = they conflict. Distinct from signal strength (how strong the agreement is).",
  },
  {
    key: "horizon",
    label: "Time horizon",
    group: "Technical",
    scale: "Short / Medium / Long",
    source: "Sentics (technical)",
    short: "The rough timeframe the technical read is oriented to (Short ≈ days, Medium ≈ weeks, Long ≈ months).",
    full: "The timeframe the technical read is oriented to, inferred from volatility and trend persistence: Short (~days), Medium (~weeks), Long (~months).",
  },
  {
    key: "technical_strength",
    label: "Technical strength",
    group: "Technical",
    scale: "0–58",
    source: "Sentics (technical)",
    short: "Direction-agnostic setup quality: how clean and well-confirmed the move is, bull or bear.",
    full: "A direction-agnostic score of setup quality built from trend cleanliness, momentum, and volume confirmation. Says nothing about which way — only how well-formed the move is.",
  },
  {
    key: "rsi",
    label: "RSI (14d)",
    group: "Technical",
    scale: "0–100",
    source: "Sentics (from CoinGecko prices)",
    short: "Wilder's 14-day Relative Strength Index — momentum oscillator; >70 often 'overbought', <30 'oversold'.",
    full: "The 14-day Relative Strength Index (Wilder's method) over daily closes. A momentum oscillator: readings above ~70 are often called overbought, below ~30 oversold — though these persist in strong trends.",
  },
  {
    key: "volume_ratio",
    label: "Volume ratio",
    group: "Technical",
    scale: "× (multiple)",
    source: "Sentics (from CoinGecko)",
    short: "Recent trading volume vs its own recent average — above 1× means heavier-than-usual activity.",
    full: "Recent trading volume divided by its trailing average. 1× is average; higher means unusually active trading, which can confirm a move.",
  },

  // ── Trade levels (illustrative) ──────────────────────────────────────
  {
    key: "trade_levels",
    label: "Technical levels (entry / target / stop)",
    group: "Trade levels",
    source: "Sentics (technical)",
    short: "Illustrative price levels derived from recent structure (moving averages, swing highs/lows) — not predictions or advice.",
    full: "Entry, target, and stop levels derived from recent price structure (moving averages, swing highs/lows) with a volatility floor. They illustrate where a technical setup would trigger, aim, and invalidate.",
    caveat: "Illustrative outputs of an automated model — not predictions, recommendations, or advice. They frequently fail.",
  },
  {
    key: "risk_reward",
    label: "Reward-to-risk (R/R)",
    group: "Trade levels",
    scale: "ratio (capped at 5+)",
    source: "Sentics (technical)",
    short: "Distance to the target divided by distance to the stop. Higher = more potential reward per unit of risk — if the levels hold.",
    full: "The distance from entry to target divided by the distance from entry to stop. A 3.0 means the target is three times as far as the stop. Assumes the illustrative levels hold, which they often don't.",
  },

  // ── Market (CoinGecko) ───────────────────────────────────────────────
  {
    key: "price",
    label: "Price",
    group: "Market",
    scale: "USD",
    source: "CoinGecko",
    short: "Latest USD price from CoinGecko.",
    full: "The most recent USD spot price from CoinGecko at the time of the run.",
  },
  {
    key: "market_cap",
    label: "Market cap",
    group: "Market",
    scale: "USD",
    source: "CoinGecko",
    short: "Circulating supply × price — the coin's total market value; the basis for the top-25 universe.",
    full: "Circulating supply multiplied by price. The main screener universe is the top 25 non-stablecoins by market cap.",
  },

  // ── Social (LunarCrush) ──────────────────────────────────────────────
  {
    key: "sentiment",
    label: "Sentiment",
    group: "Social",
    scale: "0–100 (≈50 neutral)",
    source: "LunarCrush",
    short: "Share of recent social posts scored positive (0–100, ~50 neutral). Descriptive context, not a signal.",
    full: "LunarCrush's aggregate social sentiment: the share of recent posts about the coin scored positive, on a 0–100 scale where ~50 is neutral.",
    caveat: "Social sentiment is noisy, often lagging, and can be manipulated by bots or coordinated posting.",
  },
  {
    key: "galaxy_score",
    label: "Galaxy Score",
    group: "Social",
    scale: "0–100",
    source: "LunarCrush",
    short: "LunarCrush's composite of price performance + social activity (0–100). An opaque blend — shown as context, not a rating to trade on.",
    full: "A proprietary LunarCrush composite (0–100) blending price performance, social volume, and market activity into a single 'health' score.",
    caveat: "An opaque composite we have not validated. Do not treat it as a buy/sell rating.",
  },
  {
    key: "galaxy_delta",
    label: "Galaxy Δ",
    group: "Social",
    scale: "points",
    source: "LunarCrush",
    short: "Change in Galaxy Score since the previous reading (▲ rising, ▼ falling).",
    full: "The change in Galaxy Score versus the previous reading — the velocity of the composite, which is often more meaningful than the level.",
  },
  {
    key: "alt_rank",
    label: "AltRank",
    group: "Social",
    scale: "1 = hottest",
    source: "LunarCrush",
    short: "LunarCrush's combined price-performance + social ranking across all assets. Lower = 'hotter'. Powers the Trending tab.",
    full: "A ranking (1 = best) that combines a coin's recent price performance with its social activity relative to all other assets. Lower means it's outperforming and buzzing.",
    caveat: "Ranks attention + momentum, which skews toward small, volatile, manipulation-prone coins.",
  },
  {
    key: "alt_rank_delta",
    label: "AltRank Δ",
    group: "Social",
    scale: "positions",
    source: "LunarCrush",
    short: "Change in AltRank since the previous reading — positive means it climbed the ranking.",
    full: "How many positions the coin moved in AltRank versus the previous reading. Positive = improving (climbing toward #1).",
  },
  {
    key: "social_dominance",
    label: "Social dominance",
    group: "Social",
    scale: "%",
    source: "LunarCrush",
    short: "This coin's share of all crypto social volume — how much of the conversation it's capturing.",
    full: "The percentage of all crypto-related social volume that is about this coin — its share of the overall conversation.",
  },
  {
    key: "social_volume_24h",
    label: "Social volume (24h)",
    group: "Social",
    scale: "count",
    source: "LunarCrush",
    short: "Number of social posts about the coin in the last 24 hours.",
    full: "The count of unique social posts (X, Reddit, YouTube, TikTok, news, etc.) mentioning the coin over the last 24 hours.",
  },
  {
    key: "interactions_24h",
    label: "Interactions (24h)",
    group: "Social",
    scale: "count",
    source: "LunarCrush",
    short: "Total engagement (likes, replies, shares, views) on those posts in the last 24 hours.",
    full: "Total engagement — likes, replies, reposts, views — across posts about the coin in the last 24 hours. A measure of reach, not just post count.",
  },
  {
    key: "platform_sentiment",
    label: "Sentiment by platform",
    group: "Social",
    scale: "0–100 per platform",
    source: "LunarCrush",
    short: "Sentiment broken out by platform (news, X, Reddit, YouTube…). Divergence — e.g. bullish social but neutral news — is itself informative.",
    full: "The sentiment score (0–100) computed separately for each platform. Comparing them shows where the mood is coming from; social euphoria with neutral/negative news is a common caution pattern.",
  },
  {
    key: "post_sentiment",
    label: "Post/article sentiment",
    group: "Social",
    scale: "1–5 (3 neutral)",
    source: "LunarCrush",
    short: "Per-item sentiment on an individual news article or post, 1–5 (3 ≈ neutral). Shown as a colored dot.",
    full: "The sentiment of a single news article or social post on a 1–5 scale where 3 is neutral. Rendered as a green/red dot next to each item in the evidence list.",
  },
  {
    key: "social_trend",
    label: "Social trend",
    group: "Social",
    scale: "up / down",
    source: "LunarCrush",
    short: "LunarCrush's read on whether social activity for the coin is rising or falling.",
    full: "LunarCrush's directional read on the coin's social activity — whether the volume of conversation is trending up or down.",
  },
  {
    key: "contrarian_tilt",
    label: "Contrarian social tilt",
    group: "Social",
    scale: "± conviction points",
    source: "Sentics (from LunarCrush)",
    short: "A small contrarian adjustment: coins hotter than the universe on social get slightly LOWER conviction (hyped coins have historically underperformed ~1–4 weeks).",
    full: "The one social effect that survived out-of-sample backtesting was contrarian: coins with high sentiment relative to the universe underperformed over the next 1–4 weeks. So Sentics applies a small tilt — high relative social 'heat' slightly reduces bullish conviction (and nudges bearish) — based on each coin's sentiment z-score across the current set. It never flips the technical direction.",
    caveat: "Experimental and calibrated on a single year; modest effect, being validated live via the call ledger. Not a signal to trade on.",
  },
];

export const metricsByKey: Record<string, MetricDef> = Object.fromEntries(
  METRICS.map((m) => [m.key, m])
);

/** Tooltip helper: the short definition for a metric key (empty string if unknown). */
export function tip(key: string): string {
  return metricsByKey[key]?.short ?? "";
}
