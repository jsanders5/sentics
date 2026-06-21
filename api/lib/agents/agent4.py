"""
Agent 4: Fundamental Analysis — news / catalyst layer.

For each candidate, fetches recent headlines from a cheap crypto news API
(CryptoPanic, free tier) and has a small/cheap model classify them into a
structured catalyst read: net sentiment, magnitude, a catalyst label, a short
summary, and sources. Produces `fa_score = sentiment * magnitude` in [-1, +1],
which the pipeline BLENDS with the TA directional score.

News source: free, keyless crypto-news RSS feeds (the API free tiers — CryptoPanic,
CryptoCompare, CoinDesk Data — now all require paid keys; RSS doesn't get
discontinued the same way). We fetch the feeds ONCE per run, then filter the
combined items per coin by name/symbol. A cheap model classifies the matches. This
removes the web_search per-search fee (~$5/run) entirely. Swap sources by editing
RSS_FEEDS / fetch_news_feed().

Point-in-time integrity (accumulate-forward): headlines are read AT RUN TIME and
frozen into a daily snapshot — the leak-free record the FA backtest replays.

Design choices:
  - Concurrent, with graceful degradation: no key / no headlines / any failure →
    neutral FA (fa_score 0); never drops the candidate or breaks the pipeline. If
    a coin has no headlines we skip the model call entirely (zero cost).
  - Conservative blend: FA modulates CONVICTION (agreement strengthens, opposition
    weakens) but does NOT flip the TA-derived direction — keeps the trade plan
    consistent. Signed `combined_score` is stored for a future calibrated blend.
"""

import os
import json
import re
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional

import anthropic
import requests

from .utils import log_info, log_error, cache_get, cache_set
from .agent2 import compute_candidate_score

# Headline classification is a simple task → default to a cheap model (override
# with AGENT4_MODEL, e.g. claude-sonnet-4-6 for higher quality).
AGENT4_MODEL = os.getenv("AGENT4_MODEL", "claude-haiku-4-5")
MAX_WORKERS = 4
MAX_TOKENS = 1024
NEWS_LIMIT = 8
HTTP_UA = "Mozilla/5.0 (compatible; sentics-bot/1.0)"

# Free, keyless crypto-news RSS feeds. Override with AGENT4_RSS_FEEDS (comma-sep).
RSS_FEEDS = [
    "https://cointelegraph.com/rss",
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://decrypt.co/feed",
    "https://cryptoslate.com/feed/",
]

# Conservative, UN-CALIBRATED weight: how much a full-strength catalyst (|fa_score|=1)
# adds to / subtracts from the TA magnitude (~[20,100]) when computing conviction.
# A future FA backtest (accumulate-forward) should calibrate this.
FA_WEIGHT = 25.0

# The FA stage runs across several self-chaining serverless invocations (one per
# batch). Caching the run's RSS snapshot in Redis on the first batch and reusing it
# for the rest means EVERY coin in a run is scored against the SAME headlines — so
# two coins referenced by one article (e.g. XLM and Canton in "From Stellar to
# Canton") both see it — and preserves point-in-time integrity. run_pipeline
# invalidates this key at the start of each run so every run fetches fresh.
FEED_CACHE_KEY = "fa:feed_snapshot"
FEED_CACHE_TTL_MIN = 30

NEUTRAL_FA = {
    "fa_score": 0.0, "sentiment": 0.0, "magnitude": 0.0, "catalyst": "none",
    "fa_confidence": "Low", "fa_summary": "No significant catalyst detected.",
    "fa_sources": [],
}


def _strip_html(s: str) -> str:
    return re.sub(r"<[^>]+>", " ", s or "").strip()


def fetch_news_feed() -> List[Dict]:
    """Fetch + parse all RSS feeds ONCE per run into a combined, deduped item list.
    Each item: {title, url, published_at, text, categories}. Returns [] on total
    failure (→ neutral FA). Swap RSS_FEEDS / this function to change sources."""
    feeds = os.getenv("AGENT4_RSS_FEEDS")
    feed_urls = [u.strip() for u in feeds.split(",")] if feeds else RSS_FEEDS
    items, seen = [], set()
    for url in feed_urls:
        try:
            resp = requests.get(url, headers={"User-Agent": HTTP_UA}, timeout=15)
            resp.raise_for_status()
            root = ET.fromstring(resp.content)
            for it in root.findall(".//item"):
                title = (it.findtext("title") or "").strip()
                link = (it.findtext("link") or "").strip()
                if not title or link in seen:
                    continue
                seen.add(link)
                desc = _strip_html(it.findtext("description") or "")
                cats = " ".join((c.text or "") for c in it.findall("category"))
                items.append({
                    "title": title, "url": link,
                    "published_at": (it.findtext("pubDate") or "").strip(),
                    "desc": desc,
                    "text": f"{title} {desc} {cats}",
                    "categories": cats,
                })
        except Exception as e:  # noqa: BLE001 — one bad feed shouldn't sink the rest
            log_error(f"RSS fetch failed for {url}", e)
    log_info(f"Fetched {len(items)} news items from {len(feed_urls)} feeds")
    return items


