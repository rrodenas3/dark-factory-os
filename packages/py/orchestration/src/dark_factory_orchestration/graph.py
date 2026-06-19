from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any, Literal, cast

from dark_factory_governance.risk_registry import RiskRegistry, load_risk_registry
from langchain_core.runnables import Runnable, RunnableConfig, RunnableLambda
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from .nodes import (
    approval_gate_node,
    execute_pending_gated_tool,
    memory_writer_node,
    planner_node,
    specialist_node,
    verifier_node,
)
from .state import RunState
from .telemetry import attach_tool_events, node_span, record_outcome, run_span

TerminalRoute = Literal["specialist", "verifier"]
VerifierRoute = Literal["approval_gate", "memory_writer", "__end__"]
CompiledRunGraph = CompiledStateGraph[Any, Any, Any, Any]
StateNode = Callable[[RunState], RunState]
GraphNode = Runnable[RunState, RunState]


def _find_repo_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "packages" / "py" / "governance" / "risk_registry.yaml").exists():
            return candidate
    raise FileNotFoundError("Could not find repository root containing packages/py/governance/risk_registry.yaml")


def _load_registry(registry: RiskRegistry | None) -> RiskRegistry:
    if registry is not None:
        return registry
    registry_path = _find_repo_root(Path(__file__).resolve()) / "packages" / "py" / "governance" / "risk_registry.yaml"
    return load_risk_registry(registry_path)


class RunGraph:
    """LangGraph-backed harness implementing plan -> act -> observe -> verify -> retry.

    The public interface intentionally stays small (`invoke` and `resume`) so API,
    worker, eval, and tests can keep using one runtime abstraction while the
    internals use a real LangGraph StateGraph.
    """

    def __init__(self, risk_registry: RiskRegistry | None = None) -> None:
        self.registry = _load_registry(risk_registry)
        self._checkpointer = MemorySaver()
        self._invoke_graph = self._compile_invoke_graph()
        self._resume_graph = self._compile_resume_graph()

    @property
    def compiled_graph(self) -> CompiledRunGraph:
        return self._invoke_graph

    def invoke(self, initial_state: RunState) -> RunState:
        with run_span(initial_state) as root:
            state = cast(RunState, self._invoke_graph.invoke(initial_state, config=_thread_config(initial_state)))

            attach_tool_events(root, state.get("tool_trace", []))
            record_outcome(root, state)

        return state

    def resume(self, state: RunState, decision: str) -> RunState:
        """Continue a run paused at approval_required after a human decision."""
        if state.get("status") != "approval_required":
            return state
        if decision == "rejected":
            return {
                **state,
                "status": "cancelled",
                "pending_approval": False,
                "pending_tool": None,
                "outcome": {
                    "resolved": False,
                    "approval_required": True,
                    "policy_cited": bool(state.get("policy_citations")),
                    "rejected": True,
                },
            }

        with run_span(state) as root:
            state = cast(RunState, self._resume_graph.invoke(state, config=_thread_config(state)))

            attach_tool_events(root, state.get("tool_trace", []))
            record_outcome(root, state)

        return state

    def _compile_invoke_graph(self) -> CompiledRunGraph:
        graph = StateGraph(RunState)
        graph.add_node("planner", _with_span("planner", lambda state: planner_node(state, self.registry)))
        graph.add_node("specialist", _with_span("specialist", lambda state: specialist_node(state, self.registry)))
        graph.add_node("verifier", _with_span("verifier", verifier_node))
        graph.add_node("approval_gate", _with_span("approval_gate", approval_gate_node))
        graph.add_node("memory_writer", _with_span("memory_writer", memory_writer_node))

        graph.add_edge(START, "planner")
        graph.add_edge("planner", "specialist")
        graph.add_conditional_edges(
            "specialist",
            _route_after_specialist,
            {"specialist": "specialist", "verifier": "verifier"},
        )
        graph.add_conditional_edges(
            "verifier",
            _route_after_verifier,
            {"approval_gate": "approval_gate", "memory_writer": "memory_writer", END: END},
        )
        graph.add_edge("approval_gate", END)
        graph.add_edge("memory_writer", END)
        return graph.compile(checkpointer=self._checkpointer)

    def _compile_resume_graph(self) -> CompiledRunGraph:
        graph = StateGraph(RunState)
        graph.add_node(
            "execute_pending_gated_tool",
            _with_span("specialist", lambda state: execute_pending_gated_tool(state, self.registry)),
        )
        graph.add_node("specialist", _with_span("specialist", lambda state: specialist_node(state, self.registry)))
        graph.add_node("verifier", _with_span("verifier", verifier_node))
        graph.add_node("approval_gate", _with_span("approval_gate", approval_gate_node))
        graph.add_node("memory_writer", _with_span("memory_writer", memory_writer_node))

        graph.add_edge(START, "execute_pending_gated_tool")
        graph.add_edge("execute_pending_gated_tool", "specialist")
        graph.add_conditional_edges(
            "specialist",
            _route_after_specialist,
            {"specialist": "specialist", "verifier": "verifier"},
        )
        graph.add_conditional_edges(
            "verifier",
            _route_after_verifier,
            {"approval_gate": "approval_gate", "memory_writer": "memory_writer", END: END},
        )
        graph.add_edge("approval_gate", END)
        graph.add_edge("memory_writer", END)
        return graph.compile(checkpointer=self._checkpointer)


def _thread_config(state: RunState) -> RunnableConfig:
    return {"configurable": {"thread_id": str(state.get("run_id", "unknown-run"))}}


def _with_span(name: str, node: StateNode) -> GraphNode:
    def wrapped(state: RunState) -> RunState:
        with node_span(name):
            return node(state)

    return cast(GraphNode, RunnableLambda(wrapped))


def _route_after_specialist(state: RunState) -> TerminalRoute:
    return "specialist" if state.get("status") == "running" else "verifier"


def _route_after_verifier(state: RunState) -> VerifierRoute:
    status = state.get("status")
    if status == "approval_required":
        return "approval_gate"
    if status == "completed":
        return "memory_writer"
    return "__end__"


def build_graph(registry: RiskRegistry | None = None) -> RunGraph:
    """Construct a LangGraph-backed RunGraph ready for invoke()."""
    return RunGraph(risk_registry=registry)
