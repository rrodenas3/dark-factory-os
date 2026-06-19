from __future__ import annotations

import json
from typing import Any, cast
from uuid import UUID, uuid4

import asyncpg

from .models import RunRecord, RunStatus, RunStepRecord, RunVertical, StepType

_RUN_SELECT = """
    SELECT id, workflow_key, status, vertical, briefing_json, checkpoint_json,
           total_cost_usd, step_count, agent_id, user_id, started_at, ended_at, created_at
"""

_RUN_RETURNING = """
    RETURNING id, workflow_key, status, vertical, briefing_json, checkpoint_json,
              total_cost_usd, step_count, agent_id, user_id, started_at, ended_at, created_at
"""


class RunRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def create_run(
        self,
        *,
        workflow_key: str,
        vertical: RunVertical,
        briefing_json: dict[str, Any] | None = None,
        agent_id: UUID | None = None,
        user_id: UUID | None = None,
        status: RunStatus = "pending",
    ) -> RunRecord:
        run_id = uuid4()
        briefing = json.dumps(briefing_json or {})
        row = await self._pool.fetchrow(
            """
            INSERT INTO runs (id, workflow_key, status, vertical, briefing_json, agent_id, user_id)
            VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7)
            RETURNING id, workflow_key, status, vertical, briefing_json, checkpoint_json,
                      total_cost_usd, step_count, agent_id, user_id, started_at, ended_at, created_at
            """,
            run_id,
            workflow_key,
            status,
            vertical,
            briefing,
            agent_id,
            user_id,
        )
        return _row_to_run(row)

    async def get_run(self, run_id: UUID) -> RunRecord | None:
        row = await self._pool.fetchrow(
            """
            SELECT id, workflow_key, status, vertical, briefing_json, checkpoint_json,
                   total_cost_usd, step_count, agent_id, user_id, started_at, ended_at, created_at
            FROM runs WHERE id = $1
            """,
            run_id,
        )
        return _row_to_run(row) if row else None

    async def update_run_status(
        self,
        run_id: UUID,
        *,
        status: RunStatus,
        total_cost_usd: float | None = None,
        step_count: int | None = None,
    ) -> RunRecord | None:
        row = await self._pool.fetchrow(
            """
            UPDATE runs
            SET status = $2,
                total_cost_usd = COALESCE($3, total_cost_usd),
                step_count = COALESCE($4, step_count),
                started_at = CASE WHEN $2 = 'running' AND started_at IS NULL THEN NOW() ELSE started_at END,
                ended_at = CASE WHEN $2 IN ('completed', 'failed', 'cancelled') THEN NOW() ELSE ended_at END
            WHERE id = $1
            RETURNING id, workflow_key, status, vertical, briefing_json, checkpoint_json,
                      total_cost_usd, step_count, agent_id, user_id, started_at, ended_at, created_at
            """,
            run_id,
            status,
            total_cost_usd,
            step_count,
        )
        return _row_to_run(row) if row else None

    async def list_runs(self, *, limit: int = 50) -> list[RunRecord]:
        rows = await self._pool.fetch(
            """
            SELECT id, workflow_key, status, vertical, briefing_json, checkpoint_json,
                   total_cost_usd, step_count, agent_id, user_id, started_at, ended_at, created_at
            FROM runs
            ORDER BY created_at DESC
            LIMIT $1
            """,
            limit,
        )
        return [_row_to_run(row) for row in rows]

    async def append_step(
        self,
        *,
        run_id: UUID,
        step_type: StepType,
        status: str,
        tool_name: str | None = None,
        risk_tier: str | None = None,
        input_json: dict[str, Any] | None = None,
        output_json: dict[str, Any] | None = None,
        latency_ms: int | None = None,
        cost_usd: float = 0.0,
        span_json: dict[str, Any] | None = None,
    ) -> RunStepRecord:
        step_id = uuid4()
        row = await self._pool.fetchrow(
            """
            INSERT INTO run_steps (
                id, run_id, step_type, tool_name, risk_tier, status,
                input_json, output_json, latency_ms, cost_usd, span_json
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8::jsonb, $9, $10, $11::jsonb)
            RETURNING id, run_id, step_type, tool_name, risk_tier, status,
                      input_json, output_json, latency_ms, cost_usd, span_json, created_at
            """,
            step_id,
            run_id,
            step_type,
            tool_name,
            risk_tier,
            status,
            json.dumps(input_json) if input_json is not None else None,
            json.dumps(output_json) if output_json is not None else None,
            latency_ms,
            cost_usd,
            json.dumps(span_json) if span_json is not None else None,
        )
        return _row_to_step(row)

    async def list_steps(self, run_id: UUID) -> list[RunStepRecord]:
        rows = await self._pool.fetch(
            """
            SELECT id, run_id, step_type, tool_name, risk_tier, status,
                   input_json, output_json, latency_ms, cost_usd, span_json, created_at
            FROM run_steps
            WHERE run_id = $1
            ORDER BY created_at ASC
            """,
            run_id,
        )
        return [_row_to_step(row) for row in rows]

    async def release_stale_running(self) -> int:
        rows = await self._pool.fetch(
            """
            UPDATE runs
            SET status = 'pending',
                worker_id = NULL,
                lease_expires_at = NULL
            WHERE status = 'running'
              AND lease_expires_at IS NOT NULL
              AND lease_expires_at < NOW()
            RETURNING id
            """
        )
        return len(rows)

    async def claim_next_pending(self, *, worker_id: str, lease_seconds: int = 120) -> RunRecord | None:
        row = await self._pool.fetchrow(
            """
            UPDATE runs
            SET status = 'running',
                started_at = COALESCE(started_at, NOW()),
                worker_id = $1,
                lease_expires_at = NOW() + ($2 * INTERVAL '1 second')
            WHERE id = (
                SELECT id FROM runs
                WHERE status = 'pending'
                ORDER BY created_at ASC
                FOR UPDATE SKIP LOCKED
                LIMIT 1
            )
            RETURNING id, workflow_key, status, vertical, briefing_json, checkpoint_json,
                      total_cost_usd, step_count, agent_id, user_id, started_at, ended_at, created_at
            """,
            worker_id,
            lease_seconds,
        )
        return _row_to_run(row) if row else None

    async def claim_run_by_id(
        self,
        run_id: UUID,
        *,
        worker_id: str,
        lease_seconds: int = 120,
    ) -> RunRecord | None:
        row = await self._pool.fetchrow(
            """
            UPDATE runs
            SET status = 'running',
                started_at = COALESCE(started_at, NOW()),
                worker_id = $2,
                lease_expires_at = NOW() + ($3 * INTERVAL '1 second')
            WHERE id = $1 AND status = 'pending'
            RETURNING id, workflow_key, status, vertical, briefing_json, checkpoint_json,
                      total_cost_usd, step_count, agent_id, user_id, started_at, ended_at, created_at
            """,
            run_id,
            worker_id,
            lease_seconds,
        )
        return _row_to_run(row) if row else None

    async def renew_lease(self, run_id: UUID, *, worker_id: str, lease_seconds: int = 120) -> None:
        await self._pool.execute(
            """
            UPDATE runs
            SET lease_expires_at = NOW() + ($3 * INTERVAL '1 second')
            WHERE id = $1 AND worker_id = $2 AND status = 'running'
            """,
            run_id,
            worker_id,
            lease_seconds,
        )

    async def save_checkpoint(
        self,
        run_id: UUID,
        *,
        status: RunStatus,
        checkpoint: dict[str, Any],
        total_cost_usd: float,
        step_count: int,
        persisted_trace_len: int,
    ) -> RunRecord | None:
        payload = {**checkpoint, "persisted_trace_len": persisted_trace_len}
        row = await self._pool.fetchrow(
            """
            UPDATE runs
            SET status = $2,
                checkpoint_json = $3::jsonb,
                total_cost_usd = $4,
                step_count = $5,
                worker_id = NULL,
                lease_expires_at = NULL,
                ended_at = CASE WHEN $2 IN ('completed', 'failed', 'cancelled') THEN NOW() ELSE ended_at END
            WHERE id = $1
            RETURNING id, workflow_key, status, vertical, briefing_json, checkpoint_json,
                      total_cost_usd, step_count, agent_id, user_id, started_at, ended_at, created_at
            """,
            run_id,
            status,
            json.dumps(payload),
            total_cost_usd,
            step_count,
        )
        return _row_to_run(row) if row else None


