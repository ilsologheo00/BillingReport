"""One-off cleanup: remove leftover sample/demo rows ("Acme Corp", "Northwind
Traders", "Contoso Ltd") that a database can end up with if any sync ever ran
while an integration's *_MODE was "mock" (ION, NinjaOne, or Acronis all ship
the same three placeholder tenants - see app/services/*/mock_provider.py).
Sync only upserts what the current provider returns, it never deletes rows a
past run created, so switching to "live" alone does not clean these up.

Safe to re-run: a demo customer is only deleted when it has zero
license_lines and zero sell_prices (i.e. it carries no real billing data) -
anything else is left in place and reported so a human can look at it.

Usage (inside the backend container): python -m app.scripts.purge_demo_data
"""

from app.database import SessionLocal
from app.models import AcronisOrgStat, Customer, NinjaOrgStat

_DEMO_NAMES = {"acme corp", "northwind traders", "contoso ltd"}


def main() -> None:
    db = SessionLocal()
    try:
        removed_customers = []
        kept_customers = []
        for customer in db.query(Customer).all():
            if customer.name.strip().lower() not in _DEMO_NAMES:
                continue
            if customer.license_lines or customer.sell_prices:
                kept_customers.append(customer.name)
                continue
            db.query(AcronisOrgStat).filter(AcronisOrgStat.customer_id == customer.id).delete()
            db.query(NinjaOrgStat).filter(NinjaOrgStat.customer_id == customer.id).delete()
            db.delete(customer)
            removed_customers.append(customer.name)

        removed_acronis = [
            row.tenant_name
            for row in db.query(AcronisOrgStat)
            .filter(AcronisOrgStat.customer_id.is_(None))
            .all()
            if row.tenant_name.strip().lower() in _DEMO_NAMES
        ]
        db.query(AcronisOrgStat).filter(
            AcronisOrgStat.customer_id.is_(None),
            AcronisOrgStat.tenant_name.in_(
                [n for n in ("Acme Corp", "Northwind Traders", "Contoso Ltd")]
            ),
        ).delete(synchronize_session=False)

        removed_ninja = [
            row.org_name
            for row in db.query(NinjaOrgStat)
            .filter(NinjaOrgStat.customer_id.is_(None))
            .all()
            if row.org_name.strip().lower() in _DEMO_NAMES
        ]
        db.query(NinjaOrgStat).filter(
            NinjaOrgStat.customer_id.is_(None),
            NinjaOrgStat.org_name.in_(
                [n for n in ("Acme Corp", "Northwind Traders", "Contoso Ltd")]
            ),
        ).delete(synchronize_session=False)

        db.commit()
    finally:
        db.close()

    if removed_customers:
        print(f"Removed demo customers: {', '.join(removed_customers)}")
    else:
        print("No demo customers to remove.")
    if kept_customers:
        print(f"Kept (has real billing data, review manually): {', '.join(kept_customers)}")
    if removed_acronis:
        print(f"Removed unmapped Acronis demo tenants: {', '.join(removed_acronis)}")
    if removed_ninja:
        print(f"Removed unmapped NinjaOne demo orgs: {', '.join(removed_ninja)}")


if __name__ == "__main__":
    main()
