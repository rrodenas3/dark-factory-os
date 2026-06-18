---
name: churn-risk-investigation
description: Investigate enterprise churn-risk spikes by correlating support, incidents, product usage, account data, and prior remediation outcomes.
version: 0.1.0
owner: saas-ops
risk_tier: medium
required_tools:
  - analytics.get_incident_metrics
  - telemetry.get_deployments
  - policy.search
optional_tools:
  - memory.search
  - approvals.request
memory_reads:
  - account_risk_profile
  - prior_churn_patterns
memory_writes:
  - churn_risk_outcome
triggers:
  - churn risk
  - enterprise account risk
  - revenue risk spike
eval_suite:
  - saas_goldens
effort: medium
---

# Goal

Explain churn-risk spikes and recommend account, product, support, or incident follow-ups.

# Procedure

1. Gather account health, usage, support, incident, and deployment context.
2. Identify leading signals and likely drivers.
3. Recommend remediation and owner assignments.
4. Request approval before customer-facing commitments or account status changes.
5. Store validated outcome patterns for future investigations.
