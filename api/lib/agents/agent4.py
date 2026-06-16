"""
Agent 4: Fundamental Analysis — news / catalyst layer.

For each candidate, searches recent news via Claude's server-side web_search tool
and extracts a structured catalyst read: net sentiment, magnitude, a catalyst
label, a short summary, and sources. Produces `fa_score = sentiment * magnitude`
in [-1, +1], which the pipeline BLENDS with the TA directional score.

Point-in-time integrity (accumulate-forward): the news is assessed against the web
as it exists AT RUN TIME and frozen into a daily snapshot. That snapshot — not a
future re-search — is the leak-free record the FA backtest replays. So this is
honest for forward accumulation even though live web search isn't reproducible.

Design choices:
  - Concurrent, with graceful degradation: any failure → neutral FA (fa_score 0),
    never drops the candidate or breaks the pipeline.
  - Conservative blend: FA modulates CONVICTION (agreement strengthens, opposition
    weakens) but does NOT flip the TA-derived direction — that keeps the trade plan
    (built on TA direction) consistent. The signed `combined_score` is stored so a
    future, backtest-calibrated blend can do more.
  - Robust JSON parsing (web_search emits citations, which are incompatible with
    structured outputs, so we parse the JSON from the text ourselves).
"""

import os
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional

import anthropic

from .utils import log_info, log_error
from .agent2 import compute_candidate_score

AGENT4_MODEL = os.getenv("AGENT4_MODEL", "claude-sonnet-4-6")
MAX_WORKERS = 4
MAX_TOKENS = 1024
MAX_PAUSE_CONTINUATIONS = 3
WEB_SEARCH_TOOL = {"type": "web_search_20260209", "name": "web_search"}

# Conservative, UN-CALIBRATED weight: how much a full-strength catalyst (|fa_score|=1)
# adds to / subtracts from the TA magnitude (~[20,100]) when computing conviction.
# A future FA backtest (accumulate-forward) should calibrate this.
FA_WEIGHT = 25.0

NEUTRAL_FA = {
    "fa_score": 0.0, "sentiment": 0.0, "magnitude": 0.0, "catalyst": "none",
    "fa_confidence": "Low", "fa_summary": "No significant catalyst detected.",
    "fa_sources": [],
}


def build_prompt(name: str, symbol: str) -> str:
    return f"""Search the web for recent (last ~7 days) news about the cryptocurrency {name} ({symbol})
and assess whether there is a market-moving CATALYST. Use web search; base your
assessment ONLY on what you actually find — do not speculate or rely on prior
knowledge. If there is no notable news, say so (sentiment 0, catalyst "none").

After searching, respond with ONLY a JSON object — no prose before or after:
{{
  "sentiment": <number -1.0..1.0, net bullish(+) / bearish(-) impact of the news>,
  "magnitude": <number 0.0..1.0, how market-moving the catalyst is>,
  "catalyst": "<short label, e.g. 'ETF flows', 'listing', 'hack', 'regulation', 'partnership', 'none'>",
  "confidence": "High|Medium|Low",
  "summary": "<1-2 sentences citing the specific catalyst, or 'No significant catalyst.'>",
  "sources": [{{"title": "...", "url": "..."}}]
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


def _search_and_score(client: "anthropic.Anthropic", name: str, symbol: str) -> Dict:
    """Run the web-search completion (handling pause_turn), parse, return FA dict.
    Returns NEUTRAL_FA on any failure — never raises."""
    try:
        messages = [{"role": "user", "content": build_prompt(name, symbol)}]
        message = None
        for _ in range(MAX_PAUSE_CONTINUATIONS + 1):
            message = client.messages.create(
                model=AGENT4_MODEL,
                max_tokens=MAX_TOKENS,
                tools=[WEB_SEARCH_TOOL],
                messages=messages,
            )
            if getattr(message, "stop_reason", None) != "pause_turn":
                break
            # Server tool hit the iteration cap — re-send to resume (no extra user msg)
            messages.append({"role": "assistant", "content": message.content})

        text = _extract_text(message)
        if not text:
            return dict(NEUTRAL_FA)
        return parse_fa(text)
    except Exception as e:  # noqa: BLE001 — news layer must never break the pipeline
        log_error(f"FA scoring failed for {symbol}", e)
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

    def score(c):
        # Skip the (slow, paid) news scan for Neutral coins — nothing to enrich.
        if c.get("direction", "Neutral") == "Neutral":
            m = {**c, **NEUTRAL_FA}
            combine_ta_fa(m)
            return m
        fa = _search_and_score(client, c.get("name", ""), c.get("symbol", "?"))
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
