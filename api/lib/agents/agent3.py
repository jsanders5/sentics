"""
Agent 3: Forward-Looking Synthesis with Claude

Takes the candidate list from Agent 2 and generates an AI-written narrative for
each one:
- rationale (2-3 sentences consistent with Agent 2's directional call)
- key_signals
- entry_type / entry_quality (direction-aware)

Agent 2 OWNS direction / time_horizon / confidence_tier / candidate_score /
trade_plan. Agent 3 must NOT override them — it only adds narrative fields, which
are whitelisted before merging so the deterministic source of truth can never be
clobbered by the model.

Calls are run concurrently (the pipeline is a daily batch, not latency-sensitive,
but bounded concurrency keeps it well under the serverless timeout). A candidate
whose synthesis fails is dropped and counted — never shipped with fabricated
analysis.
"""

import os
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Optional

import anthropic

from .utils import log_info, log_error

# Model is overridable via env so we can re-tier without a code change.
AGENT3_MODEL = os.getenv("AGENT3_MODEL", "claude-sonnet-4-6")
MAX_CANDIDATES = 25
MAX_WORKERS = 5
MAX_TOKENS = 1024

# Direction-aware entry vocabularies. A Bearish coin must never be tagged with a
# long-only entry type ("Breakout"/"Dip-Buy"), which was the prior bug.
ENTRY_TYPES = {
    "Bullish": ["Breakout", "Retest", "Dip-Buy"],
    "Bearish": ["Breakdown", "Failed-Retest", "Bounce-Fade"],
    "Neutral": ["Watch"],
}
ENTRY_QUALITIES = ["Strong", "Moderate", "Speculative"]

# Only these keys are allowed to flow from Claude into the candidate. Anything
# else (direction, time_horizon, confidence_tier, ...) stays owned by Agent 2.
NARRATIVE_KEYS = {"entry_type", "entry_quality", "rationale", "key_signals"}


def build_prompt(candidate: Dict) -> str:
    """Build the Claude prompt. Agent 2's classification is fixed; Claude explains it."""
    direction = candidate.get("direction", "Neutral")
    time_horizon = candidate.get("time_horizon", "Medium")
    confidence = candidate.get("confidence_tier", "Low")
    existing_signals = candidate.get("key_signals", [])

    levels = (candidate.get("trade_plan") or {}).get("levels", {})
    ma20 = levels.get("ma20")
    ma50 = levels.get("ma50")
    price = candidate.get("price")

    def _rel(p, ma):
        if not p or not ma:
            return "n/a"
        return "above" if p >= ma else "below"

    plan = candidate.get("trade_plan") or {}
    if plan.get("bias") in ("long", "short"):
        plan_str = (
            f"- Entry: {plan.get('entry')} — {plan.get('entry_condition')}\n"
            f"- Target: {plan.get('target')} — {plan.get('target_condition')}\n"
            f"- Stop: {plan.get('stop')} — {plan.get('stop_condition')}\n"
            f"- Risk/reward: {plan.get('risk_reward')}"
        )
    else:
        plan_str = "- No actionable setup (neutral)."

    entry_options = " | ".join(ENTRY_TYPES.get(direction, ENTRY_TYPES["Neutral"]))

    catalyst = candidate.get("catalyst")
    fa_summary = candidate.get("fa_summary")
    if catalyst and catalyst != "none" and fa_summary:
        fa_str = (
            f"- Catalyst: {catalyst} (sentiment {candidate.get('sentiment')}, "
            f"confidence {candidate.get('fa_confidence')})\n- {fa_summary}"
        )
    else:
        fa_str = "- No significant news catalyst detected."

    return f"""You are a crypto market analyst. A technical model has already classified this
asset. Write a rationale that explains and is fully consistent with that classification.

ASSET:
- Symbol: {candidate['symbol']}
- Name: {candidate['name']}
- Current Price: {price}

MODEL CLASSIFICATION (do NOT contradict these):
- Direction: {direction}  (price expected to move {'UP' if direction == 'Bullish' else 'DOWN' if direction == 'Bearish' else 'sideways / unclear'})
- Timeframe: {time_horizon}
- Confidence: {confidence}

TECHNICAL INDICATORS:
- RSI (14): {candidate.get('rsi')}
- Volume Ratio: {candidate.get('volume_ratio')}x its 30-day average (1.3x = confirmation threshold)
- 20-day MA: {ma20} (price is {_rel(price, ma20)} it)
- 50-day MA: {ma50} (price is {_rel(price, ma50)} it)
- Technical alignment score: {candidate.get('technical_score')}/58
- Model-detected signals: {existing_signals}

TRADE PLAN (reference these levels in your rationale; do NOT invent different ones):
{plan_str}

NEWS / CATALYST (fundamental analysis — weave in if present, don't overstate):
{fa_str}

PROVIDE OUTPUT IN THIS EXACT JSON FORMAT:
{{
  "entry_type": "{entry_options}",
  "entry_quality": "Strong | Moderate | Speculative",
  "rationale": "2-3 sentences explaining the {direction} thesis over the {time_horizon} timeframe. Cite RSI, volume, and MA structure. Be specific.",
  "key_signals": ["signal1", "signal2", "signal3"]
}}

GUIDELINES:
- The rationale MUST support a {direction} view. If Bearish, explain downside risk; if Bullish, explain upside; if Neutral, explain why the signal is unclear.
- entry_type MUST be one of: {entry_options}.
- Rationale must be 2-3 sentences max, specific, and cite actual indicator values.
- This is educational analysis, not financial advice.

Return ONLY valid JSON, no markdown or extra text.
"""


