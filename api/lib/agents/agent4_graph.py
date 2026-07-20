"""
Agent 4 reconciliation graph: adds a genuinely agentic step on top of the
existing news classification in agent4.py.

Why this exists: agent4.combine_ta_fa() blends news sentiment with Agent 2's
technical-analysis direction, but never flips it — by design, FA only modulates
conviction. That means when a catalyst's sentiment strongly OPPOSES the existing
TA direction (e.g. TA says Bullish, but the news classifier reads clearly
Bearish), the disagreement is real and worth a second look before the read ships.

This module wraps the single classification call in a small LangGraph
StateGraph:

    classify --(sentiment vs. TA direction agree, or no real catalyst)--> END
             --(meaningful disagreement)--------------------------------> reconcile --> END

`reconcile` gives Claude a tool, get_symbol_track_record, that looks up this
pipeline's OWN recent directional calls for the symbol (from the call_snapshots
ledger eval_calls.py also reads). The model decides for itself whether calling
it is useful before finalizing a read — this is a real tool-use decision, not a
scripted lookup. If the tool isn't called, or the graph/tool call fails for any
reason, we fall back to the original classification untouched (never break the
pipeline — same philosophy as the rest of Agent 4).

Output shape is identical to agent4.parse_fa()'s: sentiment / magnitude /
catalyst / fa_confidence / fa_summary / fa_sources. No new DB columns needed.
"""

import os
import json
from typing import Dict, List, Optional, TypedDict

import anthropic
from langgraph.graph import StateGraph, END

from .utils import log_info, log_error, get_symbol_track_record
from . import agent4 as a4  # reuse build_prompt / parse_fa / NEUTRAL_FA — no duplication

# Reconciliation is a slightly harder judgment call than plain classification,
# but still cheap/infrequent (only fires on real TA/news disagreement) — default
# to the same tier as classification; override independently if desired.
RECONCILE_MODEL = os.getenv("AGENT4_RECONCILE_MODEL", a4.AGENT4_MODEL)
MAX_TOKENS = 1024

# How opposed does the catalyst have to be (relative to TA direction) before it's
# worth a second look. sentiment is in [-1, 1]; aligned = sentiment * ta_sign, so
# aligned < -0.35 means a fairly confident catalyst pointing the opposite way.
DISAGREEMENT_THRESHOLD = -0.35

TRACK_RECORD_TOOL = {
    "name": "get_symbol_track_record",
    "description": (
        "Look up this pipeline's own recent directional calls for a crypto symbol "
        "(most recent first): direction, confidence tier, and score per prior run. "
        "Use this before finalizing a news read that conflicts with the current "
        "technical-analysis direction — it tells you whether this symbol's calls "
        "have been consistent or flip-flopping, which is useful context for how "
        "much conviction to put behind the disagreement."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "symbol": {"type": "string", "description": "Ticker symbol, e.g. 'BTC'"},
        },
        "required": ["symbol"],
    },
}


class FAState(TypedDict, total=False):
    name: str
    symbol: str
    direction: str
    headlines: List[Dict]
    fa: Dict
    reconciled: bool
    _client: object  # the anthropic.Anthropic instance; not persisted/serialized anywhere


def _ta_sign(direction: str) -> float:
    if direction == "Bullish":
        return 1.0
    if direction == "Bearish":
        return -1.0
    return 0.0


def classify_node(state: FAState) -> FAState:
    """Same single-call classification as agent4._classify — reused directly so
    this graph has exactly one source of truth for the base classification."""
    client = state["_client"]  # injected at invoke time, not part of persisted state
    fa = a4._classify(client, state["name"], state["symbol"], state["headlines"])
    return {"fa": fa, "reconciled": False}


def needs_reconciliation(state: FAState) -> str:
    fa = state.get("fa") or {}
    catalyst = fa.get("catalyst", "none")
    if catalyst == "none":
        return "end"  # nothing to reconcile against
    ta_sign = _ta_sign(state.get("direction", "Neutral"))
    if ta_sign == 0.0:
        return "end"  # Neutral candidates aren't directional; nothing to conflict with
    aligned = fa.get("sentiment", 0.0) * ta_sign
    return "reconcile" if aligned < DISAGREEMENT_THRESHOLD else "end"


