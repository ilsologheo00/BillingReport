from datetime import datetime

from sqlalchemy.orm import Session

from app.models import Customer, LicenseLine, SyncLog
from app.services.ion.base import IonApiError, IonProvider


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

        lines = [dto for dto in provider.get_license_lines() if dto.unit_cost != 0 and dto.quantity != 0]
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
