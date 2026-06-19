from __future__ import annotations

import json
from typing import Any, cast
from uuid import UUID, uuid4

import asyncpg

from .models import ApprovalRecord, ApprovalStatus


class ApprovalRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def create(
        self,
        *,
        run_id: UUID,
        action_type: str,
        action_payload: dict[str, Any],
        approver_role: str,
        arp_json: dict[str, Any] | None = None,
    ) -> ApprovalRecord:
        approval_id = uuid4()
        row = await self._pool.fetchrow(
            """
            INSERT INTO approvals (
                id, run_id, action_type, action_payload_json, arp_json, approver_role
            )
            VALUES ($1, $2, $3, $4::jsonb, $5::jsonb, $6)
            RETURNING id, run_id, action_type, action_payload_json, arp_json,
                      approver_role, decision, decision_reason, decided_at, created_at
            """,
            approval_id,
            run_id,
            action_type,
            json.dumps(action_payload),
            json.dumps(arp_json) if arp_json is not None else None,
            approver_role,
        )
        return _row_to_approval(row)

    async def get(self, approval_id: UUID) -> ApprovalRecord | None:
        row = await self._pool.fetchrow(
            """
            SELECT id, run_id, action_type, action_payload_json, arp_json,
                   approver_role, decision, decision_reason, decided_at, created_at
            FROM approvals WHERE id = $1
            """,
            approval_id,
        )
        return _row_to_approval(row) if row else None

    async def list_pending(self) -> list[ApprovalRecord]:
        rows = await self._pool.fetch(
            """
            SELECT id, run_id, action_type, action_payload_json, arp_json,
                   approver_role, decision, decision_reason, decided_at, created_at
            FROM approvals
            WHERE decision IS NULL
            ORDER BY created_at ASC
            """
        )
        return [_row_to_approval(row) for row in rows]

    async def list_pending_for_run(self, run_id: UUID) -> list[ApprovalRecord]:
        rows = await self._pool.fetch(
            """
            SELECT id, run_id, action_type, action_payload_json, arp_json,
                   approver_role, decision, decision_reason, decided_at, created_at
            FROM approvals
            WHERE run_id = $1 AND decision IS NULL
            ORDER BY created_at ASC
            """,
            run_id,
        )
        return [_row_to_approval(row) for row in rows]

    async def decide(
        self,
        approval_id: UUID,
        *,
        decision: ApprovalStatus,
        reason: str,
    ) -> ApprovalRecord | None:
        row = await self._pool.fetchrow(
            """
            UPDATE approvals
            SET decision = $2, decision_reason = $3, decided_at = NOW()
            WHERE id = $1
            RETURNING id, run_id, action_type, action_payload_json, arp_json,
                      approver_role, decision, decision_reason, decided_at, created_at
            """,
            approval_id,
            decision,
            reason,
        )
        return _row_to_approval(row) if row else None


def _row_to_approval(row: asyncpg.Record) -> ApprovalRecord:
    def _json(value: Any) -> dict[str, Any] | None:
        if value is None:
            return None
        if isinstance(value, str):
            return cast(dict[str, Any], json.loads(value))
        return cast(dict[str, Any], dict(value))

    return ApprovalRecord(
        id=row["id"],
        run_id=row["run_id"],
        action_type=row["action_type"],
        action_payload=_json(row["action_payload_json"]) or {},
        arp_json=_json(row["arp_json"]),
        approver_role=row["approver_role"],
        decision=row["decision"],
        decision_reason=row["decision_reason"],
        decided_at=row["decided_at"],
        created_at=row["created_at"],
    )
