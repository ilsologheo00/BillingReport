from datetime import datetime

from sqlalchemy.orm import Session

from app.models import AcronisOrgStat, Customer, LicenseLine, NinjaOrgStat, SellPrice
from app.services.acronis_sync_service import apply_acronis_stats_to_customer


def merge_customers(db: Session, keep_customer_id: int, merge_customer_id: int) -> Customer:
    """Merge `merge_customer_id` into `keep_customer_id`: move its NinjaOne/Acronis
    links, license lines and sell prices onto the surviving customer, then delete
    the now-empty duplicate. Used when the same real customer ended up as two
    rows (e.g. a NinjaOne org and an Acronis tenant with different display names
    that name-matching couldn't tell apart, like "Buratti" vs "Buratti Ilde")."""
    if keep_customer_id == merge_customer_id:
        raise ValueError("Cannot merge a customer into itself")

    keep = db.query(Customer).filter(Customer.id == keep_customer_id).first()
    if keep is None:
        raise ValueError(f"Unknown customer id: {keep_customer_id}")
    merge = db.query(Customer).filter(Customer.id == merge_customer_id).first()
    if merge is None:
        raise ValueError(f"Unknown customer id: {merge_customer_id}")

    db.query(LicenseLine).filter(LicenseLine.customer_id == merge_customer_id).update(
        {"customer_id": keep_customer_id}
    )

    # SellPrice has a unique (customer_id, sku) constraint - if the surviving
    # customer already has a price for a SKU also priced on the duplicate, keep
    # the surviving customer's price and drop the duplicate's rather than erroring.
    keep_skus = {
        sku for (sku,) in db.query(SellPrice.sku).filter(SellPrice.customer_id == keep_customer_id)
    }
    for price in db.query(SellPrice).filter(SellPrice.customer_id == merge_customer_id).all():
        if price.sku in keep_skus:
            db.delete(price)
        else:
            price.customer_id = keep_customer_id
    db.flush()

    db.query(NinjaOrgStat).filter(NinjaOrgStat.customer_id == merge_customer_id).update(
        {"customer_id": keep_customer_id}
    )
    db.query(AcronisOrgStat).filter(AcronisOrgStat.customer_id == merge_customer_id).update(
        {"customer_id": keep_customer_id}
    )
    db.flush()

    # Recompute the surviving customer's NinjaOne/Acronis-derived fields from
    # whichever stat rows now point at it (its own, plus any just moved over).
    for stat in db.query(NinjaOrgStat).filter(NinjaOrgStat.customer_id == keep_customer_id).all():
        keep.ninja_org_name = stat.org_name
        keep.device_count = stat.device_count
        keep.sentinelone_count = stat.sentinelone_count
        keep.ninja_synced_at = datetime.utcnow()
    for stat in db.query(AcronisOrgStat).filter(AcronisOrgStat.customer_id == keep_customer_id).all():
        apply_acronis_stats_to_customer(keep, stat)

    db.delete(merge)
    db.commit()
    db.refresh(keep)
    return keep
