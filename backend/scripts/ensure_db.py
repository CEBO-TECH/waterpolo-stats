"""Ensure the target database exists before running migrations.

PostgreSQL's POSTGRES_DB env var only creates the database on the FIRST
initialization of an empty data directory. When a volume already contains
data (e.g. from a previous deployment), the target database is never created.

This script connects to the maintenance `postgres` database and creates the
target database if it does not exist. Idempotent — safe to run on every start.
"""

import asyncio
import sys
from urllib.parse import unquote, urlparse

import asyncpg

from src.config import settings


async def ensure_database() -> None:
    # Strip the SQLAlchemy "+asyncpg" dialect suffix for raw asyncpg parsing
    raw_url = settings.DATABASE_URL.replace("+asyncpg", "")
    parsed = urlparse(raw_url)

    db_name = parsed.path.lstrip("/")
    if not db_name:
        print("[ensure_db] No database name in DATABASE_URL, skipping")
        return

    conn_kwargs = {
        "host": parsed.hostname,
        "port": parsed.port or 5432,
        "user": unquote(parsed.username) if parsed.username else None,
        "password": unquote(parsed.password) if parsed.password else None,
        "database": "postgres",  # maintenance DB — always exists
    }

    # Retry — postgres may still be warming up even after healthcheck
    last_err = None
    for attempt in range(1, 11):
        try:
            conn = await asyncpg.connect(**conn_kwargs)
            break
        except Exception as e:  # noqa: BLE001
            last_err = e
            print(f"[ensure_db] Postgres not ready (attempt {attempt}/10): {e}")
            await asyncio.sleep(2)
    else:
        print(f"[ensure_db] Could not connect to postgres: {last_err}")
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
