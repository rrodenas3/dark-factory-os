# Threat Model

Dark Factory OS assumes agentic systems fail through tool misuse, untrusted context, weak identity, poor approvals, and invisible state changes.

## Canonical Incident

The `terraform destroy` failure mode is the reference lesson: an autonomous agent with powerful tools and weak approval gates can erase production state. In this repo, destructive actions are never executed directly by an autonomous loop. They first produce an ActionReadinessPack and wait for human approval.

## Threat Classes

| Threat | Example | Mitigation |
|---|---|---|
| Prompt injection into tools | A policy document tells the agent to ignore approval rules | Tool schemas, policy checks, quoted context boundaries, verifier node |
| Memory poisoning | A false vendor-risk fact is stored and reused | write validation, source trust, consistency checks, contradiction flags |
| Tool misuse | Agent calls payment or void tools incorrectly | risk registry, approval thresholds, ARP requirement |
| Tool forgery | External agent claims capabilities it does not own | A2A card validation later, allowlisted agents first |
| Data leakage | Agent retrieves memory outside user scope | access scopes, RBAC, read filtering gate |
| Silent action | Agent changes business state without user visibility | audit events, run steps, trace timeline, approval inbox |

## Known Gaps

- WebMCP is experimental and browser security models are still evolving.
- A2A signing is not implemented in the first local release.
- UCP is initially a simulator, not a production commerce integration.
- Synthetic data avoids PII, but real deployments need retention, redaction, and data residency policies.
