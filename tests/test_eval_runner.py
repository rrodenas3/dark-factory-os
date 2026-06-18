from pathlib import Path

from dark_factory_evals.runner import EvalRunner
from dark_factory_governance.risk_registry import load_risk_registry
from dark_factory_orchestration.graph import build_graph

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "packages" / "py" / "governance" / "risk_registry.yaml"
DATASETS = ROOT / "evals" / "datasets"


def _make_runner() -> EvalRunner:
    registry = load_risk_registry(REGISTRY_PATH)
    graph = build_graph(registry)
    return EvalRunner(graph=graph)


def test_finance_eval_runs_all_cases() -> None:
    runner = _make_runner()
    report = runner.run_dataset(DATASETS / "finance_goldens.jsonl", "finance")
    assert report.vertical == "finance"
    assert len(report.results) == 10


def test_retail_eval_runs_all_cases() -> None:
    runner = _make_runner()
    report = runner.run_dataset(DATASETS / "retail_goldens.jsonl", "retail")
    assert len(report.results) == 5


def test_saas_eval_runs_all_cases() -> None:
    runner = _make_runner()
    report = runner.run_dataset(DATASETS / "saas_goldens.jsonl", "saas")
    assert len(report.results) == 5


def test_finance_task_success_rate_above_threshold() -> None:
    runner = _make_runner()
    report = runner.run_dataset(DATASETS / "finance_goldens.jsonl", "finance")
    assert report.task_success_rate >= 0.5, f"Success rate too low: {report.task_success_rate}"


def test_finance_grounding_score_above_threshold() -> None:
    runner = _make_runner()
    report = runner.run_dataset(DATASETS / "finance_goldens.jsonl", "finance")
    assert report.grounding_score >= 0.5, f"Grounding too low: {report.grounding_score}"


def test_clear_summary_has_all_dimensions() -> None:
    runner = _make_runner()
    report = runner.run_dataset(DATASETS / "finance_goldens.jsonl", "finance")
    summary = report.summary()
    for key in ("task_success_rate", "grounding_score", "approval_precision", "trajectory_f1", "avg_cost_usd", "p95_latency_ms"):  # noqa: E501
        assert key in summary, f"Missing CLEAR dimension: {key}"
