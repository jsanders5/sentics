# Sentics Trading Intelligence — Specialized Agents Index

This directory contains specialized agent definitions for building the Sentics Trading Intelligence (STI) platform. Each agent encapsulates deep expertise in a specific domain and can be invoked to guide architecture, design, implementation, and validation decisions.

## Core Product Agents

- [crypto-product-manager.md](crypto-product-manager.md) — Product strategy and user research for crypto trading tools. Validates personas, sets success metrics, prioritizes Phase 1/2 scope, and makes go/no-go recommendations.

## AI & Data Architecture Agents

- [ai-agent-architecture-specialist.md](ai-agent-architecture-specialist.md) — Designs the three-stage AI agent pipeline. Specifies agent coupling, failure modes, scoring formula composition, LLM prompt architecture, cost optimization, and provider evaluation.

- [data-science-ml-specialist.md](data-science-ml-specialist.md) — Validates scoring formulas empirically. Backtests technical filters, calibrates on-chain signal boosts, forecasts hit rates, and monitors post-launch performance.

- [crypto-data-engineering-specialist.md](crypto-data-engineering-specialist.md) — Builds data ETL pipelines from CoinGecko, CryptoPanic, Glassnode, and external APIs. Handles rate limits, fallback chains, on-chain metrics interpretation, and cost tracking.

## Implementation Agents

- [fullstack-crypto-engineer.md](fullstack-crypto-engineer.md) — Implements the web application using Next.js/React. Designs the three-panel dashboard, cache-aware rendering, responsive layouts, performance optimization, and accessibility.

- [infrastructure-devops-specialist.md](infrastructure-devops-specialist.md) — Provisions and operates AWS infrastructure (ECS Fargate, EventBridge, Secrets Manager, RDS). Sets up CI/CD, monitoring, alerting, and incident response procedures.

## Quality & Legal Agents

- [qa-test-automation-specialist.md](qa-test-automation-specialist.md) — Designs testing strategy and verifies go/no-go blockers. Conducts end-to-end pipeline testing, performance testing, accessibility testing, security testing, and sign-off on Section 15 launch conditions.

- [fintech-compliance-specialist.md](fintech-compliance-specialist.md) — Manages regulatory risk and legal compliance. Analyzes securities classification, Investment Advisers Act compliance, disclaimers, Terms of Service, data provider licensing, and GDPR compliance.

- [uiux-designer-fintech.md](uiux-designer-fintech.md) — Designs the dashboard UI/UX for financial products. Creates information hierarchy, responsive layouts, visual language for data status, accessibility-first design, and user research validation.

---

## How to Use These Agents

### Starting an Implementation
When kicking off a component (e.g., Agent 1 implementation), engage the relevant agents in sequence:

1. **Architecture clarity**: Ask `ai-agent-architecture-specialist` about Agent 1's input/output contract, failure modes, and cost optimization.
2. **Data design**: Ask `crypto-data-engineering-specialist` how to fetch and validate the required data.
3. **Formula validation**: Ask `data-science-ml-specialist` if the proposed formula is empirically sound.
4. **Implementation**: Ask `fullstack-crypto-engineer` or backend engineer to build it.
5. **Infrastructure**: Ask `infrastructure-devops-specialist` how to containerize and deploy.
6. **Testing**: Ask `qa-test-automation-specialist` how to validate correctness.

### Product Decisions
For Phase 1/2 scope decisions (e.g., meme coin inclusion, entry type filtering):
1. Engage `crypto-product-manager` to frame the decision and understand user impact
2. Ask `fintech-compliance-specialist` about regulatory implications
3. Consult `data-science-ml-specialist` on how the decision affects hit rate prediction
4. Make the call based on cost/benefit to success metrics

### Launch Readiness
Before launching, use the agents to verify all go/no-go blockers (Section 15 of PRD):
1. `fintech-compliance-specialist` confirms legal sign-off
2. `crypto-data-engineering-specialist` confirms data provider agreements
3. `data-science-ml-specialist` confirms formula validation
4. `qa-test-automation-specialist` confirms all blocker conditions are met

---

## Modification & Maintenance

If you modify an agent definition:
- Update the agent file directly
- Update this MEMORY.md if the agent's role or scope changes
- For breaking changes to an agent's interface/expertise, notify the team
- Test the agent by invoking it on a real design problem before committing

For new agents not yet in this directory:
- Create the .md file in the same format as existing agents
- Add a one-line entry to this MEMORY.md index
- Document the agent's expertise and when to use it
