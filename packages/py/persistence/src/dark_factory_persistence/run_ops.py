from __future__ import annotations

from typing import Any, cast
from uuid import UUID

from dark_factory_persistence import ApprovalRepository, RunRecord, RunRepository


async def append_new_tool_steps(
    runs: RunRepository,
    run_id: UUID,
    state: dict[str, Any],
    persisted_len: int,
) -> int:
    trace = list(state.get("tool_trace", []))
    for step in trace[persisted_len:]:
        await runs.append_step(
            run_id=run_id,
            step_type="act",
            status="ok" if step.get("success", False) else "error",
            tool_name=str(step.get("tool_name")),
            tool_risk_class=str(step.get("risk_tier")) if step.get("risk_tier") else None,
            output_json=step,
            latency_ms=int(step.get("latency_ms", 0)),
            cost_usd=float(step.get("cost_usd", 0.0)),
        )
    return len(trace)


async def persist_run_result(
    runs: RunRepository,
    approvals: ApprovalRepository,
    run: RunRecord,
    state: dict[str, Any],
) -> None:
    persisted_len = int((run.checkpoint_json or {}).get("persisted_trace_len", 0))
    persisted_len = await append_new_tool_steps(runs, run.id, state, persisted_len)

    status = cast(Any, state.get("status", "failed"))
    await runs.save_checkpoint(
        run.id,
        status=status,
        checkpoint=dict(state),
        total_cost_usd=float(state.get("cost_usd", 0.0)),
        step_count=int(state.get("step_count", 0)),
        persisted_trace_len=persisted_len,
    )

    if status == "approval_required" and state.get("pending_tool"):
        existing = await approvals.list_pending_for_run(run.id)
        if not existing:
            await approvals.create(
                run_id=run.id,
                action_type=str(state["pending_tool"]),
                action_payload={
                    "tool_trace": state.get("tool_trace", []),
                    "policy_citations": state.get("policy_citations", []),
                    "approval_role": state.get("approval_role"),
                },
                approver_role=str(state.get("approval_role") or "operator"),
            )


def state_from_run(run: RunRecord, *, initial: bool = False) -> dict[str, Any]:
    if not initial and run.checkpoint_json:
        data = dict(run.checkpoint_json)
        data.pop("persisted_trace_len", None)
        return data

    vertical = run.vertical or "finance"
    return {
        "run_id": str(run.id),
        "vertical": vertical,
        "skill_name": run.workflow_key,
        "outcome": {"briefing": run.briefing_json},
    }
