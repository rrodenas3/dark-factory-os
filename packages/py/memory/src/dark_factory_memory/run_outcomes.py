from __future__ import annotations

from typing import Any

from .models import MemoryItem

WRITABLE_RUN_STATUSES = {"completed", "approval_required"}


def build_run_outcome_memory(state: dict[str, Any]) -> MemoryItem | None:
    """Build an episodic memory item from a completed or approval-halted run."""
    status = str(state.get("status", ""))
    if status not in WRITABLE_RUN_STATUSES:
        return None

    run_id = str(state.get("run_id") or "unknown-run")
    vertical = str(state.get("vertical") or "general")
    skill_name = str(state.get("skill_name") or "unknown-skill")
    step_count = int(state.get("step_count", 0))
    tool_trace = list(state.get("tool_trace", []))

    return MemoryItem(
        namespace=f"{vertical}.run_outcomes",
        entity_key=f"{run_id}:{status}:{step_count}",
        memory_type="episodic",
        content={
            "run_id": run_id,
            "vertical": vertical,
            "skill_name": skill_name,
            "status": status,
            "summary": _summary(skill_name, status, tool_trace),
            "policy_citations": list(state.get("policy_citations", [])),
            "approval_required": bool(state.get("pending_approval", status == "approval_required")),
            "approval_role": state.get("approval_role"),
            "pending_tool": state.get("pending_tool"),
            "tool_names": [str(step.get("tool_name")) for step in tool_trace if isinstance(step, dict)],
            "step_count": step_count,
            "cost_usd": float(state.get("cost_usd", 0.0)),
            "outcome": state.get("outcome"),
            "error": state.get("error"),
        },
        access_scope="team",
        source_trust=0.9,
        consistency_verified=True,
    )


def _summary(skill_name: str, status: str, tool_trace: list[Any]) -> str:
    tool_names = [str(step.get("tool_name")) for step in tool_trace if isinstance(step, dict) and step.get("tool_name")]
    if not tool_names:
        return f"{skill_name} run reached {status}."
    return f"{skill_name} run reached {status} after tools: {', '.join(tool_names)}."
