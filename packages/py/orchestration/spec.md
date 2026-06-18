# Orchestration Package Spec

Purpose: LangGraph supervisor plus finance, retail, and SaaS specialist handoff graph.

State fields: `run_id`, `vertical`, `messages`, `plan`, `current_step`, `step_count`, `cost_usd`, `status`, `pending_approval`, `memory_context`, `skill_name`.

Nodes: `planner`, `router`, `finance_specialist`, `retail_specialist`, `saas_specialist`, `verifier`, `approval_gate`, `memory_writer`, `compactor`.

Stop conditions: max steps, max cost, approval requirement, recursion limit, critical policy violation.

Checkpoint strategy: Postgres-backed checkpointer with `thread_id = run_id`.