def _row_to_run(row: asyncpg.Record) -> RunRecord:
    briefing = row["briefing_json"]
    if isinstance(briefing, str):
        briefing = json.loads(briefing)
    checkpoint = row["checkpoint_json"] if "checkpoint_json" in row.keys() else None
    if isinstance(checkpoint, str):
        checkpoint = json.loads(checkpoint)
    return RunRecord(
        id=row["id"],
        workflow_key=row["workflow_key"],
        status=row["status"],
        vertical=row["vertical"],
        briefing_json=briefing or {},
        checkpoint_json=checkpoint,
        total_cost_usd=float(row["total_cost_usd"] or 0),
        step_count=int(row["step_count"] or 0),
        agent_id=row["agent_id"],
        user_id=row["user_id"],
        started_at=row["started_at"],
        ended_at=row["ended_at"],
        created_at=row["created_at"],
    )


def _row_to_step(row: asyncpg.Record) -> RunStepRecord:
    def _json(value: Any) -> dict[str, Any] | None:
        if value is None:
            return None
        if isinstance(value, str):
            return cast(dict[str, Any], json.loads(value))
        return cast(dict[str, Any], dict(value))

    return RunStepRecord(
        id=row["id"],
        run_id=row["run_id"],
        step_type=row["step_type"],
        tool_name=row["tool_name"],
        risk_tier=row["risk_tier"],
        status=row["status"],
        input_json=_json(row["input_json"]),
        output_json=_json(row["output_json"]),
        latency_ms=row["latency_ms"],
        cost_usd=float(row["cost_usd"] or 0),
        span_json=_json(row["span_json"]),
        created_at=row["created_at"],
    )
