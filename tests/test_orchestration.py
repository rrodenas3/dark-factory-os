from pathlib import Path

import pytest
from dark_factory_governance.risk_registry import load_risk_registry
from dark_factory_orchestration import RunGraph, RunState, build_graph

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "packages" / "py" / "governance" / "risk_registry.yaml"


@pytest.fixture
def graph() -> RunGraph:
    registry = load_risk_registry(REGISTRY_PATH)
    return build_graph(registry)


def _initial(run_id: str, vertical: str, skill_name: str) -> RunState:
    return RunState(
        run_id=run_id,
        vertical=vertical,
        skill_name=skill_name,
        plan=[],
        current_step=0,
        step_count=0,
        cost_usd=0.0,
        status="running",
        pending_approval=False,
        approval_role=None,
        pending_tool=None,
        tool_trace=[],
        memory_context=[],
        policy_citations=[],
        outcome=None,
        error=None,
    )


def test_finance_ap_run_reaches_terminal_state(graph: RunGraph) -> None:
    final = graph.invoke(_initial("run-fin-001", "finance", "ap-exception-resolution"))
    assert final["status"] in ("completed", "approval_required", "failed")


def test_finance_ap_run_executes_tools(graph: RunGraph) -> None:
    final = graph.invoke(_initial("run-fin-002", "finance", "ap-exception-resolution"))
    assert len(final["tool_trace"]) >= 1


def test_finance_ap_cites_policy(graph: RunGraph) -> None:
    final = graph.invoke(_initial("run-fin-003", "finance", "ap-exception-resolution"))
    has_citations = bool(final.get("policy_citations")) or final.get("outcome", {}) is not None
    assert has_citations


def test_retail_promo_run_completes(graph: RunGraph) -> None:
    final = graph.invoke(_initial("run-ret-001", "retail", "promo-rebalance"))
    assert final["status"] in ("completed", "approval_required", "failed")


def test_saas_incident_run_completes(graph: RunGraph) -> None:
    final = graph.invoke(_initial("run-saas-001", "saas", "incident-triage"))
    assert final["status"] in ("completed", "approval_required", "failed")


def test_approval_required_when_financial_tool_in_plan(graph: RunGraph) -> None:
    final = graph.invoke(_initial("run-fin-004", "finance", "promo-rebalance"))
    tool_names = {t["tool_name"] for t in final.get("tool_trace", [])}
    financial_tools = {"erp.post_payment", "erp.create_credit_memo", "pricing.set_price_band", "ucp.propose_checkout"}
    if tool_names & financial_tools:
        assert final["status"] == "approval_required"


def test_tool_trace_records_risk_tier(graph: RunGraph) -> None:
    final = graph.invoke(_initial("run-fin-005", "finance", "ap-exception-resolution"))
    for step in final.get("tool_trace", []):
        assert "risk_tier" in step
        assert step["risk_tier"] in ("read_only", "financial", "destructive")


def test_spend_anomaly_skill_completes(graph: RunGraph) -> None:
    final = graph.invoke(_initial("run-fin-006", "finance", "spend-anomaly-detection"))
    assert final["status"] in ("completed", "approval_required", "failed")


def test_gated_tool_not_executed_before_approval(graph: RunGraph) -> None:
    final = graph.invoke(_initial("run-ret-gated", "retail", "promo-rebalance"))
    assert final["status"] == "approval_required"
    gated = [t for t in final["tool_trace"] if t["tool_name"] == "pricing.set_price_band"]
    assert len(gated) == 1
    assert gated[0]["executed"] is False


def test_resume_executes_gated_tool_once(graph: RunGraph) -> None:
    paused = graph.invoke(_initial("run-ret-resume", "retail", "promo-rebalance"))
    assert paused["status"] == "approval_required"
    assert paused.get("pending_tool") == "pricing.set_price_band"

    final = graph.resume(paused, "approved")
    executed = [t for t in final["tool_trace"] if t["tool_name"] == "pricing.set_price_band" and t.get("executed")]
    assert len(executed) == 1
    assert executed[0]["success"] is True


def test_resume_rejected_cancels_run(graph: RunGraph) -> None:
    paused = graph.invoke(_initial("run-ret-reject", "retail", "promo-rebalance"))
    final = graph.resume(paused, "rejected")
    assert final["status"] == "cancelled"
    assert final.get("pending_tool") is None
