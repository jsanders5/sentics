---
name: project_meme-coin-decision
description: Resolved product decision — meme coins included in top-50 scope with Medium confidence cap and UI guardrails
metadata:
  type: project
---

Meme coin inclusion decision: INCLUDE with guardrails (decided 2026-06-08).

Rule: Any asset in top-50 by market cap is eligible, including meme coins (DOGE, SHIB, etc.). No carve-outs by asset "type."

Guardrails:
- Confidence tier hard cap at Medium (never High) for any asset lacking fundamental indicators (staking yield, protocol revenue, earnings).
- UI must surface a "speculative asset" label on the candidate card — visible, not in fine print.
- Signal sourcing note: flag that meme coin signals rely on momentum/volume, not on-chain fundamentals; signal decay is faster.
- User-level toggle to hide meme coins deferred to Phase 1.1.

**Why:** Top-50 filter is objective and defensible. Excluding within that boundary is arbitrary and invites scope disputes. Retail traders — core Phase 1 persona — actively trade these assets. The Medium cap + labeling shifts risk appropriately to the trader's judgment.

**How to apply:** When evaluating any future feature or signal decisions, apply the Medium confidence cap mechanically to meme coin assets. Do not revisit inclusion unless early user feedback (top-3 complaints) indicates traders want exclusion by default.
