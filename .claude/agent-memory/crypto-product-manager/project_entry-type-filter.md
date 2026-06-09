---
name: project_entry-type-filter
description: Entry type filtering (Breakout/Retest/Dip-Buy) deferred to Phase 1.1 with specific pull-forward conditions
metadata:
  type: project
---

Entry type filter decision (decided 2026-06-09): DEFER to Phase 1.1.

Phase 1 scope: Display entry type (Breakout/Retest/Dip-Buy) in detail panel with a one-sentence execution description. No filter control on main dashboard.

**Pull-forward conditions (either triggers Phase 1.1 acceleration):**
1. User feedback signal: 25-30%+ of complaints or feature requests in weeks 1-4 reference irrelevant entry types or request filtering by entry type.
2. Hit rate divergence: pre-launch or 30-day analysis shows material hit rate difference between entry types (e.g., one type hitting at <50% vs another at 65%+). Filtering becomes brand protection, not workflow refinement.

**Why deferred:** Filtering is a workflow refinement, not a core workflow enabler. Users can mentally discard entry types from a 10-item list. Elevating to a filter before entry type labeling accuracy is validated risks exposing model weaknesses through a prominent UI control. Not on the critical path to PMF validation.

**How to apply:** When scoping Phase 1 dashboard features, entry type filter is out of scope unless a pull-forward condition is confirmed. In Phase 1.1 planning, entry type filter is the first candidate feature from the backlog. Flag the hit rate divergence question to the data science team before the 60-day review.