def reconcile_node(state: FAState) -> FAState:
    """Give Claude a chance to check this symbol's call history before finalizing
    a read that conflicts with the TA direction. Falls back to the original
    classify_node read on any failure — reconciliation is a refinement, not a
    dependency."""
    client = state["_client"]
    fa = dict(state["fa"])
    symbol = state["symbol"]
    name = state["name"]
    direction = state["direction"]

    prompt = f"""Your read of the news for {name} ({symbol}) came out {fa['catalyst']!r}
with sentiment {fa['sentiment']:+.2f}, but the technical-analysis system has this
coin flagged {direction}. That is a real disagreement between the two signals.

You may call get_symbol_track_record to see this pipeline's own recent
directional calls on {symbol} — useful for judging whether {direction} has been
a consistent read or the pipeline has been flip-flopping.

Then respond with ONLY a JSON object in this exact format (no prose outside it):
{{
  "sentiment": <number -1.0..1.0>,
  "magnitude": <number 0.0..1.0>,
  "catalyst": "<short label, or 'none'>",
  "confidence": "High|Medium|Low",
  "summary": "<1-2 sentences, noting the TA disagreement if you're keeping the catalyst>"
}}"""

    try:
        messages = [{"role": "user", "content": prompt}]
        first = client.messages.create(
            model=RECONCILE_MODEL,
            max_tokens=MAX_TOKENS,
            tools=[TRACK_RECORD_TOOL],
            messages=messages,
        )

        tool_use = next(
            (b for b in (first.content or []) if getattr(b, "type", None) == "tool_use"),
            None,
        )

        if tool_use is None:
            # Model decided it didn't need the tool — use this response directly.
            text = next(
                (b.text for b in (first.content or []) if getattr(b, "type", None) == "text"),
                None,
            )
            if not text:
                return {"fa": fa, "reconciled": False}
            parsed = a4.parse_fa(text)
            parsed["fa_sources"] = fa.get("fa_sources", [])
            return {"fa": parsed, "reconciled": True}

        # Model asked for the track record — run it and send the result back.
        track_record = get_symbol_track_record(tool_use.input.get("symbol", symbol))
        log_info(f"Reconciliation: {symbol} called get_symbol_track_record "
                  f"({len(track_record)} prior calls found)")

        messages.append({"role": "assistant", "content": first.content})
        messages.append({
            "role": "user",
            "content": [{
                "type": "tool_result",
                "tool_use_id": tool_use.id,
                "content": json.dumps(track_record),
            }],
        })

        second = client.messages.create(
            model=RECONCILE_MODEL,
            max_tokens=MAX_TOKENS,
            tools=[TRACK_RECORD_TOOL],
            messages=messages,
        )
        text = next(
            (b.text for b in (second.content or []) if getattr(b, "type", None) == "text"),
            None,
        )
        if not text:
            return {"fa": fa, "reconciled": False}
        parsed = a4.parse_fa(text)
        parsed["fa_sources"] = fa.get("fa_sources", [])
        return {"fa": parsed, "reconciled": True}

    except Exception as e:  # noqa: BLE001 — reconciliation must never break the pipeline
        log_error(f"Reconciliation failed for {symbol}, keeping original read", e)
        return {"fa": fa, "reconciled": False}


def _build_graph():
    workflow = StateGraph(FAState)
    workflow.add_node("classify", classify_node)
    workflow.add_node("reconcile", reconcile_node)
    workflow.set_entry_point("classify")
    workflow.add_conditional_edges(
        "classify", needs_reconciliation, {"reconcile": "reconcile", "end": END}
    )
    workflow.add_edge("reconcile", END)
    return workflow.compile()


_GRAPH = _build_graph()


def classify_with_reconciliation(
    client: "anthropic.Anthropic", name: str, symbol: str,
    headlines: List[Dict], direction: str,
) -> Dict:
    """Drop-in replacement for agent4._classify with an added conditional
    reconciliation step. Same return shape (sentiment/magnitude/catalyst/
    fa_confidence/fa_summary/fa_sources), so callers don't need to change."""
    result = _GRAPH.invoke({
        "_client": client,
        "name": name,
        "symbol": symbol,
        "headlines": headlines,
        "direction": direction,
    })
    return result["fa"]