def parse_claude_response(response_text: str) -> Dict:
    """Extract the JSON object from Claude's response. Raises on failure so the
    caller drops the candidate rather than shipping fabricated analysis."""
    text = response_text.strip()
    if "```json" in text:
        text = text.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in text:
        text = text.split("```", 1)[1].split("```", 1)[0].strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Fall back to the first {...} block in the text
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def validate_analysis(parsed: Dict, direction: str) -> Dict:
    """Coerce the parsed analysis to the allowed shape: direction-appropriate
    entry_type, valid entry_quality, string rationale, list of signals."""
    valid_entries = ENTRY_TYPES.get(direction, ENTRY_TYPES["Neutral"])
    entry_type = parsed.get("entry_type")
    if entry_type not in valid_entries:
        entry_type = valid_entries[0]

    entry_quality = parsed.get("entry_quality")
    if entry_quality not in ENTRY_QUALITIES:
        entry_quality = "Moderate"

    rationale = parsed.get("rationale")
    if not isinstance(rationale, str) or not rationale.strip():
        raise ValueError("missing rationale")

    key_signals = parsed.get("key_signals")
    if not isinstance(key_signals, list):
        key_signals = []
    key_signals = [str(s) for s in key_signals if str(s).strip()]

    return {
        "entry_type": entry_type,
        "entry_quality": entry_quality,
        "rationale": rationale.strip(),
        "key_signals": key_signals,
    }


def _extract_text(message) -> Optional[str]:
    """Pull the first text block, guarding against refusals / empty content."""
    if getattr(message, "stop_reason", None) == "refusal":
        return None
    for block in getattr(message, "content", []) or []:
        if getattr(block, "type", None) == "text" and getattr(block, "text", None):
            return block.text
    return None


def _synthesize(client: "anthropic.Anthropic", candidate: Dict) -> Optional[Dict]:
    """Generate narrative for one candidate. Returns the merged candidate, or
    None if synthesis failed (caller counts and drops it)."""
    symbol = candidate.get("symbol", "?")
    direction = candidate.get("direction", "Neutral")
    try:
        message = client.messages.create(
            model=AGENT3_MODEL,
            max_tokens=MAX_TOKENS,
            messages=[{"role": "user", "content": build_prompt(candidate)}],
        )
        text = _extract_text(message)
        if not text:
            raise RuntimeError(f"no usable text (stop_reason={getattr(message, 'stop_reason', None)})")

        analysis = validate_analysis(parse_claude_response(text), direction)

        # Preserve Agent 2's deterministic key_signals if Claude returned none.
        if not analysis["key_signals"]:
            analysis["key_signals"] = candidate.get("key_signals", [])

        # Whitelist: only narrative keys merge — Agent 2's fields always win.
        merged = {**candidate, **{k: analysis[k] for k in NARRATIVE_KEYS if k in analysis}}
        log_info(f"Processed {symbol}: {direction} / {candidate.get('confidence_tier', 'Low')} confidence")
        return merged
    except Exception as e:
        log_error(f"Error processing {symbol}", e)
        return None


def run(agent2_result: Dict) -> Dict:
    """Run Agent 3: AI Synthesis over Agent 2's candidates (concurrently)."""
    start_time = time.time()

    try:
        log_info("Agent 3 starting: AI Synthesis")

        candidates = agent2_result.get("candidates", [])
        if not candidates:
            log_info("No candidates from Agent 2; skipping Agent 3")
            return {
                "status": "success",
                "candidates_with_rationales": [],
                "total_processed": 0,
                "total_failed": 0,
                "duration_seconds": 0,
            }

        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise Exception("ANTHROPIC_API_KEY not set")
        # SDK retries 429/5xx/connection errors with backoff; bump from the default 2.
        client = anthropic.Anthropic(api_key=api_key, max_retries=4, timeout=60.0)

        batch = candidates[:MAX_CANDIDATES]
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            results = list(executor.map(lambda c: _synthesize(client, c), batch))

        processed = [r for r in results if r is not None]
        failed_count = len(batch) - len(processed)

        # Sort by conviction (defensive .get — never crash on a malformed candidate)
        processed.sort(key=lambda x: x.get("candidate_score", 0), reverse=True)

        log_info(f"Agent 3 complete: {len(processed)} rationales generated, {failed_count} failed")

        return {
            "status": "success" if failed_count == 0 else "partial",
            "candidates_with_rationales": processed,
            "total_processed": len(processed),
            "total_failed": failed_count,
            "duration_seconds": round(time.time() - start_time, 2),
        }

    except Exception as e:
        log_error("Agent 3 failed", e)
        return {
            "status": "error",
            "error": str(e),
            "candidates_with_rationales": [],
            "total_processed": 0,
            "total_failed": 0,
            "duration_seconds": round(time.time() - start_time, 2),
        }
