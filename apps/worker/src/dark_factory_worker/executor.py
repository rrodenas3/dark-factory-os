from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any, cast
from uuid import UUID

from dark_factory_governance.risk_registry import load_risk_registry
from dark_factory_memory import PostgresMemoryStore, build_run_outcome_memory
from dark_factory_orchestration import RunGraph, RunState, build_graph
from dark_factory_persistence import ApprovalRepository, RunRepository
from dark_factory_persistence.pool import close_pool, get_pool
from dark_factory_persistence.run_ops import persist_run_result, state_from_run


class RunExecutor:
    """Polls pending runs and executes the governed orchestration graph."""

    def __init__(
        self,
        runs: RunRepository,
        approvals: ApprovalRepository,
        graph: RunGraph | None = None,
        *,
        worker_id: str | None = None,
        lease_seconds: int = 120,
    ) -> None:
        self._runs = runs
        self._approvals = approvals
        self._graph = graph or build_graph()
        self._worker_id = worker_id or os.environ.get("HOSTNAME", "worker")
        self._lease_seconds = lease_seconds

    async def process_pending(self) -> bool:
        await self._runs.release_stale_running()
        run = await self._runs.claim_next_pending(worker_id=self._worker_id, lease_seconds=self._lease_seconds)
        if run is None:
            return False
        await self._execute_run(run)
        return True

    async def execute_run_by_id(self, run_id: UUID) -> None:
        run = await self._runs.claim_run_by_id(
            run_id,
            worker_id=self._worker_id,
            lease_seconds=self._lease_seconds,
        )
        if run is None:
            existing = await self._runs.get_run(run_id)
            if existing is None:
                msg = f"Run {run_id} not found"
                raise ValueError(msg)
            msg = f"Run {run_id} is not pending (status={existing.status})"
            raise ValueError(msg)
        await self._execute_run(run)

    async def resume_run(self, run_id: UUID, decision: str, reason: str) -> RunState:
        run = await self._runs.get_run(run_id)
        if run is None or run.checkpoint_json is None:
            msg = f"Run {run_id} has no checkpoint to resume"
            raise ValueError(msg)

        pending = await self._approvals.list_pending_for_run(run_id)
        for approval in pending:
            await self._approvals.decide(
                approval.id,
                decision=cast(Any, "approved" if decision == "approved" else "rejected"),
                reason=reason,
            )

        state = cast(RunState, state_from_run(run))
        final = await asyncio.to_thread(self._graph.resume, state, decision)
        await persist_run_result(self._runs, self._approvals, run, dict(final))
        await self._write_run_outcome_memory(dict(final))
        return final

    async def _execute_run(self, run: Any) -> None:
        try:
            await self._runs.renew_lease(run.id, worker_id=self._worker_id, lease_seconds=self._lease_seconds)
            state = cast(RunState, state_from_run(run, initial=True))
            final = await asyncio.to_thread(self._graph.invoke, state)
            await persist_run_result(self._runs, self._approvals, run, dict(final))
            await self._write_run_outcome_memory(dict(final))
        except Exception:
            await self._runs.update_run_status(run.id, status="failed")
            raise

    async def _write_run_outcome_memory(self, state: dict[str, Any]) -> None:
        item = build_run_outcome_memory(state)
        if item is None:
            return
        store = PostgresMemoryStore(self._runs.pool)
        try:
            await store.upsert(item)
        except ValueError as exc:
            if "append-only" not in str(exc):
                raise


async def worker_loop(poll_seconds: float = 2.0) -> None:
    pool = await get_pool()
    runs = RunRepository(pool)
    approvals = ApprovalRepository(pool)
    registry_path = Path(__file__).resolve().parents[4] / "packages" / "py" / "governance" / "risk_registry.yaml"
    graph = build_graph(load_risk_registry(registry_path)) if registry_path.exists() else build_graph()
    executor = RunExecutor(runs, approvals, graph)

    try:
        while True:
            processed = await executor.process_pending()
            if not processed:
                await asyncio.sleep(poll_seconds)
    finally:
        await close_pool()
