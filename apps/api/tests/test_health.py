from dark_factory_api import persisted
from dark_factory_api.main import DEMO_APPROVALS, RUN_STATES, RUNS, app
from dark_factory_memory import MemoryQuery
from fastapi.testclient import TestClient
from pytest import MonkeyPatch


def setup_function() -> None:
    RUNS.clear()
    RUN_STATES.clear()


def test_health() -> None:
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_agent_card_served_from_well_known_route() -> None:
    response = TestClient(app).get("/.well-known/agent-card.json")
    assert response.status_code == 200
    card = response.json()
    assert card["schemaVersion"] == "1.0"
    assert card["name"] == "dark-factory-os"
    assert {"json-rpc", "http"} == set(card["protocolBindings"])


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
    assert trace["tool_trace"][-1]["executed"] is False


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
    executed = [
        step
        for step in detail["tool_trace"]
        if step["tool_name"] == "pricing.set_price_band" and step.get("executed") is True
    ]
    assert len(executed) == 1


def test_memory_search_returns_live_results() -> None:
    response = TestClient(app).post(
        "/api/memory/search",
        json={"query": "invoice mismatch vendor", "namespace": "finance"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["matches"]
    first = body["matches"][0]
    assert "entity_key" in first
    assert "score" in first
    assert first["score"] > 0


def test_memory_demo_returns_seeded_items() -> None:
    response = TestClient(app).get("/api/memory/demo")
    assert response.status_code == 200
    items = response.json()
    namespaces = {item["namespace"] for item in items}
    assert "finance.vendor_risk" in namespaces


def test_memory_search_uses_persisted_backend_when_enabled(monkeypatch: MonkeyPatch) -> None:
    async def fake_search(query: MemoryQuery) -> list[dict[str, object]]:
        return [
            {
                "entity_key": "postgres-memory",
                "memory_type": "semantic",
                "score": 0.91,
                "source_trust": 0.9,
                "content": {"summary": f"served from {query.namespace}"},
            }
        ]

    monkeypatch.setattr(persisted, "persist_runs_enabled", lambda: True)
    monkeypatch.setattr(persisted, "search_memory_persisted", fake_search)

    response = TestClient(app).post(
        "/api/memory/search",
        json={"query": "vendor risk", "namespace": "finance"},
    )

    assert response.status_code == 200
    assert response.json()["matches"][0]["entity_key"] == "postgres-memory"


def test_memory_demo_uses_persisted_backend_when_enabled(monkeypatch: MonkeyPatch) -> None:
    async def fake_demo() -> list[dict[str, object]]:
        return [
            {
                "namespace": "postgres.seed",
                "entity_key": "persisted",
                "memory_type": "semantic",
                "trust": 0.9,
                "decay_score": 1.0,
                "summary": "served from postgres",
            }
        ]

    monkeypatch.setattr(persisted, "persist_runs_enabled", lambda: True)
    monkeypatch.setattr(persisted, "memory_demo_persisted", fake_demo)

    response = TestClient(app).get("/api/memory/demo")

    assert response.status_code == 200
    assert response.json()[0]["namespace"] == "postgres.seed"


def test_knowledge_graph_demo_returns_entities_and_edges() -> None:
    response = TestClient(app).get("/api/knowledge/graph")
    assert response.status_code == 200
    graph = response.json()
    assert graph["generated_from"] == "seeded_memory"
    assert {node["id"] for node in graph["nodes"]} >= {"contoso-logistics", "sparkling-water-12pk", "billing-api"}
    assert any(edge["relation"] == "constrained_by" for edge in graph["edges"])


def test_ucp_checkout_proposal_creates_pending_approval() -> None:
    before = len(DEMO_APPROVALS)
    response = TestClient(app).post(
        "/api/ucp/checkout-proposals",
        json={
            "sku": "SKU-SW12",
            "quantity": 12,
            "unit_price_usd": 16.5,
            "user_mandate": "Approve promo checkout only after manager review.",
        },
    )

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "pending"
    assert body["proposal"]["protocol"] == "ucp-simulator"
    assert body["proposal"]["checkout_state"] == "approval_required"
    assert body["proposal"]["approval"]["risk_tier"] == "financial"
    assert len(DEMO_APPROVALS) == before + 1
    assert DEMO_APPROVALS[-1]["action_type"] == "ucp.propose_checkout"
    assert DEMO_APPROVALS[-1]["run_id"] == body["run_id"]
