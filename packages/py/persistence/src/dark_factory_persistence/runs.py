from __future__ import annotations

import json
from typing import Any, cast
from uuid import UUID, uuid4

import asyncpg

from .models import RunRecord, RunStatus, RunStepRecord, RunVertical, StepType


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
            RETURNING id, workflow_key, status, vertical, briefing_json, total_cost_usd,
                      step_count, agent_id, user_id, started_at, ended_at, created_at
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
            SELECT id, workflow_key, status, vertical, briefing_json, total_cost_usd,
                   step_count, agent_id, user_id, started_at, ended_at, created_at
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
            RETURNING id, workflow_key, status, vertical, briefing_json, total_cost_usd,
                      step_count, agent_id, user_id, started_at, ended_at, created_at
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
            SELECT id, workflow_key, status, vertical, briefing_json, total_cost_usd,
                   step_count, agent_id, user_id, started_at, ended_at, created_at
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
        tool_risk_class: str | None = None,
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
                id, run_id, step_type, tool_name, tool_risk_class, status,
                input_json, output_json, latency_ms, cost_usd, span_json
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8::jsonb, $9, $10, $11::jsonb)
            RETURNING id, run_id, step_type, tool_name, tool_risk_class, status,
                      input_json, output_json, latency_ms, cost_usd, span_json, created_at
            """,
            step_id,
            run_id,
            step_type,
            tool_name,
            tool_risk_class,
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
            SELECT id, run_id, step_type, tool_name, tool_risk_class, status,
                   input_json, output_json, latency_ms, cost_usd, span_json, created_at
            FROM run_steps
            WHERE run_id = $1
            ORDER BY created_at ASC
            """,
            run_id,
        )
        return [_row_to_step(row) for row in rows]


def _row_to_run(row: asyncpg.Record) -> RunRecord:
    briefing = row["briefing_json"]
    if isinstance(briefing, str):
        briefing = json.loads(briefing)
    return RunRecord(
        id=row["id"],
        workflow_key=row["workflow_key"],
        status=row["status"],
        vertical=row["vertical"],
        briefing_json=briefing or {},
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
        tool_risk_class=row["tool_risk_class"],
        status=row["status"],
        input_json=_json(row["input_json"]),
        output_json=_json(row["output_json"]),
        latency_ms=row["latency_ms"],
        cost_usd=float(row["cost_usd"] or 0),
        span_json=_json(row["span_json"]),
        created_at=row["created_at"],
    )
