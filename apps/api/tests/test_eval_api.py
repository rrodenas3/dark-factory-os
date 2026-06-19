from dark_factory_api.evals import _RUN_LOCK
from dark_factory_api.main import app
from fastapi.testclient import TestClient


def test_eval_summary_exposes_clear_dimensions() -> None:
    response = TestClient(app).get("/api/evals/demo")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["source"] == "eval_runner"
    assert body["totals"]["cases"] == 20

    finance = next(metric for metric in body["metrics"] if metric["vertical"] == "finance")
    assert finance["cases"] == 10
    for key in (
        "task_success_rate",
        "grounding_score",
        "approval_precision",
        "trajectory_f1",
        "avg_cost_usd",
        "p95_latency_ms",
        "efficiency_score",
        "reliability_score",
    ):
        assert key in finance


def test_eval_run_recomputes_live_summary() -> None:
    response = TestClient(app).post("/api/evals/run")

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "completed"
    assert {metric["vertical"] for metric in body["metrics"]} == {"finance", "retail", "saas"}


def test_concurrent_eval_run_returns_409() -> None:
    assert _RUN_LOCK.acquire(blocking=False)
    try:
        response = TestClient(app).post("/api/evals/run")
    finally:
        _RUN_LOCK.release()

    assert response.status_code == 409
    assert response.json()["detail"] == "Eval run already in progress"


def test_skill_improvement_endpoint_exposes_proposals() -> None:
    response = TestClient(app).get("/api/evals/skill-improvements")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["trace_count"] == 4
    assert body["proposal_count"] == 2

    proposals = {proposal["skill_name"]: proposal for proposal in body["proposals"]}
    assert proposals["promo-rebalance"]["status"] == "ready_for_review"
    assert proposals["incident-triage"]["status"] == "rejected"
