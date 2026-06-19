from __future__ import annotations

import json
from collections.abc import Iterable
from typing import cast
from uuid import UUID

import asyncpg

from .models import MemoryItem, MemoryQuery, MemorySearchResult, MemoryType
from .store import _decay_weight, _keyword_similarity

_MEMORY_SELECT = """
    SELECT id, namespace, entity_key, memory_type, content_json, access_scope,
           source_trust, decay_score, consistency_verified, created_at, last_accessed
"""


class PostgresMemoryStore:
    """Postgres-backed SSGM memory store using the canonical memory_items table."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def upsert(self, item: MemoryItem, *, validate: bool = True) -> MemoryItem:
        if validate:
            await self._write_gate(item)

        row = await self._pool.fetchrow(
            """
            INSERT INTO memory_items (
                id, namespace, entity_key, memory_type, content_json, access_scope,
                source_trust, decay_score, consistency_verified, created_at, last_accessed
            )
            VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7, $8, $9, $10, $11)
            ON CONFLICT (namespace, entity_key, memory_type)
            DO UPDATE SET
                content_json = EXCLUDED.content_json,
                access_scope = EXCLUDED.access_scope,
                source_trust = EXCLUDED.source_trust,
                decay_score = EXCLUDED.decay_score,
                consistency_verified = EXCLUDED.consistency_verified,
                last_accessed = EXCLUDED.last_accessed
            RETURNING id, namespace, entity_key, memory_type, content_json, access_scope,
                      source_trust, decay_score, consistency_verified, created_at, last_accessed
            """,
            item.id,
            item.namespace,
            item.entity_key,
            item.memory_type,
            json.dumps(item.content),
            item.access_scope,
            item.source_trust,
            item.decay_score,
            item.consistency_verified,
            item.created_at,
            item.last_accessed,
        )
        return _row_to_item(row)

    async def search(self, query: MemoryQuery) -> list[MemorySearchResult]:
        rows = await self._pool.fetch(
            _MEMORY_SELECT
            + """
            FROM memory_items
            WHERE namespace LIKE ($1 || '%')
              AND ($2::text IS NULL OR memory_type = $2)
              AND source_trust >= $3
              AND consistency_verified = TRUE
              AND ($4::text IS NULL OR access_scope = $4)
            ORDER BY last_accessed DESC
            LIMIT 200
            """,
            query.namespace,
            query.memory_type,
            query.min_trust,
            query.access_scope,
        )

        results: list[MemorySearchResult] = []
        for row in rows:
            item = _row_to_item(row)
            sim = _keyword_similarity(query.query, item)
            score = (sim * _decay_weight(item)) if query.decay_weighted else sim
            if score > 0:
                results.append(MemorySearchResult(item=item, score=score))

        results.sort(key=lambda result: result.score, reverse=True)
        selected = results[: query.k]
        await self._mark_accessed(result.item.id for result in selected)
        return selected

    async def decay_pass(self) -> int:
        rows = await self._pool.fetch(
            _MEMORY_SELECT
            + """
            FROM memory_items
            """
        )
        updated = 0
        for row in rows:
            item = _row_to_item(row)
            new_decay = round(_decay_weight(item), 4)
            if abs(new_decay - item.decay_score) > 1e-4:
                await self._pool.execute("UPDATE memory_items SET decay_score = $2 WHERE id = $1", item.id, new_decay)
                updated += 1
        return updated

    async def all(self, namespace: str | None = None, memory_type: MemoryType | None = None) -> list[MemoryItem]:
        rows = await self._pool.fetch(
            _MEMORY_SELECT
            + """
            FROM memory_items
            WHERE ($1::text IS NULL OR namespace LIKE ($1 || '%'))
              AND ($2::text IS NULL OR memory_type = $2)
            ORDER BY created_at ASC
            """,
            namespace,
            memory_type,
        )
        return [_row_to_item(row) for row in rows]

    async def _write_gate(self, item: MemoryItem) -> None:
        if item.memory_type == "semantic" and item.source_trust < 0.6:
            raise ValueError(
                f"Semantic memory item '{item.entity_key}' has trust {item.source_trust} < 0.6 - write rejected"
            )

        if item.memory_type == "episodic":
            existing = await self._pool.fetchval(
                """
                SELECT id FROM memory_items
                WHERE namespace = $1 AND entity_key = $2 AND memory_type = $3
                """,
                item.namespace,
                item.entity_key,
                item.memory_type,
            )
            if existing is not None:
                key = f"{item.namespace}:{item.entity_key}:{item.memory_type}"
                raise ValueError(f"Episodic memory '{key}' is append-only - create a new item instead")

    async def _mark_accessed(self, item_ids: Iterable[UUID]) -> None:
        ids = list(item_ids)
        if not ids:
            return
        await self._pool.execute("UPDATE memory_items SET last_accessed = NOW() WHERE id = ANY($1::uuid[])", ids)


def _row_to_item(row: asyncpg.Record) -> MemoryItem:
    content = row["content_json"]
    if isinstance(content, str):
        content = json.loads(content)
    return MemoryItem(
        id=row["id"],
        namespace=row["namespace"],
        entity_key=row["entity_key"],
        memory_type=row["memory_type"],
        content=cast(dict[str, object], dict(content)),
        access_scope=row["access_scope"],
        source_trust=float(row["source_trust"] or 0),
        decay_score=float(row["decay_score"] or 0),
        consistency_verified=bool(row["consistency_verified"]),
        created_at=row["created_at"],
        last_accessed=row["last_accessed"],
    )
