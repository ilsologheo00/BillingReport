"""One-off migration: allow customers.ion_customer_id to be NULL.

Needed so NinjaOne-only customers (present in NinjaOne but with no StreamOne/ION
counterpart) can be stored as standalone rows - see
ninjaone_sync_service.create_standalone_customer_for_org. SQLite bakes NOT NULL
into the table definition and has no ALTER COLUMN, so the table must be rebuilt.
Safe to re-run - no-ops if the column is already nullable.

Usage (inside the backend container): python -m app.scripts.migrate_customer_ion_nullable
"""

import sqlite3

from app.config import settings


def main() -> None:
    db_path = settings.database_url.removeprefix("sqlite:///")
    conn = sqlite3.connect(db_path)
    try:
        col = next(row for row in conn.execute("PRAGMA table_info(customers)") if row[1] == "ion_customer_id")
        already_nullable = col[3] == 0  # row[3] is the `notnull` flag
        if already_nullable:
            print("Already up to date - ion_customer_id is nullable.")
            return

        conn.execute("PRAGMA foreign_keys=OFF")
        cur = conn.cursor()
        cur.execute("BEGIN")
        cur.execute("ALTER TABLE customers RENAME TO customers_old")
        cur.execute(
            """
            CREATE TABLE customers (
                id INTEGER NOT NULL,
                ion_customer_id VARCHAR,
                name VARCHAR NOT NULL,
                created_at DATETIME,
                updated_at DATETIME,
                ninja_org_name TEXT,
                device_count INTEGER,
                sentinelone_count INTEGER,
                ninja_synced_at DATETIME,
                acronis_tenant_name TEXT,
                backup_total_bytes NUMERIC,
                backup_used_bytes NUMERIC,
                backup_machines_count INTEGER,
                backup_mailboxes_count INTEGER,
                acronis_synced_at DATETIME,
                PRIMARY KEY (id)
            )
            """
        )
        cur.execute(
            """
            INSERT INTO customers (
                id, ion_customer_id, name, created_at, updated_at,
                ninja_org_name, device_count, sentinelone_count, ninja_synced_at,
                acronis_tenant_name, backup_total_bytes, backup_used_bytes,
                backup_machines_count, backup_mailboxes_count, acronis_synced_at
            )
            SELECT
                id, ion_customer_id, name, created_at, updated_at,
                ninja_org_name, device_count, sentinelone_count, ninja_synced_at,
                acronis_tenant_name, backup_total_bytes, backup_used_bytes,
                backup_machines_count, backup_mailboxes_count, acronis_synced_at
            FROM customers_old
            """
        )
        cur.execute("DROP INDEX IF EXISTS ix_customers_ion_customer_id")
        cur.execute("CREATE UNIQUE INDEX ix_customers_ion_customer_id ON customers (ion_customer_id)")
        cur.execute("DROP TABLE customers_old")
        conn.commit()
        conn.execute("PRAGMA foreign_keys=ON")
    finally:
        conn.close()

    print("Migrated: ion_customer_id is now nullable.")


if __name__ == "__main__":
    main()
