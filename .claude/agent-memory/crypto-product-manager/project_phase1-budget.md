---
name: project_phase1-budget
description: Phase 1 approved operational budget recommendation — $1,200/mo with 60-day review gate
metadata:
  type: project
---

Phase 1 monthly operational budget recommendation: $1,200/mo (as of 2026-06-08).

Baseline costs: Data APIs $500/mo + Infrastructure $320/mo = $820/mo.
Buffer approved: +$380 (46%) covering API consumption spikes, data source experimentation, and monitoring tooling.

Breakdown:
- $820 baseline ops
- +$180 API cost overrun reserve (consumption-based, can spike with user load)
- +$100 Phase 1 data source experimentation (trial additional on-chain/sentiment feeds)
- +$100 monitoring/error tooling (Datadog, Sentry, etc.)

Hard review gate: 60-day go/no-go. If Phase 1 passes, present revised infrastructure cost projections for Phase 2 scale before costs increase.

**Why:** Operational budget only — does not include personnel, legal, or audit. Avoid mid-phase budget conversations by baking in a realistic buffer upfront.

**How to apply:** If asked about budget for Phase 2 or scale-up, note that Phase 2 infrastructure projections are a separate conversation contingent on Phase 1 go/no-go outcome. Do not extrapolate $1,200 to Phase 2 sizing.
