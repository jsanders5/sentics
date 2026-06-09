---
name: sti-phase1-regulatory-posture
description: STI Phase 1 regulatory risk posture — RIA registration analysis, securities classification tiers for top-50 coins, pre-trade reference risk flag, and go/no-go conditions established in Open Question #1 assessment
metadata:
  type: project
---

Open Questions #1, #7, and #10 assessed. #1 and #7 assessed on 2026-06-08; #10 assessed on 2026-06-09.

---

**Q7 — Glassnode Licensing (assessed 2026-06-09): SKIP on-chain signals for Phase 1.**

The PRD's pricing assumption of ~$39/month for Glassnode is materially wrong. Current Glassnode structure:
- Free tier: "strictly personal, revocable, non-transferable" — commercial product use explicitly prohibited
- Advanced plan (~$26/month): does NOT include programmatic API access
- API access requires Professional plan ($999/month) PLUS a paid API add-on at custom pricing

Programmatic API access is required for Agent 2's automated 6-hour pipeline. Manual dashboard access is not viable.

CoinGecko on-chain data is NOT a substitute — CoinGecko's on-chain metrics are DEX/pool-focused (liquidity, token trading on DEXes via GeckoTerminal), not blockchain-level analytics (active addresses per Glassnode's definition, exchange net flows as net supply signal, whale transaction counts). The specific metrics Agent 2 needs do not exist in CoinGecko's free or commercial API.

Recommendation: Remove the on-chain component from Phase 1 scoring. Redistribute the 15% weight to technical alignment (50% → 57%) and category momentum (35% → 43%), or score out of 85 normalized to 100. Revisit Glassnode or alternative vendors (Santiment, Nansen) in Phase 1.1 or Phase 2 after revenue is validated.

PRD already includes a self-limiting clause at Section 13: "Remove the on-chain component from scoring if < 20% of top-50 coins have usable data." Given API access costs $999+/month, this condition is effectively met — treat it as triggered.

Budget impact: saves the erroneously assumed $39/month; prevents a $999+/month spend that is unjustifiable for a 15% scoring component in an unmonetized Phase 1.

---

**Q10 — Pre-Trade Planning Reference Legal Review (assessed 2026-06-09): DEFER to Phase 1.1.**

Legal risk assessment: HIGH. The pre-trade reference as spec'd in Section 8.6 does not qualify for the publisher's exclusion because it crosses from general commentary into trade structuring guidance. Key factors:

1. Specific dollar levels ("$2.45–$2.55 area") are trade-actionable — a trader can set a limit order or stop loss directly from this number. "Prior resistance area" is commentary; "$2.45" is a price target.

2. R:R ratio + ATR + invalidation level together constitute a functional position sizing framework. A 2.0:1 R:R with a known invalidation level allows calculation of position size. This is the kind of output a registered broker-dealer research desk provides — not a general publisher.

3. Timing risk is critical: the pre-trade reference appears simultaneously with a buy candidate signal, not independently. The combined output reads as: "this coin is a buy, it faces resistance at $2.45, your stop is $2.10, minimum R:R is 2:1." That is a trade recommendation, not commentary.

4. The pre-trade reference would compromise the publisher's exclusion defense for the ENTIRE product, not just that section. If a regulator or plaintiff challenges the pre-trade fields as investment advice, they look at the whole product holistically. One feature that looks like regulated advice can invalidate the defense for the core dashboard.

5. The Section 12.2 disclaimer language is well-written but insufficient on its own. Disclaimers do not convert regulated advice into non-regulated commentary. Courts and the SEC look at substance over form.

Deferral rationale: Open Question #12 in the PRD already asks whether this should be Phase 1 or Phase 1.1 — the right answer is Phase 1.1. The core dashboard (ranked candidates, rationale text, confidence tiers) has a clean publisher's exclusion defense. Adding the pre-trade reference before getting separate counsel sign-off on that specific feature would delay core Phase 1 launch AND introduce risk to the whole product.

If included in Phase 1: requires SEPARATE written sign-off from external counsel specifically addressing the pre-trade reference fields (distinct from the core dashboard sign-off required by Q1). This is a hard blocking condition — not satisfied by the Q1 sign-off alone.

---

Open Question #1 was assessed on 2026-06-08. Core conclusions:

**RIA Registration**: Medium risk, defensible. STI's core dashboard qualifies for the publisher's exclusion (Lowe v. SEC, 1985) because output is identical for all users, no personalization, no position sizing, no fiduciary relationship. External counsel written sign-off required before launch.

**Pre-Trade Planning Reference (Section 8.6)**: Elevated risk — provides specific price levels (resistance zones, invalidation levels), ATR, and R:R ratios that look like trade structuring advice, not general commentary. This feature must NOT go live without a SEPARATE written legal sign-off from external counsel. It is blocked under Open Question #10 in the PRD. This is a hard line — do not recommend clearing this feature alongside the core dashboard.

**Securities Classification Tiers**:
- Tier 1 (Low risk, include freely): BTC, ETH, LTC, DOGE, SHIB, PEPE
- Tier 2 (Medium risk, include with standard addendum): BNB, AVAX, DOT, LINK, UNI, AAVE, MKR, ARB, OP, APT, GRT, RNDR, FET, TAO, INJ
- Tier 3 (Elevated risk, include with coin-specific enhanced disclaimer): XRP, SOL, ADA, MATIC/POL, ATOM, ALGO, NEAR, FIL, HBAR, FLOW, ICP, SAND, MANA, AXS, CHZ, TON (special TON history), TRX (special fraud context)
- ICP, MANA, AXS: weakest utility arguments in Tier 3; counsel should assess whether exclusion is preferable

**Tier 3 Enhanced Disclaimer**: Each Tier 3 coin in the detail panel must display a coin-specific disclaimer noting unresolved regulatory classification. External counsel must draft per-coin language — this assessment's language is a template, not approved text.

**CFTC**: Clean for Phase 1 spot-only scope. Must revisit if futures/perps added in Phase 2+.

**Money Transmission**: Clean — STI holds no funds, no custody, no exchange account access.

**Subscription Tier Transition**: Phase 1 legal sign-off does NOT cover the paid subscription tier. Separate legal review required before monetization launches.

**Exclusion List Capability**: Engineering must build a technical capability to exclude specific coins from the universe within 24 hours without a code deployment. Legal dependency for rapid response to new enforcement actions.

**Why:** Regulatory environment is favorable in 2026 (SEC under Atkins, enforcement actions dropped), but no binding court ruling has declared most altcoins non-securities. Primary risk is private civil litigation, not SEC enforcement.

**How to apply:** When advising on Phase 1 scope, coin universe decisions, or feature additions — always check whether the feature adds specificity (price levels, personalization, position sizing) that erodes the publisher's exclusion defense. Always flag the pre-trade reference section as requiring separate legal sign-off. Never sign off on adding futures/derivatives without noting CFTC registration implications.
