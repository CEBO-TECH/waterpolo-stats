"""Ensure the target database exists before running migrations.

PostgreSQL's POSTGRES_DB env var only creates the database on the FIRST
initialization of an empty data directory. When a volume already contains
data (e.g. from a previous deployment), the target database is never created.

This script connects to a maintenance database and creates the target
database if it does not exist. Idempotent — safe to run on every start.

We try multiple maintenance databases because a non-standard volume may be
missing the default `postgres` database. `template1` is guaranteed to exist
in every PostgreSQL cluster (CREATE DATABASE uses it as the default template
and it cannot be dropped under normal operation).
"""

import asyncio
import sys
from urllib.parse import unquote, urlparse

import asyncpg

from src.config import settings

# Maintenance databases to try, in order. template1 always exists.
MAINTENANCE_DBS = ["postgres", "template1"]


async def _connect(conn_kwargs: dict, maintenance_db: str):
    kwargs = {**conn_kwargs, "database": maintenance_db}
    return await asyncpg.connect(**kwargs)


async def ensure_database() -> None:
    # Strip the SQLAlchemy "+asyncpg" dialect suffix for raw asyncpg parsing
    raw_url = settings.DATABASE_URL.replace("+asyncpg", "")
    parsed = urlparse(raw_url)

    db_name = parsed.path.lstrip("/")
    if not db_name:
        print("[ensure_db] No database name in DATABASE_URL, skipping")
        return

    base_kwargs = {
        "host": parsed.hostname,
        "port": parsed.port or 5432,
        "user": unquote(parsed.username) if parsed.username else None,
        "password": unquote(parsed.password) if parsed.password else None,
    }

    # Retry — postgres may still be warming up even after the healthcheck.
    # On each attempt, try each candidate maintenance database.
    conn = None
    last_err = None
    for attempt in range(1, 16):
        for maint_db in MAINTENANCE_DBS:
            try:
                conn = await _connect(base_kwargs, maint_db)
                print(f"[ensure_db] Connected via maintenance db '{maint_db}'")
                break
            except asyncpg.InvalidCatalogNameError as e:
                # This maintenance db doesn't exist — try the next candidate
                last_err = e
                continue
            except Exception as e:  # noqa: BLE001 — server warming up, etc.
                last_err = e
                break  # network/auth error — retry whole attempt after sleep
        if conn is not None:
            break
        print(f"[ensure_db] Not ready (attempt {attempt}/15): {last_err}")
        await asyncio.sleep(2)

    if conn is None:
        print(f"[ensure_db] Could not connect to any maintenance database: {last_err}")
        sys.exit(1)

    try:
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", db_name
        )
        if exists:
            print(f"[ensure_db] Database '{db_name}' already exists")
        else:
            # Identifier can't be parameterized — db_name comes from our own
            # DATABASE_URL config, not user input, so quoting is sufficient.
            await conn.execute(f'CREATE DATABASE "{db_name}"')
            print(f"[ensure_db] Created database '{db_name}'")
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(ensure_database())
