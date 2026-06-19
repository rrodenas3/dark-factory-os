from __future__ import annotations

import os
from pathlib import Path

import asyncpg
import pytest
from dark_factory_persistence.migrate import migrations_dir, run_migrations

ROOT = Path(__file__).resolve().parents[1]


def _database_url() -> str | None:
    return os.environ.get("DATABASE_URL")


@pytest.mark.asyncio
async def test_run_migrations_is_idempotent() -> None:
    url = _database_url()
    if not url:
        pytest.skip("DATABASE_URL not set")
    pool = await asyncpg.create_pool(url, min_size=1, max_size=1)
    assert pool is not None
    try:
        first = await run_migrations(pool, directory=ROOT / "infra" / "migrations")
        second = await run_migrations(pool, directory=ROOT / "infra" / "migrations")
        assert isinstance(first, list)
        assert second == []
    finally:
        await pool.close()


def test_migrations_dir_points_at_repo() -> None:
    path = migrations_dir()
    assert path.name == "migrations"
    assert (path / "001_initial_schema.sql").exists()
