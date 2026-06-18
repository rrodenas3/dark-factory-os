# Agent Operating Rules

All agents in this repository follow the canonical loop:

```text
plan -> act -> observe -> verify -> retry -> approve or complete
```

## Stop Conditions

- `recursion_limit = 50`
- `max_steps = 100`
- `max_cost_usd = 5.00` for local demo runs unless a BriefingScript overrides it.
- Stop immediately when a tool returns a policy violation, budget violation, or approval requirement.

## Risk Taxonomy

Tool risk classes:

- `read_only`: can run without approval when within rate limits.
- `financial`: approval required above configured thresholds.
- `destructive`: always requires human approval and an ActionReadinessPack.

Tool policies live in `packages/py/governance/risk_registry.yaml`.

## Memory Rules

- Every skill must declare memory reads and writes in `SKILL.md` frontmatter.
- Working memory is run-scoped.
- Episodic memory is append-only.
- Semantic memory requires write validation.
- Procedural memory lives in skills and specs.
- Low-trust or unverified memory cannot justify high-risk actions.

## Approval Rules

Raise an ActionReadinessPack when:

- The action is destructive.
- The action is financial and above threshold.
- Policy confidence is low.
- Evidence conflicts.
- The action affects external customers, payments, pricing, inventory, production incidents, or compliance records.

Proceed without approval only when the tool is read-only, the policy check passes, and the run remains within step and cost limits.

## Safety Note

The `terraform destroy` incident is treated as the canonical failure mode: powerful tools plus weak gates can erase production state. Dark Factory OS models every destructive action as a proposal first and an execution only after approval.
