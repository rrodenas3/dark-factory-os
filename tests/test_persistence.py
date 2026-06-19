from __future__ import annotations

import os
from pathlib import Path
from uuid import UUID

import asyncpg
import pytest
from dark_factory_persistence import AuditRepository, CostRepository, RunRepository
from dark_factory_persistence.migrate import run_migrations

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS_DIR = ROOT / "infra" / "migrations"


def _database_url() -> str | None:
    return os.environ.get("DATABASE_URL")


@pytest.fixture(scope="module")
async def pool() -> asyncpg.Pool:
    url = _database_url()
    if not url:
        pytest.skip("DATABASE_URL not set — skipping Postgres integration tests")
    pool = await asyncpg.create_pool(url, min_size=1, max_size=2)
    assert pool is not None
    await run_migrations(pool, directory=MIGRATIONS_DIR)
    yield pool
    await pool.close()


@pytest.fixture
def repo(pool: asyncpg.Pool) -> RunRepository:
    return RunRepository(pool)


@pytest.mark.asyncio
async def test_create_and_fetch_run(repo: RunRepository) -> None:
    created = await repo.create_run(
        workflow_key="ap-exception-resolution",
        vertical="finance",
        briefing_json={"invoice_id": "INV-2042"},
    )
    assert created.status == "pending"
    assert created.vertical == "finance"

    fetched = await repo.get_run(created.id)
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.briefing_json["invoice_id"] == "INV-2042"


@pytest.mark.asyncio
async def test_append_and_list_steps(repo: RunRepository) -> None:
    run = await repo.create_run(workflow_key="promo-rebalance", vertical="retail")
    step = await repo.append_step(
        run_id=run.id,
        step_type="act",
        status="ok",
        tool_name="policy.search",
        risk_tier="read_only",
        output_json={"matches": []},
        latency_ms=42,
        cost_usd=0.001,
    )
    assert step.run_id == run.id
    assert step.risk_tier == "read_only"

    steps = await repo.list_steps(run.id)
    assert len(steps) == 1
    assert steps[0].tool_name == "policy.search"


@pytest.mark.asyncio
async def test_update_run_status(repo: RunRepository) -> None:
    run = await repo.create_run(workflow_key="incident-triage", vertical="saas")
    updated = await repo.update_run_status(run.id, status="running")
    assert updated is not None
    assert updated.status == "running"
    assert updated.started_at is not None

    completed = await repo.update_run_status(
        run.id,
        status="completed",
        total_cost_usd=0.21,
        step_count=6,
    )
    assert completed is not None
    assert completed.status == "completed"
    assert completed.total_cost_usd == 0.21
    assert completed.ended_at is not None


@pytest.mark.asyncio
async def test_list_runs_returns_recent(repo: RunRepository) -> None:
    runs = await repo.list_runs(limit=10)
    assert isinstance(runs, list)
    for run in runs:
        assert isinstance(run.id, UUID)


@pytest.mark.asyncio
async def test_save_checkpoint_persists_trace(repo: RunRepository) -> None:
    run = await repo.create_run(workflow_key="promo-rebalance", vertical="retail")
    updated = await repo.save_checkpoint(
        run.id,
        status="approval_required",
        checkpoint={"tool_trace": [{"tool_name": "pricing.set_price_band", "executed": False}]},
        total_cost_usd=0.12,
        step_count=3,
        persisted_trace_len=1,
    )
    assert updated is not None
    assert updated.status == "approval_required"
    assert updated.checkpoint_json is not None
    assert updated.checkpoint_json["persisted_trace_len"] == 1
    assert updated.checkpoint_json["tool_trace"][0]["tool_name"] == "pricing.set_price_band"


@pytest.mark.asyncio
async def test_audit_repository_records_and_filters_events(pool: asyncpg.Pool) -> None:
    runs = RunRepository(pool)
    audit = AuditRepository(pool)
    run = await runs.create_run(workflow_key="promo-rebalance", vertical="retail")

    created = await audit.record(
        actor_type="user",
        event_type="run.created",
        object_type="run",
        object_id=run.id,
        payload_json={"workflow_key": run.workflow_key},
    )

    assert created.event_type == "run.created"
    events = await audit.list_events(run_id=run.id, event_type="run.created")
    assert any(event.id == created.id for event in events)
    assert events[0].payload_json["workflow_key"] == "promo-rebalance"


@pytest.mark.asyncio
async def test_cost_repository_summarizes_steps(pool: asyncpg.Pool) -> None:
    runs = RunRepository(pool)
    run = await runs.create_run(workflow_key="spend-anomaly-detection", vertical="finance")
    await runs.append_step(
        run_id=run.id,
        step_type="act",
        status="ok",
        tool_name="policy.search",
        risk_tier="read_only",
        cost_usd=0.002,
        latency_ms=25,
    )
    await runs.append_step(
        run_id=run.id,
        step_type="act",
        status="ok",
        tool_name="analytics.get_campaign_metrics",
        risk_tier="read_only",
        cost_usd=0.003,
        latency_ms=50,
    )

    summary = await CostRepository(pool).summary()

    assert summary["by_category"]["retrieval"] >= 0.002
    assert summary["by_category"]["tool_compute"] >= 0.003
    assert "finance" in summary["by_vertical"]
    assert summary["clear"]["latency"]["p95_seconds"] >= 0.025
