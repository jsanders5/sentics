---
name: project-oq2-evaluation-framework
description: OQ#2 LLM provider evaluation framework for Agent 3 — Claude Sonnet 4.6 vs GPT-4o — designed 2026-06-08, evaluation not yet run
metadata:
  type: project
---

The OQ#2 evaluation framework was designed in the session of 2026-06-08. The evaluation has NOT yet been run. This is Go/No-Go Blocker #3 for Phase 1.

**Why:** Agent 3 sprint cannot begin until the production LLM provider is selected. The PRD (Section 6.3 and Section 14) mandates a structured side-by-side evaluation of at least 20 crypto candidates before provider selection.

**How to apply:** When the user asks about running the evaluation, resuming work on Agent 3, or the OQ#2 status — the evaluation protocol exists but has not been executed. The next action is to build the test set inputs, build the evaluation harness, and schedule reviewer time.

## Key Decisions Made

- Run both providers simultaneously (not sequentially) — eliminates anchoring bias, saves calendar time
- 25 candidates across 3 difficulty tiers (5 clear signal, 10 mixed signal, 10 edge cases)
- Blind review: outputs labeled A/B; reviewers don't know which provider is which
- 3 iterations per provider per candidate — iteration 1 for human review, iterations 2–3 for consistency scoring
- Claude candidate: claude-sonnet-4-6 at effort:high. Secondary pass: claude-opus-4-8 on Tier 3 only (10 candidates, ~$0.06)
- GPT-4o candidate: gpt-4o with temperature=0 and response_format: json_object
- Human reviewers: minimum 2 (per PRD); recommended 3 for tiebreaking

## Evaluation Dimensions

1. Rationale Quality (human, 5 sub-dimensions: technical citation, narrative citation, on-chain citation, confidence tier calibration, pre-trade reference quality) — 1–5 scale each
2. Schema Compliance (automated) — percentage of fields passing; <90% is disqualifying
3. Hallucination Rate (automated + spot check) — <95% (>1 hallucination/25 candidates) is a serious concern
4. Latency (automated) — p50 and p95; p95 >60 seconds is disqualifying
5. Cost per run (automated) — projected monthly vs. $50–$200 target

## Success Criteria (abbreviated)

Provider wins on a dimension if it exceeds the other by: ≥5pp on schema compliance; ≥5pp on hallucination rate; ≥0.5 points on rationale quality; ≥20% lower cost; ≥20% lower p95 latency. Win on 3+ of 5 dimensions = winner. Meme coin High confidence = immediate disqualification.

## Cost and Time Estimate

- LLM API cost for the evaluation: ~$1.70–$1.90 total (trivial)
- Human reviewer time: ~50–53 person-hours
- Calendar duration: 6–7 working days from kickoff to decision memo

## Critical Edge Cases in the Test Set

- Candidates 16, 17, 18: Meme coins (DOGE, SHIB, PEPE) — must never receive High confidence
- Candidate 12 (TAO): No on-chain data available — graceful omission required
- Candidate 19 (CRV): Token unlock in 5 days — must identify as risk
- Candidate 22: RSI=71 (upper boundary) — overbought boundary handling
- Candidates 23, 24, 25: Synthetic inputs required (modified RSI, zeroed on-chain, conflicting signals)
