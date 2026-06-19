# Agent Runtime Spec

## Loop

```text
plan -> act -> observe -> verify -> retry -> approve or complete
```

## State

The supervisor state contains:

- `run_id`
- `vertical`
- `messages`
- `plan`
- `current_step`
- `step_count`
- `cost_usd`
- `status`
- `pending_approval`
- `memory_context`
- `skill_name`

## Nodes

- `planner`: decomposes request and selects skill.
- `router`: routes to finance, retail, or SaaS specialist.
- `finance_specialist`: handles AP, spend, vendor, and policy workflows.
- `retail_specialist`: handles pricing, inventory, campaign, and commerce workflows.
- `saas_specialist`: handles incidents, churn risk, telemetry, and support workflows.
- `verifier`: checks grounding, schemas, policy, cost, and risk.
- `approval_gate`: emits ActionReadinessPack and pauses.
- `memory_writer`: writes validated outcomes and episodic events.
- `compactor`: summarizes long context after task completion.

## Stop Conditions

- `step_count >= 100`
- `cost_usd >= budget`
- `status == approval_required`
- recursion limit exceeded
- verifier returns critical policy violation

## Checkpointing

Use Postgres-backed LangGraph checkpoints with `thread_id = run_id` in Docker and production (`DFOS_LANGGRAPH_CHECKPOINTS=postgres`). Unit tests and local isolated graph construction default to `memory` mode for deterministic execution. Use Temporal only for long-running workflows that need durable timers, retries, or external wait states.
