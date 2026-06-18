---
name: promo-rebalance
description: Diagnose retail or CPG promotion underperformance and propose margin, pricing, inventory, or channel rebalancing actions with approval gates.
version: 0.1.0
owner: retail-ops
risk_tier: medium
required_tools:
  - analytics.get_campaign_metrics
  - pricing.set_price_band
  - inventory.reorder
  - approvals.request
optional_tools:
  - policy.search
  - memory.search
  - ucp.propose_checkout
memory_reads:
  - campaign_history
  - price_band_policy
memory_writes:
  - promo_rebalance_outcome
triggers:
  - margin drop
  - campaign underperforming
  - promo rebalance
eval_suite:
  - retail_goldens
effort: medium
---

# Goal

Improve promotional margin while protecting in-stock rate, policy compliance, and customer experience.

# Context

Retail actions can affect pricing, inventory, suppliers, and customer-facing commerce. Price and reorder actions require explicit approval under the risk registry.

# Procedure

1. Gather campaign metrics, price bands, inventory, supplier risk, and historical campaign memory.
2. Identify the likely root cause: demand shift, stockout risk, margin compression, channel mix, supplier delay, or pricing drift.
3. Propose a rebalance plan with expected margin, inventory, and customer impact.
4. Write an ActionReadinessPack for price, reorder, checkout, or cross-channel changes.
5. Request approval and execute only after approval.

# Verification

- Never change price above approved band.
- Never reorder inventory without operations approval.
- Include margin, stockout, and customer impact estimates.
- Label UCP-style commerce actions as simulator-backed unless production integration exists.
