---
name: replenishment-control
description: Monitor stockout and supplier risk, propose replenishment actions, and request approval for inventory-changing operations.
version: 0.1.0
owner: retail-ops
risk_tier: medium
required_tools:
  - analytics.get_campaign_metrics
  - inventory.reorder
  - approvals.request
optional_tools:
  - policy.search
  - memory.search
memory_reads:
  - supplier_risk_profile
  - stockout_history
memory_writes:
  - replenishment_outcome
triggers:
  - stockout risk
  - reorder recommendation
  - supplier delay
eval_suite:
  - retail_goldens
effort: medium
---

# Goal

Prevent stockouts while avoiding over-ordering and policy violations.

# Procedure

1. Inspect demand, inventory, campaign, and supplier context.
2. Estimate stockout risk and business impact.
3. Check policy and supplier constraints.
4. Produce an ActionReadinessPack for any reorder.
5. Request operations approval before inventory-changing actions.
