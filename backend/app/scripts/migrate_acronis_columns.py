"""One-off migration: add the Acronis columns to `customers` on a database
created before the Acronis integration existed. SQLAlchemy's create_all()
only creates missing tables, never adds columns to existing ones, so this
must be run manually after deploying the Acronis feature to an existing
database. Safe to re-run - skips columns that already exist.

Usage (inside the backend container): python -m app.scripts.migrate_acronis_columns
"""

import sqlite3

from app.config import settings

_NEW_COLUMNS = [
    ("acronis_tenant_name", "VARCHAR"),
    ("backup_total_bytes", "NUMERIC(20,0)"),
    ("backup_used_bytes", "NUMERIC(20,0)"),
    ("backup_machines_count", "INTEGER"),
    ("backup_mailboxes_count", "INTEGER"),
    ("acronis_synced_at", "DATETIME"),
]


def main() -> None:
    db_path = settings.database_url.removeprefix("sqlite:///")
    conn = sqlite3.connect(db_path)
    try:
        existing = {row[1] for row in conn.execute("PRAGMA table_info(customers)")}
        added = []
        for name, coltype in _NEW_COLUMNS:
            if name not in existing:
                conn.execute(f"ALTER TABLE customers ADD COLUMN {name} {coltype}")
                added.append(name)
        conn.commit()
    finally:
        conn.close()

    if added:
        print(f"Added columns: {', '.join(added)}")
    else:
        print("No columns to add - already up to date.")


if __name__ == "__main__":
    main()
