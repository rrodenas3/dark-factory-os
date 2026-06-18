# Product Spec

Dark Factory OS is a governed agentic operations platform for enterprise workflows. It gives each user a personalized workbench where agents can investigate, propose, request approval, execute safe actions, and learn from outcomes.

## Actors

- Finance manager: reviews AP exceptions, spend anomalies, approvals, and audit trails.
- Commercial manager: reviews promo, pricing, inventory, and margin actions.
- SaaS ops lead: reviews incidents, support signals, churn risk, and follow-up tasks.
- Operator: monitors runs, retries, approvals, traces, and failures.
- Admin / skill publisher: manages tools, skills, policies, budgets, evals, and agent identities.

## Core Workflows

1. User or cron trigger creates a run from a BriefingScript.
2. Supervisor selects a vertical specialist and skill.
3. Specialist retrieves policy, memory, structured data, and documents.
4. Verifier checks grounding, policy, budget, and tool risk.
5. Low-risk actions complete; risky actions produce an ActionReadinessPack.
6. Human approval resumes or rejects the run.
7. Trace, audit, cost, eval, and memory updates are written.
8. Repeated learnings can propose skill improvements.

## Success Criteria

- All three verticals share one platform architecture.
- Every material action is attributable to a user, agent, tool, and run.
- Risky actions are proposal-first.
- Skills are portable, versioned, and evaluated.
- Evals and costs are visible in the product surface.
- Experimental protocols are labeled honestly.
