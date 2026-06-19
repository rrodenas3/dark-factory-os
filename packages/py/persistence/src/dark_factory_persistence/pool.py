from __future__ import annotations

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import asyncpg

_pool: asyncpg.Pool | None = None


def database_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        msg = "DATABASE_URL is required for Postgres persistence"
        raise RuntimeError(msg)
    return url


async def get_pool(*, apply_migrations: bool = True) -> asyncpg.Pool:
    global _pool
    if _pool is None:
        import asyncpg

        from .migrate import run_migrations as _run_migrations

        _pool = await asyncpg.create_pool(database_url(), min_size=1, max_size=5)
        if apply_migrations:
            await _run_migrations(_pool)
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
