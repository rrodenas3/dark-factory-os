from __future__ import annotations

import json
from typing import Any, cast
from uuid import UUID, uuid4

import asyncpg

from .models import KnowledgeEdgeRecord, KnowledgeEntityRecord


class KnowledgeGraphRepository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def upsert_entity(
        self,
        *,
        entity_type: str,
        entity_key: str,
        props_json: dict[str, Any] | None = None,
    ) -> KnowledgeEntityRecord:
        row = await self._pool.fetchrow(
            """
            INSERT INTO kg_entities (id, entity_type, entity_key, props_json)
            VALUES ($1, $2, $3, $4::jsonb)
            ON CONFLICT (entity_type, entity_key)
            DO UPDATE SET props_json = EXCLUDED.props_json
            RETURNING id, entity_type, entity_key, props_json
            """,
            uuid4(),
            entity_type,
            entity_key,
            json.dumps(props_json or {}),
        )
        return _row_to_entity(row)

    async def create_edge(
        self,
        *,
        source_entity_id: UUID,
        relation: str,
        target_entity_id: UUID,
        props_json: dict[str, Any] | None = None,
    ) -> KnowledgeEdgeRecord:
        row = await self._pool.fetchrow(
            """
            INSERT INTO kg_edges (id, source_entity_id, relation, target_entity_id, props_json)
            VALUES ($1, $2, $3, $4, $5::jsonb)
            RETURNING id, source_entity_id, relation, target_entity_id, props_json
            """,
            uuid4(),
            source_entity_id,
            relation,
            target_entity_id,
            json.dumps(props_json or {}),
        )
        return _row_to_edge(row)

    async def graph(self, *, limit: int = 100) -> dict[str, object]:
        nodes = await self._pool.fetch(
            """
            SELECT id, entity_type, entity_key, props_json
            FROM kg_entities
            ORDER BY entity_type, entity_key
            LIMIT $1
            """,
            limit,
        )
        edges = await self._pool.fetch(
            """
            SELECT
              e.relation,
              e.props_json,
              source.entity_key AS source_key,
              target.entity_key AS target_key
            FROM kg_edges e
            JOIN kg_entities source ON source.id = e.source_entity_id
            JOIN kg_entities target ON target.id = e.target_entity_id
            ORDER BY e.relation, source.entity_key, target.entity_key
            LIMIT $1
            """,
            limit,
        )
        return {
            "generated_from": "postgres_kg",
            "nodes": [_node_to_api(row) for row in nodes],
            "edges": [_edge_to_api(row) for row in edges],
        }


def _json_dict(value: object) -> dict[str, Any]:
    if isinstance(value, str):
        value = json.loads(value)
    return cast(dict[str, Any], value or {})


def _row_to_entity(row: asyncpg.Record) -> KnowledgeEntityRecord:
    return KnowledgeEntityRecord(
        id=row["id"],
        entity_type=row["entity_type"],
        entity_key=row["entity_key"],
        props_json=_json_dict(row["props_json"]),
    )


def _row_to_edge(row: asyncpg.Record) -> KnowledgeEdgeRecord:
    return KnowledgeEdgeRecord(
        id=row["id"],
        source_entity_id=row["source_entity_id"],
        relation=row["relation"],
        target_entity_id=row["target_entity_id"],
        props_json=_json_dict(row["props_json"]),
    )


def _node_to_api(row: asyncpg.Record) -> dict[str, object]:
    props = _json_dict(row["props_json"])
    return {
        "id": row["entity_key"],
        "label": str(props.get("label") or row["entity_key"]),
        "type": row["entity_type"],
        "vertical": str(props.get("vertical") or "global"),
        "risk": str(props.get("risk") or "unknown"),
    }


def _edge_to_api(row: asyncpg.Record) -> dict[str, object]:
    props = _json_dict(row["props_json"])
    return {
        "source": row["source_key"],
        "relation": row["relation"],
        "target": row["target_key"],
        "evidence": str(props.get("evidence") or "Persisted KG relationship."),
    }
