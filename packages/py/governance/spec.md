# Governance Package Spec

The governance package owns the controls that make autonomous enterprise workflows safe to run: RBAC, approval gates,
tool policy, budgets, audit metadata, and policy citation lookup. It is the enforcement layer between agent plans and
tool execution.

## Package Purpose

- Validate platform roles before API operations.
- Resolve tool risk from `packages/py/governance/risk_registry.yaml`.
- Decide whether a tool call may proceed, must request approval, or must be denied.
- Build and validate ActionReadinessPack artifacts before human-gated actions.
- Enforce run and agent budgets before every tool call.
- Provide policy search as a cited retrieval tool over governed `documents` records.

## RBAC Roles

| Role | Allowed API operations |
| --- | --- |
| `admin` | Full access to runs, approvals, agents, skills, memory, evals, costs, policies, and tool registry changes |
| `operator` | Create runs, pause/resume runs, retry failed runs, decide approvals for assigned business roles |
| `analyst` | Create runs, read runs, read approvals, search memory, view evals and costs |
| `viewer` | Read-only access to dashboards, run traces, skill metadata, eval summaries, and cost summaries |

Business approver roles are separate from platform roles and are checked against approval records:

- `finance-manager`
- `finance-director`
- `commercial-manager`
- `operations-manager`
- `support-lead`

## Permission Matrix

| Operation | `admin` | `operator` | `analyst` | `viewer` |
| --- | --- | --- | --- | --- |
| `runs:create` | yes | yes | yes | no |
| `runs:read` | yes | yes | yes | yes |
| `runs:resume` | yes | yes | no | no |
| `runs:cancel` | yes | yes | no | no |
| `approvals:read` | yes | yes | yes | yes |
| `approvals:decide` | yes | role-gated | no | no |
| `memory:search` | yes | yes | yes | read-only scoped |
| `memory:write` | yes | no | no | no |
| `skills:publish` | yes | no | no | no |
| `evals:run` | yes | yes | no | no |
| `costs:read` | yes | yes | yes | yes |
| `tools:mutate` | yes | no | no | no |

## Approval Flow

1. Agent or verifier identifies a risky proposed action.
2. Governance resolves the tool in `risk_registry.yaml`.
3. Governance checks risk tier, thresholds, role requirements, and budget headroom.
4. If approval is required, the agent writes an ActionReadinessPack.
5. API inserts an `approvals` row with `arp_json`, `approver_role`, `expires_at`, and `requested_by_agent_id`.
6. API pushes the approval to the web approval inbox over WebSocket or server-sent events.
7. Human approver chooses approved, rejected, or lets the request time out.
8. API persists the decision and audit event.
9. Agent resumes through `POST /api/runs/:id/resume` with the decision context.

Destructive actions never execute directly from the autonomous loop. They always stop at the approval gate.

## ActionReadinessPack Schema

The canonical ARP artifact is stored as `approvals.arp_json` and must conform to
`packages/py/artifacts/schemas/action_readiness_pack.yaml`.

Required fields:

- `run_id`: run UUID.
- `action_type`: canonical tool or action name.
- `proposed_action`: human-readable description plus target system and payload preview.
- `evidence`: list of cited facts, source URIs, tool outputs, and retrieval snippets.
- `risk_assessment`: risk tier, confidence, blast radius, reversibility, and known failure modes.
- `policy_citations`: cited policy clauses and compliance status.
- `estimated_impact`: financial impact, systems affected, users affected, and operational impact.
- `reversible`: boolean decision aid for the human reviewer.
- `expires_at`: deadline after which the request times out.

ARP quality gates:

- At least one evidence item is required.
- Financial and destructive actions require at least one policy citation.
- `risk_assessment.tier` must match the tool registry tier.
- `estimated_impact.financial_usd` must be present for financial actions.
- Destructive actions require `reversible=false` or explicit rollback evidence.

## Risk Policy

Risk tiers:

- `read_only`: no approval needed, subject to scope and rate limits.
- `financial`: approval required when the action amount exceeds the registry threshold. A threshold of `0` means
  approval is always required.
- `destructive`: approval always required with `require_arp=true`.

Default behavior:

- Unknown tools are denied.
- Missing risk metadata is denied.
- Tool names must match the registry exactly.
- Tool risk cannot be downgraded at runtime.
- A run cannot exceed `default_policy.max_read_per_run`, `max_financial_per_run`, or `max_destructive_per_run`.

## Budget Enforcement

Before each tool call:

1. Load `runs.total_cost_usd` and the owning agent's `agents.budget_daily_usd`.
2. Add projected model, retrieval, tool compute, storage, and observability cost.
3. If the projected total exceeds the budget, halt the run and notify the user.
4. If the action is financial, compare transaction value with the registry threshold.
5. Write a `run_steps` record for budget checks and denials.

Budget violations set run status to `paused` when human intervention can recover the run, or `failed` when the run cannot
continue.

## Policy Engine

The `policy.search` tool queries the `documents` table with:

- `source = 'policy'`
- optional `vertical` filter
- semantic similarity over `embedding`
- metadata filters from the briefing or skill

Return shape:

```json
{
  "query": "AP approval threshold",
  "vertical": "finance",
  "citations": [
    {
      "policy_id": "POL-AP-20",
      "clause_id": "2.0",
      "excerpt": "Payments above threshold require finance-manager approval.",
      "score": 0.91,
      "uri": "policy://finance/ap/POL-AP-20#2.0"
    }
  ]
}
```

Policy search results must be citation-first. The verifier may not mark a risky action ready if the ARP only contains
uncited summary text.

## Audit Events

Governance writes append-only audit events for:

- Approval requested.
- Approval decided.
- Financial tool executed.
- Destructive action proposed, approved, denied, or executed.
- Budget exceeded.
- Unknown tool denied.
- Policy contradiction detected.

Audit payloads must include `run_id`, `tool_name`, `risk_tier`, `actor_type`, `actor_id`, and trace/span IDs when
available.

## Terraform Destroy Safety Note

The reference failure mode is an autonomous agent executing a destructive infrastructure command without a human gate.
In this repo, any tool equivalent to `terraform destroy`, data deletion, invoice voiding, inventory movement, or
irreversible external mutation is classified as `destructive`, requires an ActionReadinessPack, and cannot proceed
without explicit human approval.
