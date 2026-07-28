"""One-off migration: add the server/workstation/VM breakdown columns to
`customers` and `acronis_org_stats`, replacing the single
`backup_machines_count` column (left in place, unused, rather than dropped -
SQLite has no cheap ALTER COLUMN/DROP COLUMN path worth the risk here).
SQLAlchemy's create_all() only creates missing tables, never adds columns to
existing ones, so this must be run manually after deploying this feature to
an existing database. Safe to re-run - skips columns that already exist.

Usage (inside the backend container): python -m app.scripts.migrate_acronis_machine_breakdown
"""

import sqlite3

from app.config import settings

_NEW_COLUMNS = ["backup_server_count", "backup_workstation_count", "backup_vm_count"]


def main() -> None:
    db_path = settings.database_url.removeprefix("sqlite:///")
    conn = sqlite3.connect(db_path)
    try:
        added = []
        for table in ("customers", "acronis_org_stats"):
            existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
            for name in _NEW_COLUMNS:
                if name not in existing:
                    conn.execute(f"ALTER TABLE {table} ADD COLUMN {name} INTEGER")
                    added.append(f"{table}.{name}")
        conn.commit()
    finally:
        conn.close()

    if added:
        print(f"Added columns: {', '.join(added)}")
    else:
        print("No columns to add - already up to date.")


if __name__ == "__main__":
    main()
