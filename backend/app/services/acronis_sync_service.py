from datetime import datetime

from sqlalchemy.orm import Session

from app.models import AcronisOrgStat, AcronisSyncLog, Customer
from app.services.acronis.base import AcronisApiError, AcronisProvider
from app.services.name_matching import find_by_name, normalize_name, unique_normalized_index


def apply_acronis_stats_to_customer(customer: Customer, row: AcronisOrgStat) -> None:
    customer.acronis_tenant_name = row.tenant_name
    customer.backup_total_bytes = row.backup_total_bytes
    customer.backup_used_bytes = row.backup_used_bytes
    customer.backup_server_count = row.backup_server_count
    customer.backup_workstation_count = row.backup_workstation_count
    customer.backup_vm_count = row.backup_vm_count
    customer.backup_mailboxes_count = row.backup_mailboxes_count
    customer.dr_storage_total_bytes = row.dr_storage_total_bytes
    customer.dr_storage_used_bytes = row.dr_storage_used_bytes
    customer.acronis_synced_at = datetime.utcnow()


def acronis_sync_all(db: Session, provider: AcronisProvider) -> AcronisSyncLog:
    log = AcronisSyncLog(started_at=datetime.utcnow(), status="running")
    db.add(log)
    db.commit()
    db.refresh(log)

    try:
        stats = provider.get_tenant_stats()
        customers = db.query(Customer).all()
        customers_by_id = {c.id: c for c in customers}
        exact_by_name = {c.name.strip().lower(): c for c in customers}
        # Only trust the normalized match when it resolves to exactly one
        # customer - an ambiguous normalized match is worse than none.
        normalized_unique = unique_normalized_index(customers, lambda c: c.name)

        org_rows = {row.tenant_id: row for row in db.query(AcronisOrgStat).all()}

        matched = 0
        unmatched = 0
        for stat in stats:
            row = org_rows.get(stat.tenant_id)
            if row is None:
                row = AcronisOrgStat(tenant_id=stat.tenant_id, tenant_name=stat.tenant_name)
                db.add(row)
                db.flush()
                org_rows[stat.tenant_id] = row

            row.tenant_name = stat.tenant_name
            row.backup_total_bytes = stat.backup_total_bytes
            row.backup_used_bytes = stat.backup_used_bytes
            row.backup_server_count = stat.backup_server_count
            row.backup_workstation_count = stat.backup_workstation_count
            row.backup_vm_count = stat.backup_vm_count
            row.backup_mailboxes_count = stat.backup_mailboxes_count
            row.dr_storage_total_bytes = stat.dr_storage_total_bytes
            row.dr_storage_used_bytes = stat.dr_storage_used_bytes
            row.synced_at = datetime.utcnow()

            # A manually-mapped tenant (or one auto-matched on a previous
            # sync) keeps its customer_id; only try auto-matching when it's
            # unset, so a manual mapping is never silently overwritten.
            if row.customer_id is None:
                customer = exact_by_name.get(stat.tenant_name.strip().lower())
                if customer is None:
                    customer = normalized_unique.get(normalize_name(stat.tenant_name))
                if customer is not None:
                    row.customer_id = customer.id

            if row.customer_id is None:
                unmatched += 1
                continue

            customer = customers_by_id.get(row.customer_id)
            if customer is None:
                unmatched += 1
                continue

            apply_acronis_stats_to_customer(customer, row)
            matched += 1

        log.status = "success"
        log.tenants_matched = matched
        log.tenants_unmatched = unmatched
    except AcronisApiError as exc:
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


def create_standalone_customer_for_tenant(db: Session, tenant_id: str) -> AcronisOrgStat:
    """For an Acronis tenant with no StreamOne/ION counterpart: attach it to a
    customer with no ion_customer_id, so it can still be listed (with its
    backup stats) instead of sitting hidden in the unmapped-tenants list
    forever. If NinjaOne already created a standalone customer with a matching
    name (the same real customer, mapped from the other integration first),
    reuse that row instead of creating a duplicate."""
    row = db.query(AcronisOrgStat).filter(AcronisOrgStat.tenant_id == tenant_id).first()
    if row is None:
        raise ValueError(f"Unknown Acronis tenant: {tenant_id}")
    if row.customer_id is not None:
        raise ValueError(f"Acronis tenant already mapped: {tenant_id}")

    customer = find_by_name(db.query(Customer).all(), lambda c: c.name, row.tenant_name)
    if customer is None:
        customer = Customer(ion_customer_id=None, name=row.tenant_name)
        db.add(customer)
        db.flush()

    row.customer_id = customer.id
    apply_acronis_stats_to_customer(customer, row)

    db.commit()
    db.refresh(row)
    return row


def get_unmapped_tenants(db: Session) -> list[AcronisOrgStat]:
    return db.query(AcronisOrgStat).filter(AcronisOrgStat.customer_id.is_(None)).order_by(AcronisOrgStat.tenant_name).all()


def set_tenant_mapping(db: Session, tenant_id: str, customer_id: int) -> AcronisOrgStat:
    row = db.query(AcronisOrgStat).filter(AcronisOrgStat.tenant_id == tenant_id).first()
    if row is None:
        raise ValueError(f"Unknown Acronis tenant: {tenant_id}")

    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if customer is None:
        raise ValueError(f"Unknown customer id: {customer_id}")

    row.customer_id = customer_id
    apply_acronis_stats_to_customer(customer, row)

    db.commit()
    db.refresh(row)
    return row
