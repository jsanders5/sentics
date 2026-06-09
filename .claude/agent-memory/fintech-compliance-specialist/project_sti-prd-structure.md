---
name: sti-prd-structure
description: STI Phase 1 PRD structure, key open questions, and go/no-go blockers — reference for navigating the PRD in future compliance conversations
metadata:
  type: project
---

The Phase 1 PRD is at `/docs/PRD-phase1-crypto.md` (v1.0, dated 2026-04-30, status: Draft — Pending Legal Review).
The Phase 2 PRD is at `/docs/PRD-v1.0.md`.

**Product**: Sentics Trading Intelligence (STI) — AI-powered ranked list of crypto buy candidates, updated every 6 hours, top 50 cryptos by market cap.

**Key scope facts for compliance purposes**:
- Phase 1: crypto only, spot only, no derivatives, no user accounts, no personalization
- Three-agent pipeline: Agent 1 (category trend) → Agent 2 (coin discovery) → Agent 3 (LLM synthesis/rationale)
- Stablecoins and wrapped token duplicates are excluded at ingestion layer
- Output: ranked "buy candidates" with confidence tier (High/Medium/Low) and time horizon (Short/Medium/Long)
- Pre-Trade Planning Reference (Section 8.6) is "Should Have" — surfaces resistance zones, invalidation levels, ATR, R:R context — requires separate legal review

**Go/No-Go Blockers (Section 15)**:
1. Legal sign-off in writing (crypto RIA question, coin exclusion list, disclaimer adequacy)
2. Data provider agreements confirmed (CoinGecko Pro, CryptoPanic, Glassnode, Anthropic)
3. LLM provider selected and tested
4. Candidate Score formula validated and documented
5. Disclaimer layer implemented and verified
6. End-to-end pipeline test completed
7. Security review completed
8. Graceful degradation verified

**Compliance-relevant open questions**:
- Q1: BLOCKING (launch) — regulatory registration and coin exclusion (assessed 2026-06-08, see [[sti-phase1-regulatory-posture]])
- Q7: Non-blocking — Glassnode licensing. RESOLVED 2026-06-09: Skip on-chain signals for Phase 1. PRD pricing assumption ($39/month) was wrong; API access costs $999+/month. CoinGecko is not a viable substitute. See [[sti-phase1-regulatory-posture]] for detail.
- Q10: BLOCKING (pre-trade reference feature) — RESOLVED 2026-06-09: Defer pre-trade planning reference to Phase 1.1. Legal risk is HIGH; including it in Phase 1 compromises publisher's exclusion defense for the entire product. See [[sti-phase1-regulatory-posture]] for detail.
- Q12: RESOLVED by Q10 outcome — pre-trade reference is Phase 1.1, not Phase 1 launch.

**Go/No-Go Blocker #2 update**: Glassnode is no longer a required data provider for Phase 1. The blocker for data provider agreements now covers: CoinGecko Pro, CryptoPanic, Anthropic only. Glassnode removed from required vendor list.

**Why:** Phase 1 is positioned as a faster, lower-cost crypto MVP. The plan is to assess product-market fit in crypto before building Phase 2 (equities + user accounts). Regulatory complexity is deliberately kept lower by excluding equities, derivatives, and user accounts.

**How to apply:** When the user asks about STI compliance questions, always check whether the question is about Phase 1 (crypto-only, spot, no accounts) or Phase 2 (equities + accounts). The regulatory analyses differ substantially — Phase 2 triggers full IAA analysis because equities are unambiguously securities.
