"""One-off migration for two related changes:

1. Add `customers.consolidate_license_lines` (nullable, treated as True/on when
   unset) - simple ADD COLUMN.
2. Reshape `purchase_orders` from (customer_id, sku) to license_line_id, so a
   customer with consolidation disabled can carry a distinct PO per purchase
   batch instead of one per SKU. Since this table was only just introduced and
   holds no real data yet, the old-shaped table (if present) is dropped outright
   rather than migrated in place - SQLAlchemy's create_all() then recreates it
   with the new schema on next app startup.

Safe to re-run - skips whatever's already up to date.

Usage (inside the backend container): python -m app.scripts.migrate_consolidation_and_po_schema
"""

import sqlite3

from app.config import settings


def main() -> None:
    db_path = settings.database_url.removeprefix("sqlite:///")
    conn = sqlite3.connect(db_path)
    try:
        customers_columns = {row[1] for row in conn.execute("PRAGMA table_info(customers)")}
        if "consolidate_license_lines" not in customers_columns:
            conn.execute("ALTER TABLE customers ADD COLUMN consolidate_license_lines BOOLEAN")
            print("Added column: customers.consolidate_license_lines")
        else:
            print("customers.consolidate_license_lines already present.")

        po_columns = {row[1] for row in conn.execute("PRAGMA table_info(purchase_orders)")}
        if po_columns and "license_line_id" not in po_columns:
            conn.execute("DROP TABLE purchase_orders")
            print("Dropped old-shaped purchase_orders table - create_all() will recreate it on startup.")
        else:
            print("purchase_orders already up to date (or doesn't exist yet).")

        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
