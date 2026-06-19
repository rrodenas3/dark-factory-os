from __future__ import annotations

import os
from pathlib import Path

import asyncpg


async def ensure_schema_migrations(conn: asyncpg.Connection) -> None:
    await conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            filename TEXT PRIMARY KEY,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )


async def is_effectively_applied(conn: asyncpg.Connection, filename: str) -> bool:
    """Detect migrations that Docker entrypoint may have applied before the ledger existed."""
    if filename.startswith("001_"):
        return bool(await conn.fetchval("SELECT to_regclass('public.runs') IS NOT NULL"))
    if filename.startswith("002_"):
        return bool(
            await conn.fetchval(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.columns
                    WHERE table_schema = 'public'
                      AND table_name = 'runs'
                      AND column_name = 'checkpoint_json'
                )
                """
            )
        )
    return False


def migrations_dir() -> Path:
    override = os.environ.get("DFOS_MIGRATIONS_DIR")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[5] / "infra" / "migrations"


async def run_migrations(pool: asyncpg.Pool, *, directory: Path | None = None) -> list[str]:
    """Apply pending SQL migrations idempotently. Returns newly applied filenames."""
    root = directory or migrations_dir()
    if not root.is_dir():
        msg = f"Migrations directory not found: {root}"
        raise FileNotFoundError(msg)

    files = sorted(root.glob("*.sql"))
    applied: list[str] = []

    async with pool.acquire() as conn:
        await ensure_schema_migrations(conn)
        for path in files:
            already = await conn.fetchval(
                "SELECT 1 FROM schema_migrations WHERE filename = $1",
                path.name,
            )
            if already:
                continue
            if await is_effectively_applied(conn, path.name):
                await conn.execute(
                    "INSERT INTO schema_migrations (filename) VALUES ($1) ON CONFLICT DO NOTHING",
                    path.name,
                )
                continue
            sql = path.read_text(encoding="utf-8")
            async with conn.transaction():
                await conn.execute(sql)
                await conn.execute(
                    "INSERT INTO schema_migrations (filename) VALUES ($1)",
                    path.name,
                )
            applied.append(path.name)

    return applied
