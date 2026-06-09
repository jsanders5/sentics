---
name: project_go-no-go-cohort
description: Minimum cohort size and signal volume required for a statistically meaningful 60-day go/no-go review
metadata:
  type: project
---

60-day go/no-go cohort requirements (decided 2026-06-09):

- Minimum: 100 users + 500 closed signals
- Target: 150 users + 800+ closed signals
- Hard floor: 75 users — below this, delay review by 30 days (distribution problem, not a product problem)

Decision rules by cohort size:
- 150+ users, 500+ signals: full go/no-go, all four metrics evaluable
- 100-149 users: proceed, flag 7-day retention as lower-confidence
- 75-99 users: extend window 30 days
- Under 75 users: diagnose acquisition funnel before assessing product metrics

Binding constraint by metric:
- Hit rate (55%): constrained by signal volume (need 400+ closed trades for meaningful binomial test), not user count
- 7-day retention (40%): binding constraint on user count — need 3-4 weekly cohorts of 25-40 users each
- DAU/MAU (40%): needs 100+ users to avoid individual behavior dominating the ratio
- Free-to-paid intent (15%): needs 75+ survey responses — not the binding constraint

**Why:** Below 75 users, a go/no-go becomes a judgment call rather than a data-driven decision, which undermines the discipline the gate is meant to create. 7-day retention cohort analysis is the most user-count-sensitive metric and sets the floor.

**How to apply:** Reference this when planning Phase 1 user acquisition targets. If asked whether to proceed with the 60-day review at a given user count, apply this decision table directly.
