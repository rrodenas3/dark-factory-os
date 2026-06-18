from __future__ import annotations

from pathlib import Path

from dark_factory_governance.risk_registry import RiskRegistry, load_risk_registry

from .nodes import (
    approval_gate_node,
    memory_writer_node,
    planner_node,
    specialist_node,
    verifier_node,
)
from .state import RunState

_DEFAULT_REGISTRY_PATH = Path(__file__).resolve().parents[5] / "packages" / "py" / "governance" / "risk_registry.yaml"


def _load_registry(registry: RiskRegistry | None) -> RiskRegistry:
    if registry is not None:
        return registry
    if _DEFAULT_REGISTRY_PATH.exists():
        return load_risk_registry(_DEFAULT_REGISTRY_PATH)
    raise FileNotFoundError(f"Risk registry not found at {_DEFAULT_REGISTRY_PATH}")


class RunGraph:
    """Deterministic harness graph implementing plan → act → observe → verify → retry.

    Mirrors the LangGraph StateGraph interface so swapping in real LangGraph
    (with Postgres checkpointer + interrupt_before on approval_gate_node)
    requires only replacing this class with the langgraph.graph.StateGraph builder.

    Node map:
        planner → specialist (loop) → verifier → [approval_gate | memory_writer]

    Stop conditions (enforced in specialist_node):
        - max_steps = 100
        - max_cost_usd = 5.00
        - approval_required (financial/destructive tool)
        - critical policy violation
    """

    def __init__(self, risk_registry: RiskRegistry | None = None) -> None:
        self.registry = _load_registry(risk_registry)

    def invoke(self, initial_state: RunState) -> RunState:
        state = planner_node(initial_state)
        plan = state.get("plan", [])

        for _ in range(len(plan) + 1):
            status = state.get("status", "running")
            if status in ("completed", "failed", "approval_required"):
                break
            state = specialist_node(state, self.registry)

        state = verifier_node(state)

        if state.get("status") == "approval_required":
            state = approval_gate_node(state)
        elif state.get("status") == "completed":
            state = memory_writer_node(state)

        return state


def build_graph(registry: RiskRegistry | None = None) -> RunGraph:
    """Construct a RunGraph ready for invoke().

    Pass a pre-loaded RiskRegistry to skip filesystem lookup (useful in tests).
    Production: replace RunGraph with a langgraph.graph.StateGraph that uses
    MemorySaver (dev) or AsyncPostgresSaver (production) as the checkpointer.
    """
    return RunGraph(risk_registry=registry)
