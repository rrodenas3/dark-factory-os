# Orchestration Package Spec

## Purpose

The orchestration package owns the LangGraph supervisor and specialist handoff graph. It turns a `BriefingScript` into a
durable run, routes work to vertical specialists, checks policy and cost constraints, pauses at approval gates, and writes
traceable state back to Postgres.

Expected imports:

- `langgraph`
- `langchain-anthropic`
- `langchain-mcp-adapters`

## State Schema

The graph state is a `TypedDict` with these fields:

```python
class RunState(TypedDict, total=False):
    run_id: str
    vertical: Literal["retail", "finance", "saas"]
    messages: list[dict[str, object]]
    plan: list[dict[str, object]]
    current_step: dict[str, object] | None
    step_count: int
    cost_usd: float
    status: Literal["pending", "running", "approval_required", "completed", "failed", "cancelled"]
    pending_approval: dict[str, object] | None
    memory_context: list[dict[str, object]]
    skill_name: str
```

## Node Inventory

- `planner`: converts the briefing and selected skill into a step plan.
- `router`: selects the next specialist or terminal verifier based on `vertical`, plan state, and tool risk.
- `retail_specialist`: handles promo rebalance, inventory, pricing, and campaign tasks.
- `finance_specialist`: handles AP exceptions, spend anomalies, vendors, and policy controls.
- `saas_specialist`: handles incidents, churn risk, support tickets, deployments, and account state.
- `verifier`: checks schemas, citations, policy compliance, expected tool trajectory, and stop conditions.
- `approval_gate`: converts risky proposals into ActionReadinessPacks and pauses execution.
- `memory_writer`: writes verified episodic, semantic, and procedural learnings after successful runs.
- `compactor`: summarizes long traces and message history without losing citations or approval context.

## Edge Logic

The graph uses conditional routing:

- `planner -> router` after initial plan creation.
- `router -> finance_specialist` when `vertical == "finance"`.
- `router -> retail_specialist` when `vertical == "retail"`.
- `router -> saas_specialist` when `vertical == "saas"`.
- `*_specialist -> verifier` after every proposed tool action or completed reasoning step.
- `verifier -> approval_gate` when a financial/destructive action requires human review.
- `verifier -> router` when the current step passes and more plan steps remain.
- `verifier -> memory_writer` when the run is complete.
- `memory_writer -> compactor` for durable trace summarization.
- `compactor -> END`.

Unknown verticals fail closed with `status = "failed"` and an audit event.

## Loop Contract

Canonical loop:

`plan -> act -> observe -> verify -> retry`

Stop conditions:

- `step_count >= 100`
- `cost_usd >= budget`
- `status == "approval_required"`
- `status in {"completed", "failed", "cancelled"}`
- verifier detects critical policy violation
- LangGraph recursion limit is reached

Every node increments or preserves `step_count` intentionally. Cost must be attributed after every model call, retrieval,
or tool call.

## Checkpoint Strategy

- Checkpointer: Postgres-backed LangGraph checkpointer.
- `thread_id = run_id`.
- Checkpoints are written after every node.
- Approval pauses must be resumable without replaying unsafe tool calls.
- Long-running jobs are executed by the worker process, not the API process.

## Human-In-The-Loop

LangGraph is configured with:

```python
interrupt_before = ["approval_gate"]
```

The approval gate returns a pending ActionReadinessPack, writes an `approvals` row, sets run status to
`approval_required`, and stops. Resume happens through `POST /api/runs/:id/resume` after an approval decision has been
persisted.

## Observability

Each node emits an OTEL span containing:

- `run_id`
- `node_name`
- `vertical`
- `skill_name`
- `step_count`
- `cost_usd`
- `status`
- `pending_approval_id` when applicable
