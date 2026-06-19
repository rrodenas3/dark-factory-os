from __future__ import annotations

import json
from typing import Any, cast
from uuid import UUID, uuid4

import asyncpg

from .models import ActorType, AuditEventRecord


class AuditRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def record(
        self,
        *,
        actor_type: ActorType,
        event_type: str,
        actor_id: UUID | None = None,
        object_type: str | None = None,
        object_id: UUID | None = None,
        payload_json: dict[str, Any] | None = None,
    ) -> AuditEventRecord:
        event_id = uuid4()
        row = await self._pool.fetchrow(
            """
            INSERT INTO audit_events (
                id, actor_type, actor_id, event_type, object_type, object_id, payload_json
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb)
            RETURNING id, actor_type, actor_id, event_type, object_type, object_id, payload_json, created_at
            """,
            event_id,
            actor_type,
            actor_id,
            event_type,
            object_type,
            object_id,
            json.dumps(payload_json or {}),
        )
        return _row_to_audit_event(row)

    async def list_events(
        self,
        *,
        run_id: UUID | None = None,
        event_type: str | None = None,
        limit: int = 100,
    ) -> list[AuditEventRecord]:
        rows = await self._pool.fetch(
            """
            SELECT id, actor_type, actor_id, event_type, object_type, object_id, payload_json, created_at
            FROM audit_events
            WHERE (
                $1::uuid IS NULL
                OR object_id = $1
                OR payload_json->>'run_id' = $1::text
            )
              AND ($2::text IS NULL OR event_type = $2)
            ORDER BY created_at DESC
            LIMIT $3
            """,
            run_id,
            event_type,
            limit,
        )
        return [_row_to_audit_event(row) for row in rows]


def _row_to_audit_event(row: asyncpg.Record) -> AuditEventRecord:
    payload = row["payload_json"]
    if isinstance(payload, str):
        payload = json.loads(payload)
    return AuditEventRecord(
        id=row["id"],
        actor_type=cast(ActorType, row["actor_type"]),
        actor_id=row["actor_id"],
        event_type=row["event_type"],
        object_type=row["object_type"],
        object_id=row["object_id"],
        payload_json=cast(dict[str, Any], payload or {}),
        created_at=row["created_at"],
    )
