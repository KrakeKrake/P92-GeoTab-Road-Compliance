#!/usr/bin/env python3
"""Apply the compliance SQL files exactly once.

The SQL files are listed explicitly because order matters: schema, core seed,
goods schema, goods seed. Each file runs in its own transaction and is recorded
in compliance.schema_migrations, so an interrupted run can be retried safely.
Seeded rows are only initial defaults; the web app can edit them afterwards.
"""
import os
import sys
import time
from pathlib import Path

import psycopg2

HERE = Path(__file__).resolve().parent
MIGRATIONS = [
    "combined_create_tables.sql",
    "combined_seed.sql",
]
CORE = {"combined_create_tables.sql", "combined_seed.sql"}

# The schema and seed files were merged into two combined files. A database
# migrated by the older list already has their contents; map the old versions
# so the merged files are not applied a second time (the seeds use plain
# INSERTs and would fail on the existing primary keys).
LEGACY_VERSIONS = {
    "combined_create_tables.sql": {
        "create_table.sql",
        "create_goods_tables.sql",
    },
    "combined_seed.sql": {
        "hvnl_seed.sql",
        "goods_seed.sql",
    },
}

CONNECT_TIMEOUT = float(os.environ.get("DB_CONNECT_TIMEOUT", "120"))


def connect():
    url = os.environ.get("DATABASE_URL")
    if not url:
        sys.exit("DATABASE_URL is not set")
    dsn = url.replace("+psycopg2", "").replace("+psycopg", "")
    deadline = time.monotonic() + CONNECT_TIMEOUT
    attempt = 0
    while True:
        try:
            return psycopg2.connect(dsn)
        except psycopg2.OperationalError as exc:
            if time.monotonic() >= deadline:
                sys.exit(f"database not reachable within {CONNECT_TIMEOUT:.0f}s: {exc}")
            attempt += 1
            delay = min(attempt, 5)
            print(
                f"database not ready yet ({exc}); retrying in {delay}s",
                file=sys.stderr,
                flush=True,
            )
            time.sleep(delay)


def table_exists(cur, name):
    cur.execute("SELECT to_regclass(%s) IS NOT NULL", (name,))
    return cur.fetchone()[0]


def main():
    reset = "--reset" in sys.argv
    dry_run = "--dry-run" in sys.argv

    with connect() as conn:
        with conn.cursor() as cur:
            if reset:
                print("dropping compliance and account schemas")
                if not dry_run:
                    cur.execute(
                        "DROP SCHEMA IF EXISTS compliance CASCADE;"
                        "DROP SCHEMA IF EXISTS account CASCADE;"
                    )
                    conn.commit()

            if dry_run:
                print("would apply:", ", ".join(MIGRATIONS))
                return

            cur.execute("CREATE SCHEMA IF NOT EXISTS compliance;")
            had_tracking = table_exists(cur, "compliance.schema_migrations")
            cur.execute(
                "CREATE TABLE IF NOT EXISTS compliance.schema_migrations ("
                " version TEXT PRIMARY KEY,"
                " applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"
            )
            conn.commit()

            applied = set()
            if had_tracking:
                cur.execute("SELECT version FROM compliance.schema_migrations")
                applied = {row[0] for row in cur.fetchall()}
                # An existing install may still list the pre-merge file names.
                # Record the merged names that those versions cover so the
                # plain INSERT seeds are not replayed.
                legacy_applied = {
                    merged
                    for merged, legacy in LEGACY_VERSIONS.items()
                    if merged not in applied and legacy.issubset(applied)
                }
                if legacy_applied:
                    cur.executemany(
                        "INSERT INTO compliance.schema_migrations (version) VALUES (%s)"
                        " ON CONFLICT DO NOTHING",
                        [(name,) for name in legacy_applied],
                    )
                    applied |= legacy_applied
                    conn.commit()
            elif table_exists(cur, "compliance.vehicle_profiles"):
                # Database created by the older setup.sh: the core schema and
                # seeds are present, but there is no migration history yet.
                applied |= CORE
                if table_exists(cur, "compliance.goods_types"):
                    cur.execute("SELECT count(*) FROM compliance.goods_types")
                    if cur.fetchone()[0] > 0:
                        applied |= {"create_goods_tables.sql", "goods_seed.sql"}
                cur.executemany(
                    "INSERT INTO compliance.schema_migrations (version) VALUES (%s)"
                    " ON CONFLICT DO NOTHING",
                    [(name,) for name in applied],
                )
                conn.commit()

            for name in MIGRATIONS:
                if name in applied:
                    continue
                path = HERE / name
                print(f"applying {name}")
                try:
                    cur.execute(path.read_text())
                    cur.execute(
                        "INSERT INTO compliance.schema_migrations (version) VALUES (%s)",
                        (name,),
                    )
                    conn.commit()
                except Exception:
                    conn.rollback()
                    raise

    print("compliance schema is up to date")


if __name__ == "__main__":
    main()
