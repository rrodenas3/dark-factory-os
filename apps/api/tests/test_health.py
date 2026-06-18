from dark_factory_api.main import RUN_STATES, RUNS, app
from fastapi.testclient import TestClient


def setup_function() -> None:
    RUNS.clear()
    RUN_STATES.clear()


def test_health() -> None:
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_run_executes_deterministic_harness() -> None:
    response = TestClient(app).post(
        "/api/runs",
        json={
            "vertical": "finance",
            "skill_name": "spend-anomaly-detection",
            "briefing_json": {"objective": "Detect abnormal vendor spend."},
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "completed"
    assert body["step_count"] == 2
    assert body["total_cost_usd"] > 0


def test_create_run_can_pause_for_approval_and_expose_trace() -> None:
    client = TestClient(app)
    created = client.post(
        "/api/runs",
        json={
            "vertical": "retail",
            "skill_name": "promo-rebalance",
            "briefing_json": {"objective": "Recover promo margin safely."},
        },
    )

    assert created.status_code == 201
    run = created.json()
    assert run["status"] == "approval_required"

    detail = client.get(f"/api/runs/{run['id']}").json()
    assert detail["pending_approval"] is True
    assert detail["approval_role"] == "commercial-manager"
    assert "POL-AP-20 §2.0" in detail["policy_citations"]

    trace = client.get(f"/api/runs/{run['id']}/trace").json()
    assert trace["status"] == "approval_required"
    assert trace["tool_trace"][-1]["tool_name"] == "pricing.set_price_band"
    assert trace["tool_trace"][-1]["requires_approval"] is True


def test_resume_run_records_approval_decision() -> None:
    client = TestClient(app)
    created = client.post(
        "/api/runs",
        json={
            "vertical": "retail",
            "skill_name": "promo-rebalance",
            "briefing_json": {"objective": "Recover promo margin safely."},
        },
    ).json()

    response = client.post(
        f"/api/runs/{created['id']}/resume",
        json={"decision": "approved", "reason": "Evidence and policy citation checked."},
    )

    assert response.status_code == 202
    assert response.json()["run_status"] == "completed"
    detail = client.get(f"/api/runs/{created['id']}").json()
    assert detail["pending_approval"] is False
    assert detail["outcome"]["approval_decision"] == "approved"
