from datetime import datetime

from sqlalchemy.orm import Session

from app.models import Customer, NinjaOrgStat, NinjaSyncLog
from app.services.name_matching import normalize_name, unique_normalized_index
from app.services.ninjaone.base import NinjaApiError, NinjaOneProvider


def ninjaone_sync_all(db: Session, provider: NinjaOneProvider) -> NinjaSyncLog:
    log = NinjaSyncLog(started_at=datetime.utcnow(), status="running")
    db.add(log)
    db.commit()
    db.refresh(log)

    try:
        stats = provider.get_org_stats()
        customers = db.query(Customer).all()
        customers_by_id = {c.id: c for c in customers}
        exact_by_name = {c.name.strip().lower(): c for c in customers}
        # Only trust the normalized match when it resolves to exactly one
        # customer - if two customers normalize to the same key (e.g. two
        # differently-formatted "Combitras" rows), matching by that key would
        # be a guess, so skip it and leave those unmatched.
        normalized_unique = unique_normalized_index(customers, lambda c: c.name)

        org_rows = {row.org_name: row for row in db.query(NinjaOrgStat).all()}

        matched = 0
        unmatched = 0
        for stat in stats:
            row = org_rows.get(stat.org_name)
            if row is None:
                row = NinjaOrgStat(org_name=stat.org_name)
                db.add(row)
                org_rows[stat.org_name] = row

            row.device_count = stat.device_count
            row.sentinelone_count = stat.sentinelone_count
            row.synced_at = datetime.utcnow()

            # A manually-mapped org (or one auto-matched on a previous sync)
            # keeps its customer_id; only try auto-matching when it's unset,
            # so a manual mapping is never silently overwritten.
            if row.customer_id is None:
                customer = exact_by_name.get(stat.org_name.strip().lower())
                if customer is None:
                    customer = normalized_unique.get(normalize_name(stat.org_name))
                if customer is not None:
                    row.customer_id = customer.id

            if row.customer_id is None:
                unmatched += 1
                continue

            customer = customers_by_id.get(row.customer_id)
            if customer is None:
                unmatched += 1
                continue
            customer.ninja_org_name = stat.org_name
            customer.device_count = stat.device_count
            customer.sentinelone_count = stat.sentinelone_count
            customer.ninja_synced_at = datetime.utcnow()
            matched += 1

        log.status = "success"
        log.orgs_matched = matched
        log.orgs_unmatched = unmatched
    except NinjaApiError as exc:
        db.rollback()
        db.add(log)
        log.status = "failed"
        log.error_message = str(exc)
    except Exception as exc:  # noqa: BLE001 - want any unexpected failure logged, not crash the request
        db.rollback()
        db.add(log)
        log.status = "failed"
        log.error_message = str(exc)
    finally:
        log.finished_at = datetime.utcnow()
        db.commit()
        db.refresh(log)

    return log


def get_unmapped_orgs(db: Session) -> list[NinjaOrgStat]:
    return db.query(NinjaOrgStat).filter(NinjaOrgStat.customer_id.is_(None)).order_by(NinjaOrgStat.org_name).all()


def create_standalone_customer_for_org(db: Session, org_name: str) -> NinjaOrgStat:
    """For a NinjaOne org with no StreamOne/ION counterpart: create a customer
    row with no ion_customer_id, so it can still be listed (with its NinjaOne
    stats) instead of sitting hidden in the unmapped-orgs list forever."""
    row = db.query(NinjaOrgStat).filter(NinjaOrgStat.org_name == org_name).first()
    if row is None:
        raise ValueError(f"Unknown NinjaOne organization: {org_name}")
    if row.customer_id is not None:
        raise ValueError(f"NinjaOne organization already mapped: {org_name}")

    customer = Customer(
        ion_customer_id=None,
        name=row.org_name,
        ninja_org_name=row.org_name,
        device_count=row.device_count,
        sentinelone_count=row.sentinelone_count,
        ninja_synced_at=datetime.utcnow(),
    )
    db.add(customer)
    db.flush()

    row.customer_id = customer.id
    db.commit()
    db.refresh(row)
    return row


def set_org_mapping(db: Session, org_name: str, customer_id: int | None) -> NinjaOrgStat:
    row = db.query(NinjaOrgStat).filter(NinjaOrgStat.org_name == org_name).first()
    if row is None:
        raise ValueError(f"Unknown NinjaOne organization: {org_name}")

    row.customer_id = customer_id

    if customer_id is not None:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if customer is None:
            raise ValueError(f"Unknown customer id: {customer_id}")
        customer.ninja_org_name = row.org_name
        customer.device_count = row.device_count
        customer.sentinelone_count = row.sentinelone_count
        customer.ninja_synced_at = datetime.utcnow()

    db.commit()
    db.refresh(row)
    return row
