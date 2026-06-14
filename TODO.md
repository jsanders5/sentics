# TODO

Tracked follow-ups for the sentics platform.

## Trade plans (priority)

- [ ] **Compliance review of trade plans.** The dashboard now outputs specific
  entry / target / stop levels (`compute_trade_plan` in `api/lib/agents/agent2.py`),
  which moves from general "analysis" toward investment-advice territory. Before
  this goes public, run a review with the `fintech-compliance-specialist` agent:
  validate disclaimer language, the "educational / not financial advice" framing
  on plans, and the spot-vs-short presentation. Keep stop/risk shown alongside
  every target.

- [ ] **Higher-precision price levels (OHLC).** Trade-plan levels currently use
  daily *closes* from CoinGecko's `market_chart` endpoint. This is fine for
  MA/swing logic but means stops/targets ignore true intraday highs and lows. To
  tighten them, pull `/coins/{id}/ohlc` and compute swing levels / ATR-based
  stops from real candle ranges (one extra API call per coin — mind rate limits).

## Other known open items

- [ ] **Refresh can time out on long runs.** `POST /api/run-pipeline` triggers the
  pipeline synchronously; a full run (~25 CoinGecko + 25 Claude calls) can exceed
  Vercel's function execution limit even though the run continues server-side.
  Make the trigger fire-and-forget and have the UI poll for completion.

- [ ] **`run-pipeline` has no auth.** The endpoint is public, so anyone could
  trigger expensive CoinGecko/Claude runs. Add a shared-secret guard (or similar)
  before public launch.
