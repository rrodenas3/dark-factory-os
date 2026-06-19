from __future__ import annotations

import os
from pathlib import Path

import asyncpg
import pytest
from dark_factory_memory import MemoryItem, MemoryQuery, PostgresMemoryStore
from dark_factory_persistence.migrate import run_migrations

ROOT = Path(__file__).resolve().parents[4]
MIGRATIONS_DIR = ROOT / "infra" / "migrations"


@pytest.fixture
async def pool() -> asyncpg.Pool:
    url = os.environ.get("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL not set - skipping Postgres memory integration tests")
    pool = await asyncpg.create_pool(url, min_size=1, max_size=2)
    assert pool is not None
    await run_migrations(pool, directory=MIGRATIONS_DIR)
    yield pool
    await pool.close()


@pytest.fixture
async def store(pool: asyncpg.Pool) -> PostgresMemoryStore:
    await pool.execute("DELETE FROM memory_items WHERE namespace LIKE 'test.%'")
    return PostgresMemoryStore(pool)


def _item(entity_key: str, *, trust: float = 0.9, verified: bool = True) -> MemoryItem:
    return MemoryItem(
        namespace="test.finance.vendor_risk",
        entity_key=entity_key,
        memory_type="semantic",
        content={"summary": "Contoso vendor has low risk and clean payment history."},
        source_trust=trust,
        consistency_verified=verified,
        access_scope="team",
    )


@pytest.mark.asyncio
async def test_pg_store_upsert_and_search(store: PostgresMemoryStore) -> None:
    await store.upsert(_item("contoso-logistics"))

    results = await store.search(
        MemoryQuery(query="low risk vendor", namespace="test.finance", access_scope="team")
    )

    assert len(results) == 1
    assert results[0].entity_key == "contoso-logistics"
    assert results[0].score > 0


@pytest.mark.asyncio
async def test_pg_store_filters_unverified_memory(store: PostgresMemoryStore) -> None:
    await store.upsert(_item("unverified-vendor", verified=False), validate=False)

    results = await store.search(MemoryQuery(query="vendor risk", namespace="test.finance"))

    assert results == []


@pytest.mark.asyncio
async def test_pg_store_rejects_low_trust_semantic(store: PostgresMemoryStore) -> None:
    with pytest.raises(ValueError, match="trust"):
        await store.upsert(_item("risky-vendor", trust=0.3))


@pytest.mark.asyncio
async def test_pg_store_enforces_episodic_append_only(store: PostgresMemoryStore) -> None:
    event = MemoryItem(
        namespace="test.saas.incident_history",
        entity_key="billing-api",
        memory_type="episodic",
        content={"summary": "P1 incident after deployment."},
        source_trust=0.9,
        consistency_verified=True,
    )
    await store.upsert(event, validate=False)

    with pytest.raises(ValueError, match="append-only"):
        await store.upsert(event)
