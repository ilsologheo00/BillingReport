from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Customer, LicenseLine, SellPrice, User
from app.schemas import CustomerDetailOut, CustomerMergeRequest, CustomerSummaryOut, LicenseLineOut
from app.security import get_current_user
from app.services.customer_merge_service import merge_customers
from app.services.margin_service import aggregate_totals, is_customer_empty, line_margin, sell_price_lookup

router = APIRouter(prefix="/api/customers", tags=["customers"])


def _backup_available_bytes(customer: Customer):
    if customer.backup_total_bytes is None or customer.backup_used_bytes is None:
        return None
    return customer.backup_total_bytes - customer.backup_used_bytes


@router.get("", response_model=list[CustomerSummaryOut])
def list_customers(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    customers = db.query(Customer).order_by(Customer.name).all()
    prices = sell_price_lookup(db.query(SellPrice).all())

    results = []
    for customer in customers:
        margins = [line_margin(line, prices.get((customer.id, line.sku))) for line in customer.license_lines]
        totals = aggregate_totals(margins)
        if is_customer_empty(customer, totals.line_count):
            continue
        results.append(
            CustomerSummaryOut(
                id=customer.id,
                name=customer.name,
                ion_customer_id=customer.ion_customer_id,
                total_cost=totals.total_cost,
                total_price=totals.total_price,
                total_margin=totals.total_margin,
                margin_pct=totals.margin_pct,
                line_count=totals.line_count,
                device_count=customer.device_count,
                sentinelone_count=customer.sentinelone_count,
                backup_total_bytes=customer.backup_total_bytes,
                backup_used_bytes=customer.backup_used_bytes,
                backup_available_bytes=_backup_available_bytes(customer),
                backup_machines_count=customer.backup_machines_count,
                backup_mailboxes_count=customer.backup_mailboxes_count,
            )
        )
    return results


def _customer_detail(db: Session, customer_id: int) -> CustomerDetailOut:
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    prices = sell_price_lookup(db.query(SellPrice).filter(SellPrice.customer_id == customer_id).all())
    margins = [line_margin(line, prices.get((customer_id, line.sku))) for line in customer.license_lines]
    totals = aggregate_totals(margins)

    line_outs = [
        LicenseLineOut(
            id=lm.line.id,
            sku=lm.line.sku,
            product_name=lm.line.product_name,
            vendor=lm.line.vendor,
            quantity=lm.line.quantity,
            unit_cost=lm.line.unit_cost,
            unit_price=lm.unit_price,
            unit_margin=lm.unit_margin,
            total_cost=lm.total_cost,
            total_price=lm.total_price,
            total_margin=lm.total_margin,
            margin_pct=lm.margin_pct,
            term_start=lm.line.term_start,
            term_end=lm.line.term_end,
            billing_period=lm.line.billing_period,
            last_synced_at=lm.line.last_synced_at,
        )
        for lm in margins
    ]

    return CustomerDetailOut(
        id=customer.id,
        name=customer.name,
        ion_customer_id=customer.ion_customer_id,
        license_lines=line_outs,
        total_cost=totals.total_cost,
        total_price=totals.total_price,
        total_margin=totals.total_margin,
        margin_pct=totals.margin_pct,
        device_count=customer.device_count,
        sentinelone_count=customer.sentinelone_count,
        backup_total_bytes=customer.backup_total_bytes,
        backup_used_bytes=customer.backup_used_bytes,
        backup_available_bytes=_backup_available_bytes(customer),
        backup_machines_count=customer.backup_machines_count,
        backup_mailboxes_count=customer.backup_mailboxes_count,
    )


@router.get("/{customer_id}", response_model=CustomerDetailOut)
def get_customer(customer_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return _customer_detail(db, customer_id)


@router.post("/merge", response_model=CustomerDetailOut)
def merge_customer(
    payload: CustomerMergeRequest,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    try:
        merge_customers(db, payload.keep_customer_id, payload.merge_customer_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _customer_detail(db, payload.keep_customer_id)
