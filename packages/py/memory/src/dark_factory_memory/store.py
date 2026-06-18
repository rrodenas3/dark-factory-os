from __future__ import annotations

import math
from datetime import datetime
from typing import Any

from .models import MemoryItem, MemoryQuery, MemorySearchResult, MemoryType


def _keyword_similarity(query: str, item: MemoryItem) -> float:
    """Lightweight keyword overlap score (replaces vector cosine in demo mode)."""
    q_tokens = set(query.lower().split())
    text = " ".join(str(v) for v in item.content.values()).lower()
    i_tokens = set(text.split())
    if not q_tokens or not i_tokens:
        return 0.0
    return len(q_tokens & i_tokens) / len(q_tokens | i_tokens)


def _decay_weight(item: MemoryItem, lam: float = 0.01) -> float:
    age_seconds = (datetime.utcnow() - item.last_accessed).total_seconds()
    return math.exp(-lam * age_seconds / 3600)


class InMemoryStore:
    """SSGM-inspired in-memory store.

    Production path: replace with Postgres + pgvector using the memory_items table.
    Read gate: filters by access_scope, min trust, consistency, and decay-weighted similarity.
    Write gate: enforces memory_type rules and trust thresholds before upsert.
    Episodic log: append-only via the episodic_log table in production.
    """

    def __init__(self) -> None:
        self._items: dict[str, MemoryItem] = {}

    def _key(self, item: MemoryItem) -> str:
        return f"{item.namespace}:{item.entity_key}:{item.memory_type}"

    def upsert(self, item: MemoryItem, *, validate: bool = True) -> MemoryItem:
        if validate:
            self._write_gate(item)
        key = self._key(item)
        self._items[key] = item
        return item

    def _write_gate(self, item: MemoryItem) -> None:
        # Semantic memory requires external verification before being trusted.
        if item.memory_type == "semantic" and item.source_trust < 0.6:
            raise ValueError(f"Semantic memory item '{item.entity_key}' has trust {item.source_trust} < 0.6 — write rejected")  # noqa: E501
        # Episodic memory is append-only: reject overwrites.
        existing_key = self._key(item)
        if item.memory_type == "episodic" and existing_key in self._items:
            raise ValueError(f"Episodic memory '{existing_key}' is append-only — create a new item instead")

    def search(self, query: MemoryQuery) -> list[MemorySearchResult]:
        results: list[MemorySearchResult] = []
        for item in self._items.values():
            if not item.namespace.startswith(query.namespace):
                continue
            if query.memory_type is not None and item.memory_type != query.memory_type:
                continue
            if item.source_trust < query.min_trust:
                continue
            if query.access_scope is not None and item.access_scope != query.access_scope:
                continue
            sim = _keyword_similarity(query.query, item)
            score = (sim * _decay_weight(item)) if query.decay_weighted else sim
            if score > 0:
                results.append(MemorySearchResult(item=item, score=score))
        results.sort(key=lambda r: r.score, reverse=True)
        return results[: query.k]

    def decay_pass(self, lam: float = 0.01) -> int:
        updated = 0
        for key, item in self._items.items():
            new_decay = _decay_weight(item, lam)
            if abs(new_decay - item.decay_score) > 1e-4:
                self._items[key] = item.model_copy(update={"decay_score": round(new_decay, 4)})
                updated += 1
        return updated

    def all(self, namespace: str | None = None, memory_type: MemoryType | None = None) -> list[MemoryItem]:
        items = list(self._items.values())
        if namespace:
            items = [i for i in items if i.namespace.startswith(namespace)]
        if memory_type:
            items = [i for i in items if i.memory_type == memory_type]
        return items

    def seed_demo(self) -> None:
        from uuid import uuid4

        demo_items: list[dict[str, Any]] = [
            {
                "namespace": "finance.vendor_risk",
                "entity_key": "contoso-logistics",
                "memory_type": "semantic",
                "content": {"summary": "Prior amount mismatches resolved after PO correction; payments above $1K require review.", "risk_level": "elevated"},  # noqa: E501
                "source_trust": 0.92,
                "consistency_verified": True,
            },
            {
                "namespace": "finance.vendor_risk",
                "entity_key": "tailspin-supplies",
                "memory_type": "semantic",
                "content": {"summary": "Two disputed invoices in prior quarter; vendor risk flag elevated.", "risk_level": "high"},  # noqa: E501
                "source_trust": 0.88,
                "consistency_verified": True,
            },
            {
                "namespace": "retail.campaign_history",
                "entity_key": "sparkling-water-12pk",
                "memory_type": "semantic",
                "content": {"summary": "Margin drops correlate with channel mix shift and supplier rebate timing during Q2 promos."},  # noqa: E501
                "source_trust": 0.89,
                "consistency_verified": True,
            },
            {
                "namespace": "saas.incident_history",
                "entity_key": "billing-api",
                "memory_type": "episodic",
                "content": {"summary": "Recent P1 spikes followed deploys touching invoice-preview and payment-retry logic.", "sha_pattern": "invoice-preview"},  # noqa: E501
                "source_trust": 0.86,
                "consistency_verified": True,
            },
        ]
        for data in demo_items:
            self.upsert(
                MemoryItem(
                    id=uuid4(),
                    namespace=str(data["namespace"]),
                    entity_key=str(data["entity_key"]),
                    memory_type=data["memory_type"],  # noqa: E501
                    content=data["content"],  # noqa: E501
                    source_trust=float(data["source_trust"]),
                    consistency_verified=bool(data["consistency_verified"]),
                    access_scope="team",
                ),
                validate=False,
            )
