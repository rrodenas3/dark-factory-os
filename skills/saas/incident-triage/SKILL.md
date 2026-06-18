---
name: incident-triage
description: Correlate support tickets, deployment changes, uptime metrics, and account impact to triage SaaS incidents and schedule follow-up tasks.
version: 0.1.0
owner: saas-ops
risk_tier: medium
required_tools:
  - analytics.get_incident_metrics
  - telemetry.get_deployments
  - policy.search
  - approvals.request
optional_tools:
  - memory.search
memory_reads:
  - incident_history
  - account_risk_profile
memory_writes:
  - incident_outcome
triggers:
  - P1 incident
  - incident spike
  - support ticket surge
heartbeat:
  cron: "*/15 * * * *"
eval_suite:
  - saas_goldens
effort: medium
---

# Goal

Reduce incident time-to-understanding by correlating operational signals and producing a grounded remediation proposal.

# Procedure

1. Gather ticket volume, incident metrics, deployment changes, uptime, and affected account context.
2. Form a root-cause hypothesis with evidence and confidence.
3. Draft remediation and follow-up tasks.
4. Request approval for status-changing, customer-impacting, or destructive actions.
5. Write incident outcome memory after resolution.

# Verification

- Include affected services, affected customers, probable cause, confidence, and next owner.
- Distinguish hypothesis from verified cause.
- Do not change incident status without approval when customer-facing impact exists.
