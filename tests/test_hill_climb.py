import json
import subprocess
from pathlib import Path

from dark_factory_evals.hill_climb import (
    HillClimbConfig,
    load_trace_corpus,
    proposals_to_json,
    propose_skill_improvements,
)

ROOT = Path(__file__).resolve().parents[1]
TRACE_CORPUS = ROOT / "evals" / "trace_corpus" / "skill_improvement_traces.jsonl"


def test_repeated_approval_required_produces_ready_proposal() -> None:
    traces = load_trace_corpus(TRACE_CORPUS)
    proposals = propose_skill_improvements(traces, config=HillClimbConfig(min_repeated_events=2))

    retail = next(proposal for proposal in proposals if proposal.skill_name == "promo-rebalance")
    assert retail.status == "ready_for_review"
    assert "approval_required" in retail.trigger
    assert any("pricing.set_price_band" in line for line in retail.diff_summary)
    assert retail.eval_report_attachment is not None
    assert retail.eval_report_attachment["task_success_rate"] >= 0.8


def test_failing_eval_replay_marks_proposal_rejected() -> None:
    traces = load_trace_corpus(TRACE_CORPUS)
    proposals = propose_skill_improvements(traces, config=HillClimbConfig(min_repeated_events=2))

    saas = next(proposal for proposal in proposals if proposal.skill_name == "incident-triage")
    assert saas.status == "rejected"
    assert "failed runs" in saas.trigger
    assert saas.eval_report_attachment is not None
    assert saas.eval_report_attachment["grounding_score"] < 0.8


def test_proposals_json_has_expected_artifact_shape() -> None:
    traces = load_trace_corpus(TRACE_CORPUS)
    payload = json.loads(proposals_to_json(propose_skill_improvements(traces)))

    assert "proposals" in payload
    assert len(payload["proposals"]) == 2
    for proposal in payload["proposals"]:
        assert {"id", "skill_name", "evidence", "diff_summary", "eval_plan", "status", "created_at"} <= set(proposal)


def test_cli_produces_proposal_json_from_fixture_corpus() -> None:
    completed = subprocess.run(
        ["uv", "run", "dfos-propose-skill", str(TRACE_CORPUS)],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)
    statuses = {proposal["skill_name"]: proposal["status"] for proposal in payload["proposals"]}
    assert statuses["promo-rebalance"] == "ready_for_review"
    assert statuses["incident-triage"] == "rejected"
