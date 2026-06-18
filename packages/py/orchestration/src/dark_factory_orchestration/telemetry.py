"""OTEL tracing for the Dark Factory OS orchestration loop.

Uses the OpenTelemetry GenAI semantic conventions (experimental, 2026-07).
Opt-in: set OTEL_SEMCONV_STABILITY_OPT_IN=gen_ai_latest_experimental.
In production wire an OTLP exporter; in demo mode spans go to a NoOpTracer.
"""
from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

from opentelemetry import trace
from opentelemetry.trace import NonRecordingSpan, Span, Status, StatusCode, Tracer

if TYPE_CHECKING:
    from .state import RunState

# Gen AI semantic convention attribute names (OTEL spec, 2026-07 experimental).
# Defined as constants because opentelemetry-semantic-conventions 0.63b does not
# yet ship the gen_ai attribute module; use these until the stable 1.x release.
GEN_AI_SYSTEM = "gen_ai.system"
GEN_AI_OPERATION_NAME = "gen_ai.operation.name"
GEN_AI_TOOL_NAME = "gen_ai.tool.name"
GEN_AI_TOOL_RISK_TIER = "gen_ai.tool.call.risk_tier"
GEN_AI_TOOL_REQUIRES_APPROVAL = "gen_ai.tool.call.requires_approval"
GEN_AI_RUN_ID = "dfos.run.id"
GEN_AI_VERTICAL = "dfos.run.vertical"
GEN_AI_SKILL_NAME = "dfos.run.skill_name"
GEN_AI_PLAN_LENGTH = "dfos.run.plan_length"
GEN_AI_STEP_COUNT = "dfos.run.step_count"
GEN_AI_COST_USD = "dfos.run.cost_usd"
GEN_AI_STATUS = "dfos.run.status"

_TRACER_NAME = "dark_factory.orchestration"
_SCHEMA_URL = "https://opentelemetry.io/schemas/1.27.0"


def get_tracer() -> Tracer:
    return trace.get_tracer(_TRACER_NAME, schema_url=_SCHEMA_URL)


@contextmanager
def run_span(state: RunState) -> Generator[Span, None, None]:
    """Root span covering one full RunGraph.invoke() call."""
    tracer = get_tracer()
    with tracer.start_as_current_span(
        "dfos.run",
        attributes={
            GEN_AI_SYSTEM: "dark_factory_os",
            GEN_AI_OPERATION_NAME: "plan_act_verify",
            GEN_AI_RUN_ID: state.get("run_id", ""),
            GEN_AI_VERTICAL: state.get("vertical", ""),
            GEN_AI_SKILL_NAME: state.get("skill_name", ""),
        },
    ) as span:
        yield span


@contextmanager
def node_span(name: str) -> Generator[Span, None, None]:
    """Child span for a single graph node execution."""
    tracer = get_tracer()
    with tracer.start_as_current_span(
        f"dfos.node.{name}",
        attributes={
            GEN_AI_SYSTEM: "dark_factory_os",
            GEN_AI_OPERATION_NAME: name,
        },
    ) as span:
        yield span


def tool_event(span: Span, tool_name: str, risk_tier: str, requires_approval: bool, cost_usd: float) -> None:
    """Add a tool-call event to the current span (aligns with gen_ai.tool.call spec)."""
    span.add_event(
        "gen_ai.tool.call",
        attributes={
            GEN_AI_TOOL_NAME: tool_name,
            GEN_AI_TOOL_RISK_TIER: risk_tier,
            GEN_AI_TOOL_REQUIRES_APPROVAL: requires_approval,
            "gen_ai.tool.call.cost_usd": cost_usd,
        },
    )


def record_outcome(span: Span, final_state: RunState) -> None:
    """Annotate the root span with run outcome metrics."""
    status = final_state.get("status", "unknown")
    if isinstance(span, NonRecordingSpan):
        return
    span.set_attributes(
        {
            GEN_AI_PLAN_LENGTH: len(final_state.get("plan", [])),
            GEN_AI_STEP_COUNT: final_state.get("step_count", 0),
            GEN_AI_COST_USD: final_state.get("cost_usd", 0.0),
            GEN_AI_STATUS: status,
        }
    )
    if status == "failed":
        span.set_status(Status(StatusCode.ERROR, final_state.get("error", "unknown error")))
    else:
        span.set_status(Status(StatusCode.OK))


def attach_tool_events(span: Span, tool_trace: list[dict[str, Any]]) -> None:
    """Replay a completed tool_trace onto a span as gen_ai.tool.call events."""
    for step in tool_trace:
        tool_event(
            span,
            tool_name=str(step.get("tool_name", "")),
            risk_tier=str(step.get("risk_tier", "read_only")),
            requires_approval=bool(step.get("requires_approval", False)),
            cost_usd=float(step.get("cost_usd", 0.0)),
        )