def get_feed_snapshot() -> List[Dict]:
    """Return the run's shared RSS snapshot, fetching + caching on first use so all
    FA batches in a run see the same headlines (see FEED_CACHE_KEY). Falls back to a
    direct fetch if Redis is unavailable."""
    cached = cache_get(FEED_CACHE_KEY)
    if cached and isinstance(cached.get("items"), list) and cached["items"]:
        log_info(f"Using cached news snapshot ({len(cached['items'])} items)")
        return cached["items"]
    feed = fetch_news_feed()
    if feed:
        cache_set(FEED_CACHE_KEY, {"items": feed}, ttl_minutes=FEED_CACHE_TTL_MIN)
    return feed


def headlines_for(symbol: str, name: str, feed: List[Dict], limit: int = NEWS_LIMIT) -> List[Dict]:
    """Filter the combined feed for items relevant to a coin: full name match
    (case-insensitive) or symbol as a standalone token (case-insensitive). Short
    tickers (≤2 chars, e.g. CC) collide with stray uppercase tokens in unrelated
    articles, so for those we require a full-name match and ignore bare-symbol
    matching. Each result carries the description snippet for the classifier."""
    name_l = (name or "").lower().strip()
    sym = (symbol or "").upper().strip()
    allow_sym = len(sym) >= 3
    sym_re = re.compile(rf"\b{re.escape(sym)}\b", re.IGNORECASE) if allow_sym else None
    out = []
    for it in feed:
        text = it["text"]
        name_hit = bool(name_l) and len(name_l) >= 3 and name_l in text.lower()
        sym_hit = bool(sym_re) and sym_re.search(text)
        if name_hit or sym_hit:
            out.append({
                "title": it["title"], "url": it["url"],
                "published_at": it["published_at"], "snippet": it.get("desc", ""),
            })
            if len(out) >= limit:
                break
    return out


def build_prompt(name: str, symbol: str, headlines: List[Dict]) -> str:
    parts = []
    for h in headlines:
        entry = f"- ({h.get('published_at','')}) {h.get('title','')}"
        snippet = (h.get("snippet", "") or "").strip()
        if snippet:
            entry += f"\n    {snippet[:300]}"
        parts.append(entry)
    lines = "\n".join(parts)
    return f"""Below are recent news headlines (with snippets) about the cryptocurrency {name} ({symbol}).
Assess their market-moving impact FOR {symbol} SPECIFICALLY.

Rules:
- Score sentiment from the perspective of {name} ({symbol}) as an asset — NOT the
  broader crypto market or another project mentioned in the story.
- A development that moves activity, partnerships, capital, or institutional support
  AWAY from {name} (e.g. a partner migrating off {symbol}, an institution choosing a
  competing chain) is BEARISH for {symbol}, even if it's bullish for crypto or
  tokenization in general. Read each snippet carefully to tell which side {symbol} is on.
- Base your assessment ONLY on these headlines/snippets — do not speculate or use
  prior knowledge. If they're routine or immaterial, say so (sentiment 0, catalyst "none").
- The `sentiment` number MUST agree with your `summary`: if the summary explains the
  news is negative for {symbol}, sentiment must be negative; if positive, positive.

HEADLINES:
{lines}

Respond with ONLY a JSON object — no prose before or after:
{{
  "sentiment": <number -1.0..1.0, net bullish(+) / bearish(-) impact FOR {symbol}>,
  "magnitude": <number 0.0..1.0, how market-moving the catalyst is>,
  "catalyst": "<short label, e.g. 'ETF flows', 'listing', 'hack', 'regulation', 'partnership', 'none'>",
  "confidence": "High|Medium|Low",
  "summary": "<1-2 sentences citing the specific catalyst and why it's bullish/bearish for {symbol}, or 'No significant catalyst.'>"
}}
"""


def _extract_text(message) -> Optional[str]:
    if getattr(message, "stop_reason", None) == "refusal":
        return None
    parts = [b.text for b in getattr(message, "content", []) or []
             if getattr(b, "type", None) == "text" and getattr(b, "text", None)]
    return "\n".join(parts) if parts else None


def parse_fa(text: str) -> Dict:
    """Parse + validate the JSON catalyst read; raises on unrecoverable garbage."""
    t = text.strip()
    if "```json" in t:
        t = t.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in t:
        t = t.split("```", 1)[1].split("```", 1)[0].strip()
    try:
        parsed = json.loads(t)
    except json.JSONDecodeError:
        m = re.search(r"\{.*\}", t, re.DOTALL)
        if not m:
            raise
        parsed = json.loads(m.group(0))

    sentiment = max(-1.0, min(1.0, float(parsed.get("sentiment", 0.0))))
    magnitude = max(0.0, min(1.0, float(parsed.get("magnitude", 0.0))))
    confidence = parsed.get("confidence")
    if confidence not in ("High", "Medium", "Low"):
        confidence = "Low"
    catalyst = str(parsed.get("catalyst", "none")) or "none"
    summary = str(parsed.get("summary", "")).strip() or "No significant catalyst."
    sources = parsed.get("sources")
    clean_sources = []
    if isinstance(sources, list):
        for s in sources[:5]:
            if isinstance(s, dict) and s.get("url"):
                clean_sources.append({"title": str(s.get("title", ""))[:200], "url": str(s["url"])[:500]})

    return {
        "fa_score": round(sentiment * magnitude, 4),
        "sentiment": round(sentiment, 4),
        "magnitude": round(magnitude, 4),
        "catalyst": catalyst,
        "fa_confidence": confidence,
        "fa_summary": summary,
        "fa_sources": clean_sources,
    }


