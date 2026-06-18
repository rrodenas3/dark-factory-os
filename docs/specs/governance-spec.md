# Governance Spec

## Roles

Platform roles:

- `admin`: full platform control.
- `operator`: run operations and retries.
- `analyst`: create and inspect runs.
- `viewer`: read-only access.

Business approver roles:

- `finance-manager`
- `finance-director`
- `commercial-manager`
- `operations-manager`
- `support-lead`

## Approval Flow

1. Agent proposes a risky action.
2. Verifier checks risk registry and policy.
3. Agent writes an ActionReadinessPack.
4. API inserts an approval row.
5. UI shows the approval card.
6. Human approves, rejects, or lets it time out.
7. Run resumes or closes with rejection.

## Budget Enforcement

Before every tool call, check run cost, agent daily budget, max steps, and tool call counts. Budget violations pause the run and emit audit events.

## Tool Policy

Unknown tools are denied. Destructive tools always require approval. Financial tools use thresholds. Read-only tools are limited by rate and scope.
