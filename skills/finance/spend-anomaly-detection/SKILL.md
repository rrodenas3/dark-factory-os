---
name: spend-anomaly-detection
description: Proactively scan synthetic finance data for unusual spend, vendor risk, duplicate payments, or policy drift and surface approval-ready alerts.
version: 0.1.0
owner: finance-ops
risk_tier: medium
required_tools:
  - policy.search
  - memory.search
  - approvals.request
optional_tools:
  - erp.get_invoice
memory_reads:
  - vendor_risk_profile
  - prior_spend_patterns
memory_writes:
  - spend_anomaly_alert
triggers:
  - spend anomaly
  - vendor spike
  - duplicate payment risk
heartbeat:
  cron: "0 8 * * 1-5"
eval_suite:
  - finance_goldens
effort: medium
---

# Goal

Detect spend anomalies before they become finance-control failures.

# Procedure

1. Run on heartbeat or explicit request.
2. Compare current spend patterns against prior vendor and category baselines.
3. Search policy for approval thresholds and exception handling.
4. Produce a ranked anomaly list with evidence and recommended next action.
5. Request approval when a financial or destructive action is recommended.

# Verification

Every alert must include vendor, amount, anomaly reason, policy citation, confidence, and recommended owner.
