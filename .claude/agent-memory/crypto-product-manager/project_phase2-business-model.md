---
name: project_phase2-business-model
description: Phase 2 paid tier pricing ($39/mo), feature set, and Phase 1 data model requirements for monetization
metadata:
  type: project
---

Phase 2 business model decision (decided 2026-06-09):

**Pricing:** $39/month, $374/year (20% annual discount).

Rationale: Parity with Messari Pro; 2.5x TradingView Pro floor signals quality to traders putting real capital at risk. Do not anchor below $25.

**Free vs. Paid tier split:**
- Free: top-5 crypto candidates/day, current-day signals only, detail panel access
- Paid: unlimited candidates (crypto + US equities), 90-day signal history + outcome tracking, watchlist with alerts, CSV/JSON export, daily/weekly digest, confidence level filter, priority support
- US equities access is the primary paid-tier anchor in Phase 2

**Phase 1 data model requirements (critical — do not skip):**
1. Anonymous session IDs: persistent cookie/localStorage ID assigned on first visit; all events logged against it. Enables Phase 2 "create an account to preserve your history" conversion hook without forcing registration in Phase 1.
2. Server-side event log: log candidate_viewed, candidate_detail_opened, signal_age_at_view server-side (not just client analytics). This is the conversion funnel dataset for paywall feature decisions.
3. Watchlist in localStorage only: no server-side watchlist table in Phase 1. Phase 2 upgrade hook is "sync your watchlist across devices and get alerts."

**What NOT to build in Phase 1:** user accounts, password reset, email verification, session management. Auth stack is 2-3 engineering weeks and is not on the critical path to PMF validation.

**Why:** Phase 1 is free and validates signal quality. Phase 2 monetization requires conversion funnel visibility from day 1 — anonymous session tracking is the mechanism. Premature auth delays launch with no PMF benefit.

**How to apply:** If asked about user accounts, login, or auth in a Phase 1 context, redirect to anonymous session ID approach. If asked about Phase 2 pricing, anchor at $39/month and defend with hit rate track record as the primary value justification. See [[project_phase1-budget]] for operational cost context.
