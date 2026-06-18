from __future__ import annotations

from typing import Any

from dark_factory_governance.risk_registry import RiskRegistry, ToolPolicy
from dark_factory_tool_adapters import ToolCall, dispatch

from .state import RunState

MAX_STEPS = 100
MAX_COST_USD = 5.00

_SKILL_PLANS: dict[str, list[str]] = {
    "ap-exception-resolution": ["erp.get_invoice", "erp.get_purchase_order", "policy.search", "memory.search"],
    "spend-anomaly-detection": ["memory.search", "policy.search"],
    "promo-rebalance": ["analytics.get_campaign_metrics", "policy.search", "memory.search", "pricing.set_price_band"],
    "replenishment-control": ["analytics.get_campaign_metrics", "memory.search", "inventory.reorder"],
    "incident-triage": [  # noqa: E501
        "analytics.get_incident_metrics",
        "telemetry.get_deployments",
        "memory.search",
        "incident.change_status",
    ],
    "churn-risk-investigation": ["analytics.get_incident_metrics", "memory.search", "policy.search"],
}


def planner_node(state: RunState) -> RunState:
    """Resolve the tool sequence from the skill manifest.

    Computational (deterministic) control — no LLM call.
    The skill manifest declares required_tools; the planner orders them.
    In production this node adds context-sensitive reordering via an LLM call.
    """
    skill_name = state.get("skill_name", "ap-exception-resolution")
    plan = _SKILL_PLANS.get(skill_name, ["policy.search", "memory.search"])
    return {
        **state,
        "plan": plan,
        "current_step": 0,
        "step_count": 0,
        "cost_usd": 0.0,
        "status": "running",
        "tool_trace": [],
        "memory_context": [],
        "policy_citations": [],
        "pending_approval": False,
        "approval_role": None,
        "outcome": None,
        "error": None,
    }


def specialist_node(state: RunState, risk_registry: RiskRegistry) -> RunState:
    """Execute the next tool in the plan.

    Computational control: checks risk tier BEFORE calling.
    Financial/destructive tools set pending_approval and stop — they must
    be unblocked by a human gate (interrupt_before in the real LangGraph graph).
    """
    plan: list[str] = state.get("plan", [])
    step = state.get("current_step", 0)
    tool_trace: list[dict[str, Any]] = list(state.get("tool_trace", []))
    cost = state.get("cost_usd", 0.0)
    step_count = state.get("step_count", 0)
    policy_citations: list[str] = list(state.get("policy_citations", []))

    if step >= len(plan):
        return {**state, "status": "completed"}

    if step_count >= MAX_STEPS or cost >= MAX_COST_USD:
        return {**state, "status": "failed", "error": f"Budget exceeded: steps={step_count} cost=${cost:.4f}"}

    tool_name = plan[step]

    try:
        policy: ToolPolicy = risk_registry.require_tool(tool_name)
    except KeyError:
        msg = f"Tool '{tool_name}' not in risk registry — denied by default policy"
        return {**state, "status": "failed", "error": msg}

    if policy.risk_tier in ("financial", "destructive"):
        result = dispatch(ToolCall(name=tool_name, args={}))
        tool_trace.append(
            {
                "tool_name": tool_name,
                "risk_tier": policy.risk_tier,
                "success": result.success,
                "latency_ms": result.latency_ms,
                "cost_usd": result.cost_usd,
                "requires_approval": True,
            }
        )
        return {
            **state,
            "current_step": step + 1,
            "step_count": step_count + 1,
            "cost_usd": cost + result.cost_usd,
            "tool_trace": tool_trace,
            "policy_citations": policy_citations,
            "status": "approval_required",
            "pending_approval": True,
            "approval_role": policy.approver_role,
        }

    result = dispatch(ToolCall(name=tool_name, args=_build_args(tool_name, state)))
    step_trace: dict[str, Any] = {
        "tool_name": tool_name,
        "risk_tier": policy.risk_tier,
        "success": result.success,
        "latency_ms": result.latency_ms,
        "cost_usd": result.cost_usd,
        "requires_approval": False,
    }

    if result.success and tool_name == "policy.search" and isinstance(result.output, dict):
        for match in result.output.get("matches", []):
            if isinstance(match, dict):
                citation = f"{match.get('policy_id', '')} §{match.get('clause_id', '')}"
                if citation not in policy_citations:
                    policy_citations.append(citation)

    tool_trace.append(step_trace)
    return {
        **state,
        "current_step": step + 1,
        "step_count": step_count + 1,
        "cost_usd": cost + result.cost_usd,
        "tool_trace": tool_trace,
        "policy_citations": policy_citations,
        "status": "running",
    }


def verifier_node(state: RunState) -> RunState:
    """Verify loop-exit conditions.

    Computational control: checks policy citations, step counts, cost.
    Returns 'completed' when all planned steps executed with at least one policy citation.
    Returns 'failed' on missing citations.
    """
    plan: list[str] = state.get("plan", [])
    step = state.get("current_step", 0)
    citations = state.get("policy_citations", [])
    status = state.get("status", "running")

    if status in ("approval_required", "failed"):
        return state

    if step < len(plan):
        return {**state, "status": "running"}

    if not citations:
        return {**state, "status": "failed", "error": "Verifier: no policy cited — run fails grounding check"}

    outcome: dict[str, Any] = {
        "resolved": True,
        "approval_required": state.get("pending_approval", False),
        "policy_cited": bool(citations),
        "citations": citations,
        "tool_count": state.get("step_count", 0),
        "cost_usd": state.get("cost_usd", 0.0),
    }
    return {**state, "status": "completed", "outcome": outcome}


def approval_gate_node(state: RunState) -> RunState:
    """Approval gate — in a real LangGraph graph this node is decorated with interrupt_before.

    The graph pauses here; the operator calls /api/runs/{id}/resume to unblock.
    In the test harness we skip the interrupt and record the requirement.
    """
    return {
        **state,
        "outcome": {
            "resolved": False,
            "approval_required": True,
            "policy_cited": bool(state.get("policy_citations")),
            "approval_role": state.get("approval_role"),
            "tool_trace": state.get("tool_trace", []),
        },
    }


def memory_writer_node(state: RunState) -> RunState:
    """Write outcome to episodic memory after a successful or approval-halted run.

    Production: inserts into memory_items + episodic_log via Postgres.
    """
    return state


def _build_args(tool_name: str, state: RunState) -> dict[str, Any]:
    args: dict[str, Any] = {}
    if tool_name == "erp.get_invoice":
        args["invoice_id"] = state.get("outcome", {}) or {}
    if tool_name in ("analytics.get_campaign_metrics", "analytics.get_incident_metrics", "telemetry.get_deployments"):
        vertical = state.get("vertical", "")
        args["service"] = "billing-api" if vertical == "saas" else vertical
    return args