def _classify(client: "anthropic.Anthropic", name: str, symbol: str, headlines: List[Dict]) -> Dict:
    """Classify provided headlines into a structured FA read (no web search).
    Returns NEUTRAL_FA on any failure — never raises."""
    try:
        message = client.messages.create(
            model=AGENT4_MODEL,
            max_tokens=MAX_TOKENS,
            messages=[{"role": "user", "content": build_prompt(name, symbol, headlines)}],
        )
        text = _extract_text(message)
        if not text:
            return dict(NEUTRAL_FA)
        fa = parse_fa(text)
        # Sources = the ACTUAL headlines we fed the model (the evidence base), not
        # the model's echoed list — consistent run-to-run, complete, and free of
        # hallucinated URLs (the model's `sources` field varied/dropped entries).
        fa["fa_sources"] = [
            {"title": h.get("title", "")[:200], "url": h.get("url", "")[:500]}
            for h in headlines[:3] if h.get("url")
        ]
        return fa
    except Exception as e:  # noqa: BLE001 — news layer must never break the pipeline
        log_error(f"FA classify failed for {symbol}", e)
        return dict(NEUTRAL_FA)


def combine_ta_fa(candidate: Dict) -> None:
    """Blend FA into the candidate IN PLACE. FA modulates conviction (agreement
    strengthens, opposition weakens) but does not flip the TA direction, so the
    trade plan stays consistent. Stores signed `combined_score` for the backtest."""
    ta = candidate.get("directional_score", 0.0) or 0.0
    fa = candidate.get("fa_score", 0.0) or 0.0
    candidate["combined_score"] = round(max(-100.0, min(100.0, ta + fa * FA_WEIGHT)), 2)

    direction = candidate.get("direction", "Neutral")
    if direction == "Neutral":
        return  # FA does not manufacture a directional call from nothing (conservative)

    ta_sign = 1.0 if direction == "Bullish" else -1.0
    aligned = fa * ta_sign  # >0 if the catalyst agrees with the TA direction
    adj_mag = max(0.0, min(100.0, abs(ta) + aligned * FA_WEIGHT))
    candidate["candidate_score"] = compute_candidate_score(
        direction, ta_sign * adj_mag, candidate.get("volume_ratio", 0.0),
        candidate.get("confidence_tier", "Medium"),
    )


def score_candidates(candidates: List[Dict]) -> List[Dict]:
    """FA-score + blend a list of candidate dicts (concurrent). Used by the chunked
    FA pipeline stage on a small batch loaded from the DB. Never raises; on a
    missing key or per-coin failure the coin gets neutral FA."""
    if not candidates:
        return []

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        log_error("ANTHROPIC_API_KEY not set; FA neutral for this batch")
        out = []
        for c in candidates:
            m = {**c, **NEUTRAL_FA}
            combine_ta_fa(m)
            out.append(m)
        return out

    client = anthropic.Anthropic(api_key=api_key, max_retries=3, timeout=120.0)
    feed = get_feed_snapshot()  # shared across ALL batches in the run (cached)

    def score(c):
        # Skip Neutral coins — nothing to enrich.
        if c.get("direction", "Neutral") == "Neutral":
            m = {**c, **NEUTRAL_FA}
            combine_ta_fa(m)
            return m
        headlines = headlines_for(c.get("symbol", "?"), c.get("name", ""), feed)
        if not headlines:
            fa = dict(NEUTRAL_FA)  # no matching news → neutral, no model call (free)
        else:
            fa = _classify(client, c.get("name", ""), c.get("symbol", "?"), headlines)
        m = {**c, **fa}
        combine_ta_fa(m)
        if fa["catalyst"] != "none" or fa["fa_score"] != 0.0:
            log_info(f"  {c.get('symbol')}: catalyst={fa['catalyst']} fa_score={fa['fa_score']:+.2f}")
        return m

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        return list(ex.map(score, candidates))


def run(agent2_result: Dict) -> Dict:
    """Score Agent 2's candidates in one shot (non-split usage / tests)."""
    import time as _t
    start = _t.time()
    candidates = agent2_result.get("candidates", [])
    out = score_candidates(candidates)
    found = sum(1 for c in out if c.get("catalyst") not in (None, "none"))
    return {
        "status": "success",
        "candidates_with_fa": out,
        "total_processed": found,
        "total_failed": len(out) - found,
        "duration_seconds": round(_t.time() - start, 2),
    }
