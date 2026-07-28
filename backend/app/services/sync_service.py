from collections import defaultdict
from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import Customer, LicenseLine, SyncLog
from app.services.ion.base import IonApiError, IonLicenseLineDTO, IonProvider


def _consolidate_lines(lines: list[IonLicenseLineDTO], no_consolidate_ion_ids: set[str]) -> list[IonLicenseLineDTO]:
    """ION invoices each purchase batch of the same product as its own subscription
    (e.g. 10 seats bought in 2022, 2 more in 2024), so a customer can have several
    lines for the same SKU. Merge those into one line per (customer, sku), summing
    quantities and computing a quantity-weighted average unit cost so total_cost
    stays accurate - unless the customer has consolidation disabled (see
    Customer.consolidate_license_lines), in which case its lines pass through
    unmerged so each purchase batch can carry its own PurchaseOrder note."""
    passthrough = [dto for dto in lines if dto.ion_customer_id in no_consolidate_ion_ids]
    to_consolidate = [dto for dto in lines if dto.ion_customer_id not in no_consolidate_ion_ids]

    groups: dict[tuple[str, str], list[IonLicenseLineDTO]] = defaultdict(list)
    for dto in to_consolidate:
        groups[(dto.ion_customer_id, dto.sku)].append(dto)

    consolidated = list(passthrough)
    for (ion_customer_id, sku), group in groups.items():
        total_quantity = sum(dto.quantity for dto in group)
        total_cost = sum(dto.unit_cost * dto.quantity for dto in group)
        weighted_unit_cost = total_cost / total_quantity if total_quantity else Decimal("0")
        term_starts = [dto.term_start for dto in group if dto.term_start is not None]
        term_ends = [dto.term_end for dto in group if dto.term_end is not None]
        first = group[0]

        consolidated.append(
            IonLicenseLineDTO(
                ion_line_id=f"consolidated:{ion_customer_id}:{sku}",
                ion_customer_id=ion_customer_id,
                sku=sku,
                product_name=first.product_name,
                vendor=first.vendor,
                quantity=total_quantity,
                unit_cost=weighted_unit_cost,
                term_start=min(term_starts) if term_starts else None,
                term_end=max(term_ends) if term_ends else None,
                billing_period=first.billing_period,
            )
        )
    return consolidated


def sync_all(db: Session, provider: IonProvider) -> SyncLog:
    log = SyncLog(started_at=datetime.utcnow(), status="running")
    db.add(log)
    db.commit()
    db.refresh(log)

    try:
        customers = provider.get_customers()
        customer_id_by_ion_id = {}
        for dto in customers:
            customer = db.query(Customer).filter(Customer.ion_customer_id == dto.ion_customer_id).first()
            if customer is None:
                customer = Customer(ion_customer_id=dto.ion_customer_id, name=dto.name)
                db.add(customer)
            else:
                customer.name = dto.name
            db.flush()
            customer_id_by_ion_id[dto.ion_customer_id] = customer.id

        no_consolidate_ion_ids = {
            ion_id
            for (ion_id,) in db.query(Customer.ion_customer_id).filter(Customer.consolidate_license_lines.is_(False))
        }

        raw_lines = [
            dto for dto in provider.get_license_lines()
            if dto.unit_cost != 0 and dto.quantity != 0 and dto.billing_period != "one_time"
        ]
        lines = _consolidate_lines(raw_lines, no_consolidate_ion_ids)
        seen_ion_line_ids = set()
        for dto in lines:
            customer_id = customer_id_by_ion_id.get(dto.ion_customer_id)
            if customer_id is None:
                # License line references a customer ION didn't include in get_customers();
                # skip rather than fail the whole sync.
                continue

            line = db.query(LicenseLine).filter(LicenseLine.ion_line_id == dto.ion_line_id).first()
            if line is None:
                line = LicenseLine(ion_line_id=dto.ion_line_id)
                db.add(line)

            line.customer_id = customer_id
            line.sku = dto.sku
            line.product_name = dto.product_name
            line.vendor = dto.vendor
            line.quantity = dto.quantity
            line.unit_cost = dto.unit_cost
            line.term_start = dto.term_start
            line.term_end = dto.term_end
            line.billing_period = dto.billing_period
            line.last_synced_at = datetime.utcnow()
            seen_ion_line_ids.add(dto.ion_line_id)

        db.flush()

        stale_lines = db.query(LicenseLine).filter(~LicenseLine.ion_line_id.in_(seen_ion_line_ids)).all() \
            if seen_ion_line_ids else db.query(LicenseLine).all()
        for stale in stale_lines:
            db.delete(stale)

        log.status = "success"
        log.customers_synced = len(customers)
        log.lines_synced = len(lines)
    except IonApiError as exc:
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
