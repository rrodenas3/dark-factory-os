"""Tests for OTEL telemetry integration in the orchestration graph.

Uses an in-memory OTEL SDK (no collector needed) to assert spans are emitted
with correct gen_ai.* attribute names and tool call events.

The TracerProvider is set once for the entire module (OTEL only allows one
set_tracer_provider call per process) and cleared between tests via exporter.clear().
"""
from __future__ import annotations

import pytest
from dark_factory_orchestration import build_graph
from dark_factory_orchestration.telemetry import (
    GEN_AI_OPERATION_NAME,
    GEN_AI_SKILL_NAME,
    GEN_AI_STATUS,
    GEN_AI_SYSTEM,
    GEN_AI_VERTICAL,
)
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

_exporter = InMemorySpanExporter()
_provider = TracerProvider()
_provider.add_span_processor(SimpleSpanProcessor(_exporter))
trace.set_tracer_provider(_provider)


@pytest.fixture(autouse=True)
def clear_spans() -> None:
    _exporter.clear()


def _invoke(vertical: str, skill: str, run_id: str = "test-x") -> None:
    build_graph().invoke({"run_id": run_id, "vertical": vertical, "skill_name": skill})


def test_run_emits_root_span() -> None:
    _invoke("finance", "spend-anomaly-detection", "t01")
    names = [s.name for s in _exporter.get_finished_spans()]
    assert "dfos.run" in names


def test_run_emits_node_spans() -> None:
    _invoke("finance", "spend-anomaly-detection", "t02")
    names = [s.name for s in _exporter.get_finished_spans()]
    assert "dfos.node.planner" in names
    assert "dfos.node.specialist" in names
    assert "dfos.node.verifier" in names


def test_root_span_has_gen_ai_attributes() -> None:
    _invoke("saas", "incident-triage", "t03")
    root = next(s for s in _exporter.get_finished_spans() if s.name == "dfos.run")
    attrs = root.attributes or {}
    assert attrs.get(GEN_AI_SYSTEM) == "dark_factory_os"
    assert attrs.get(GEN_AI_OPERATION_NAME) == "plan_act_verify"
    assert attrs.get(GEN_AI_VERTICAL) == "saas"
    assert attrs.get(GEN_AI_SKILL_NAME) == "incident-triage"


def test_root_span_records_outcome_status() -> None:
    _invoke("finance", "spend-anomaly-detection", "t04")
    root = next(s for s in _exporter.get_finished_spans() if s.name == "dfos.run")
    attrs = root.attributes or {}
    assert GEN_AI_STATUS in attrs


def test_approval_required_run_emits_approval_gate_span() -> None:
    _invoke("retail", "promo-rebalance", "t05")
    names = [s.name for s in _exporter.get_finished_spans()]
    assert "dfos.node.approval_gate" in names


def test_tool_call_events_are_attached_to_root_span() -> None:
    _invoke("finance", "spend-anomaly-detection", "t06")
    root = next(s for s in _exporter.get_finished_spans() if s.name == "dfos.run")
    event_names = [e.name for e in root.events]
    assert "gen_ai.tool.call" in event_names
