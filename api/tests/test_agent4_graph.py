"""
Offline tests for lib/agents/agent4_graph.py — no live Anthropic API key, no
Supabase, no network. Verifies:

  1. Aligned sentiment (or no catalyst) skips reconciliation entirely.
  2. Disagreement triggers reconciliation, and the model's decision to call
     get_symbol_track_record is honored end-to-end (tool call -> tool result ->
     final answer).
  3. The model choosing NOT to call the tool during reconciliation is also
     handled correctly (no forced tool call).
  4. Any failure during reconciliation falls back to the original classification
     instead of raising — matching the rest of Agent 4's graceful-degradation
     design.

Run with: pytest api/tests/test_agent4_graph.py -v
"""

import json
import sys
import os
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_SECRET_KEY", "test")
os.environ.setdefault("SENTRY_DSN", "")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-not-real")

from lib.agents import agent4_graph as ag  # noqa: E402


class Block:
    """Mimics an Anthropic content block (text or tool_use)."""
    def __init__(self, type_, text=None, input=None, id=None):
        self.type = type_
        self.text = text
        self.input = input
        self.id = id


class FakeMessage:
    def __init__(self, content, stop_reason="end_turn"):
        self.content = content
        self.stop_reason = stop_reason


class FakeClient:
    """Returns canned responses in sequence; records call count."""
    def __init__(self, responses):
        self._responses = list(responses)
        self.call_count = 0

    class _Messages:
        def __init__(self, outer):
            self._outer = outer

        def create(self, **kwargs):
            self._outer.call_count += 1
            return self._outer._responses[self._outer.call_count - 1]

    @property
    def messages(self):
        return FakeClient._Messages(self)


CLASSIFY_JSON = json.dumps({
    "sentiment": 0.8, "magnitude": 0.7, "catalyst": "listing",
    "confidence": "High", "summary": "Major exchange listing announced.",
})

CONFLICTING_CLASSIFY_JSON = json.dumps({
    "sentiment": -0.9, "magnitude": 0.8, "catalyst": "hack",
    "confidence": "High", "summary": "Protocol exploit drained funds.",
})

RECONCILED_JSON = json.dumps({
    "sentiment": -0.6, "magnitude": 0.6, "catalyst": "hack",
    "confidence": "Medium",
    "summary": "Exploit is real but TA has been consistently Bullish; softened conviction.",
})


def _headlines():
    return [{"title": "Some headline", "url": "https://example.com/a", "snippet": "..."}]


def test_aligned_sentiment_skips_reconciliation():
    """Sentiment agrees with TA direction -> only the classify call happens."""
    client = FakeClient([FakeMessage([Block("text", text=CLASSIFY_JSON)])])
    fa = ag.classify_with_reconciliation(client, "Example Coin", "EX", _headlines(), "Bullish")
    assert fa["catalyst"] == "listing"
    assert client.call_count == 1  # no reconciliation triggered


def test_no_catalyst_skips_reconciliation():
    """catalyst == 'none' -> never reconcile, regardless of sentiment number."""
    neutral_json = json.dumps({
        "sentiment": -0.9, "magnitude": 0.1, "catalyst": "none",
        "confidence": "Low", "summary": "No significant catalyst.",
    })
    client = FakeClient([FakeMessage([Block("text", text=neutral_json)])])
    fa = ag.classify_with_reconciliation(client, "Example Coin", "EX", _headlines(), "Bullish")
    assert fa["catalyst"] == "none"
    assert client.call_count == 1


@patch("lib.agents.agent4_graph.get_symbol_track_record")
def test_disagreement_triggers_reconciliation_with_tool_call(mock_track_record):
    """TA says Bullish, news reads strongly Bearish -> reconciliation fires, model
    calls the tool, tool result is round-tripped, final answer is used."""
    mock_track_record.return_value = [
        {"run_ts": "2026-07-10T00:00:00Z", "direction": "Bullish", "confidence_tier": "High"},
        {"run_ts": "2026-07-09T00:00:00Z", "direction": "Bullish", "confidence_tier": "High"},
    ]
    client = FakeClient([
        FakeMessage([Block("text", text=CONFLICTING_CLASSIFY_JSON)]),           # classify
        FakeMessage(                                                            # reconcile: calls tool
            [Block("tool_use", input={"symbol": "EX"}, id="tool_1")],
            stop_reason="tool_use",
        ),
        FakeMessage([Block("text", text=RECONCILED_JSON)]),                     # reconcile: final
    ])
    fa = ag.classify_with_reconciliation(client, "Example Coin", "EX", _headlines(), "Bullish")

    assert client.call_count == 3
    mock_track_record.assert_called_once_with("EX")
    assert fa["fa_confidence"] == "Medium"
    assert "softened" in fa["fa_summary"]


def test_disagreement_triggers_reconciliation_without_tool_call():
    """Model decides it doesn't need the tool -> uses its first reconcile answer
    directly; get_symbol_track_record is never called."""
    client = FakeClient([
        FakeMessage([Block("text", text=CONFLICTING_CLASSIFY_JSON)]),  # classify
        FakeMessage([Block("text", text=RECONCILED_JSON)]),            # reconcile, no tool
    ])
    with patch("lib.agents.agent4_graph.get_symbol_track_record") as mock_track_record:
        fa = ag.classify_with_reconciliation(client, "Example Coin", "EX", _headlines(), "Bullish")
        mock_track_record.assert_not_called()
    assert client.call_count == 2
    assert "softened" in fa["fa_summary"]


def test_reconciliation_failure_falls_back_to_original():
    """If the reconcile call raises, fall back to the original classification
    instead of propagating — reconciliation is a refinement, never a dependency."""
    class RaisingClient(FakeClient):
        class _Messages(FakeClient._Messages):
            def create(self, **kwargs):
                self._outer.call_count += 1
                if self._outer.call_count == 1:
                    return FakeMessage([Block("text", text=CONFLICTING_CLASSIFY_JSON)])
                raise RuntimeError("simulated API failure")

        @property
        def messages(self):
            return RaisingClient._Messages(self)

    client = RaisingClient([])
    fa = ag.classify_with_reconciliation(client, "Example Coin", "EX", _headlines(), "Bullish")
    # Falls back to the original (pre-reconciliation) classification.
    assert fa["catalyst"] == "hack"
    assert fa["fa_summary"] == "Protocol exploit drained funds."


if __name__ == "__main__":
    import pytest
    raise SystemExit(pytest.main([__file__, "-v"]))
