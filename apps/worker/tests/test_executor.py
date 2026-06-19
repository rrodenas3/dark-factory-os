from __future__ import annotations

import os
from pathlib import Path

import asyncpg
import pytest
from dark_factory_memory import PostgresMemoryStore
from dark_factory_orchestration import build_graph
from dark_factory_persistence import ApprovalRepository, RunRepository
from dark_factory_persistence.migrate import run_migrations
from dark_factory_worker.executor import RunExecutor

ROOT = Path(__file__).resolve().parents[3]
MIGRATIONS_DIR = ROOT / "infra" / "migrations"


def _database_url() -> str | None:
    return os.environ.get("DATABASE_URL")


@pytest.fixture
async def pool() -> asyncpg.Pool:
    url = _database_url()
    if not url:
        pytest.skip("DATABASE_URL not set — skipping worker integration tests")
    pool = await asyncpg.create_pool(url, min_size=1, max_size=2)
    assert pool is not None
    await run_migrations(pool, directory=MIGRATIONS_DIR)
    yield pool
    await pool.close()


@pytest.fixture
def executor(pool: asyncpg.Pool) -> RunExecutor:
    return RunExecutor(RunRepository(pool), ApprovalRepository(pool), build_graph(), worker_id="test-worker")


@pytest.mark.asyncio
async def test_executor_completes_read_only_run(executor: RunExecutor, pool: asyncpg.Pool) -> None:
    runs = RunRepository(pool)
    await pool.execute("DELETE FROM memory_items WHERE namespace = 'finance.run_outcomes'")
    created = await runs.create_run(
        workflow_key="spend-anomaly-detection",
        vertical="finance",
        briefing_json={"objective": "Detect abnormal vendor spend."},
    )
    await executor.execute_run_by_id(created.id)

    finished = await runs.get_run(created.id)
    assert finished is not None
    assert finished.status == "completed"
    assert finished.step_count == 2
    assert finished.checkpoint_json is not None
    assert finished.checkpoint_json.get("tool_trace")

    memories = await PostgresMemoryStore(pool).all(namespace="finance.run_outcomes")
    assert any(item.content["run_id"] == str(created.id) for item in memories)


@pytest.mark.asyncio
async def test_executor_pauses_for_approval_and_resumes(executor: RunExecutor, pool: asyncpg.Pool) -> None:
    runs = RunRepository(pool)
    approvals = ApprovalRepository(pool)
    await pool.execute("DELETE FROM memory_items WHERE namespace = 'retail.run_outcomes'")
    created = await runs.create_run(
        workflow_key="promo-rebalance",
        vertical="retail",
        briefing_json={"objective": "Recover promo margin safely."},
    )
    await executor.execute_run_by_id(created.id)

    paused = await runs.get_run(created.id)
    assert paused is not None
    assert paused.status == "approval_required"
    pending = await approvals.list_pending_for_run(created.id)
    assert pending

    final = await executor.resume_run(created.id, "approved", "Policy citation verified.")
    assert final["status"] == "completed"

    completed = await runs.get_run(created.id)
    assert completed is not None
    assert completed.status == "completed"
    assert completed.checkpoint_json is not None
    executed = [
        step
        for step in completed.checkpoint_json.get("tool_trace", [])
        if step.get("tool_name") == "pricing.set_price_band" and step.get("executed") is True
    ]
    assert len(executed) == 1

    memories = await PostgresMemoryStore(pool).all(namespace="retail.run_outcomes")
    statuses = {item.content["status"] for item in memories if item.content["run_id"] == str(created.id)}
    assert {"approval_required", "completed"} <= statuses


@pytest.mark.asyncio
async def test_claim_next_pending_skips_non_pending(pool: asyncpg.Pool) -> None:
    runs = RunRepository(pool)
    run = await runs.create_run(workflow_key="incident-triage", vertical="saas")
    claimed = await runs.claim_next_pending(worker_id="worker-a", lease_seconds=120)
    assert claimed is not None
    assert claimed.id == run.id
    assert claimed.status == "running"

    second = await runs.claim_next_pending(worker_id="worker-b", lease_seconds=120)
    assert second is None


@pytest.mark.asyncio
async def test_release_stale_running_requeues_run(pool: asyncpg.Pool) -> None:
    runs = RunRepository(pool)
    run = await runs.create_run(workflow_key="incident-triage", vertical="saas")
    claimed = await runs.claim_next_pending(worker_id="worker-a", lease_seconds=1)
    assert claimed is not None

    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE runs SET lease_expires_at = NOW() - INTERVAL '1 minute' WHERE id = $1",
            run.id,
        )

    released = await runs.release_stale_running()
    assert released == 1

    refreshed = await runs.get_run(run.id)
    assert refreshed is not None
    assert refreshed.status == "pending"
