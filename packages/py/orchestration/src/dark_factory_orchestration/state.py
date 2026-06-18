from __future__ import annotations

from typing import Any, TypedDict


class RunState(TypedDict, total=False):
    """Typed state for a Dark Factory OS run.

    Production: backed by LangGraph Postgres checkpointer with thread_id = run_id.
    Demo: backed by MemorySaver for local `docker compose up`.
    """

    run_id: str
    vertical: str  # "finance" | "retail" | "saas"
    skill_name: str
    plan: list[str]  # ordered tool names the planner resolved
    current_step: int
    step_count: int
    cost_usd: float
    status: str  # "running" | "paused" | "approval_required" | "completed" | "failed"
    pending_approval: bool
    approval_role: str | None
    pending_tool: str | None  # gated tool awaiting human approval before dispatch
    tool_trace: list[dict[str, Any]]  # [{tool_name, success, latency_ms, cost_usd, executed?}]
    memory_context: list[dict[str, Any]]
    policy_citations: list[str]
    outcome: dict[str, Any] | None
    error: str | None
