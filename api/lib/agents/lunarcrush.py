"""
LunarCrush social‑intelligence client (API v4).

Replaces the old RSS + cheap‑model FA layer with structured social data. One call
to /coins/list/v2 returns per‑coin sentiment + social metrics for the whole
universe, so the pipeline reads social for all coins in a single request. Topic
endpoints provide the EVIDENCE behind a coin's sentiment (platform breakdown +
actual news/posts) for the drawer, lazily.

Design:
  - Display‑only for now: social data is surfaced and logged point‑in‑time, but
    does NOT modulate the conviction score until a backtest proves it has edge.
  - Graceful: any failure returns empty/None; the social layer must never break
    the pipeline (mirrors the old FA layer's contract).
  - NOTE: LunarCrush's WAF 403s the default python‑requests/urllib User‑Agent — a
    browser‑like UA header is required.
"""

import os
from typing import Dict, List, Optional

import requests

from .utils import log_info, log_error

BASE = "https://lunarcrush.com/api4/public"
HTTP_UA = "Mozilla/5.0 (compatible; sentics/1.0)"
TIMEOUT = 20

# Symbols we never surface as candidates / trending (stablecoins).
STABLECOINS = {
    "USDT", "USDC", "DAI", "FDUSD", "TUSD", "USDE", "USDS", "PYUSD", "BUSD",
    "GUSD", "USDP", "FRAX", "LUSD",
}


def _headers() -> Optional[Dict]:
    key = os.getenv("LUNARCRUSH_API_KEY")
    if not key:
        log_error("LUNARCRUSH_API_KEY not set; social layer disabled")
        return None
    return {"Authorization": f"Bearer {key}", "User-Agent": HTTP_UA}


def _get(path: str, params: Optional[Dict] = None):
    """GET a LunarCrush endpoint → its `data` payload, or None on any failure."""
    headers = _headers()
    if not headers:
        return None
    try:
        resp = requests.get(f"{BASE}/{path}", headers=headers, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        body = resp.json()
        return body.get("data") if isinstance(body, dict) else body
    except Exception as e:  # noqa: BLE001 — social layer must never break the pipeline
        log_error(f"LunarCrush GET {path} failed", e)
        return None


def _social_from_row(r: Dict) -> Dict:
    """Extract the per‑coin social read from a coins/list row. `_delta` fields use
    LunarCrush's *_previous values so we can show change (velocity), which is where
    any signal would live — not the raw level."""
    gs, gsp = r.get("galaxy_score"), r.get("galaxy_score_previous")
    ar, arp = r.get("alt_rank"), r.get("alt_rank_previous")
    return {
        "sentiment": r.get("sentiment"),                       # 0–100, LunarCrush
        "galaxy_score": gs,
        "galaxy_delta": round(gs - gsp, 2) if gs is not None and gsp is not None else None,
        "alt_rank": ar,
        "alt_rank_delta": (arp - ar) if ar is not None and arp is not None else None,  # +ve = improving
        "social_dominance": r.get("social_dominance"),
        "social_volume_24h": r.get("social_volume_24h"),
        "interactions_24h": r.get("interactions_24h"),
        "topic": r.get("topic"),
    }


def fetch_coins_list() -> List[Dict]:
    """Full coins/list/v2 (5k+ coins with price + social). [] on failure."""
    data = _get("coins/list/v2")
    return data if isinstance(data, list) else []


def social_read(symbols: List[str], coins: Optional[List[Dict]] = None) -> Dict[str, Dict]:
    """Map {SYMBOL: social_read} for the requested symbols. Fetches the list once
    (or reuses `coins`), picking the highest‑market‑cap row per symbol to avoid
    ticker collisions in the 5k‑coin universe."""
    coins = coins if coins is not None else fetch_coins_list()
    wanted = {s.upper() for s in symbols}
    best: Dict[str, Dict] = {}
    for r in coins:
        s = (r.get("symbol") or "").upper()
        if s in wanted and (s not in best or (r.get("market_cap") or 0) > (best[s].get("market_cap") or 0)):
            best[s] = r
    return {s: _social_from_row(r) for s, r in best.items()}


def fetch_trending(limit: int = 25, min_market_cap: float = 1e7,
                   coins: Optional[List[Dict]] = None) -> List[Dict]:
    """Discovery list ranked by AltRank (LunarCrush's price+social composite; lower
    = hotter). Excludes stablecoins and illiquid dust. Descriptive only — clearly
    labelled in the UI as trending, NOT the main screener universe."""
    coins = coins if coins is not None else fetch_coins_list()
    cand = [
        r for r in coins
        if (r.get("symbol") or "").upper() not in STABLECOINS
        and r.get("alt_rank")
        and (r.get("market_cap") or 0) > min_market_cap
    ]
    cand.sort(key=lambda r: r["alt_rank"])
    out = []
    for r in cand[:limit]:
        out.append({
            "symbol": (r.get("symbol") or "").upper(),
            "name": r.get("name"),
            "price": r.get("price"),
            "market_cap": r.get("market_cap"),
            "percent_change_24h": r.get("percent_change_24h"),
            "logo": r.get("logo"),
            "topic": r.get("topic"),
            **_social_from_row(r),
        })
    return out


def fetch_topic_evidence(topic: str, news_limit: int = 6, posts_limit: int = 6) -> Dict:
    """The EVIDENCE behind a coin's sentiment for the drawer: platform sentiment
    breakdown + top news + top social posts. Returns partial/empty on failure."""
    detail = _get(f"topic/{topic}/v1") or {}
    news = _get(f"topic/{topic}/news/v1") or []
    posts = _get(f"topic/{topic}/posts/v1") or []

    def _clean(items, n):
        out = []
        for it in (items if isinstance(items, list) else [])[:n]:
            out.append({
                "title": it.get("post_title"),
                "link": it.get("post_link"),
                "type": it.get("post_type"),
                "sentiment": it.get("post_sentiment"),   # 1–5 scale (3 ≈ neutral)
                "creator": it.get("creator_display_name") or it.get("creator_name"),
                "interactions": it.get("interactions_24h"),
            })
        return out

    return {
        "trend": detail.get("trend"),
        "num_posts": detail.get("num_posts"),
        "num_contributors": detail.get("num_contributors"),
        "types_sentiment": detail.get("types_sentiment"),          # per‑platform 0–100
        "types_sentiment_detail": detail.get("types_sentiment_detail"),
        "news": _clean(news, news_limit),
        "posts": _clean(posts, posts_limit),
    }
