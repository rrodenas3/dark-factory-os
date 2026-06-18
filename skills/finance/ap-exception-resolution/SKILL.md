---
name: ap-exception-resolution
description: Resolve finance AP exceptions by gathering invoice, PO, vendor, policy, and approval context; escalate when policy confidence is low or thresholds are crossed.
version: 0.1.0
owner: finance-ops
risk_tier: medium
required_tools:
  - erp.get_invoice
  - erp.get_purchase_order
  - policy.search
  - approvals.request
optional_tools:
  - erp.post_payment
  - erp.create_credit_memo
memory_reads:
  - vendor_risk_profile
  - prior_exception_patterns
memory_writes:
  - exception_outcome
triggers:
  - invoice mismatch
  - duplicate invoice
  - missing PO
eval_suite:
  - finance_goldens
effort: medium
---

# Goal

Resolve routine AP exceptions safely while preserving policy compliance, auditability, and finance-manager trust.

# Context

The agent may inspect invoice, purchase order, vendor, prior exception, and policy context. It may propose financial actions, but payment, credit memo, and void actions are governed by the risk registry.

# Procedure

1. Gather invoice, purchase order, vendor, prior exception, and policy context.
2. Classify the discrepancy as duplicate invoice, amount mismatch, missing PO, vendor risk, or policy ambiguity.
3. Compare invoice values against PO, receiving records, and policy clauses.
4. If the action is safe, reversible, and below threshold, propose auto-resolution with citations.
5. If the action is financial, destructive, ambiguous, or above threshold, write an ActionReadinessPack and request approval.

# Verification

- Cite at least one policy clause for every resolution.
- Confirm the expected tool sequence matches the exception type.
- Never execute financial or destructive tools without approval.
- Write `exception_outcome` memory only after the verifier passes.

# Failure Handling

If invoice, PO, or policy context is missing, escalate with a ConsultationRequestPack rather than guessing.
