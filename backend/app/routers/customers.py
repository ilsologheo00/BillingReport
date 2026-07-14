from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Customer, LicenseLine, SellPrice, User
from app.schemas import CustomerDetailOut, CustomerSummaryOut, LicenseLineOut
from app.security import get_current_user
from app.services.margin_service import aggregate_totals, line_margin, sell_price_lookup

router = APIRouter(prefix="/api/customers", tags=["customers"])


@router.get("", response_model=list[CustomerSummaryOut])
def list_customers(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    customers = db.query(Customer).order_by(Customer.name).all()
    prices = sell_price_lookup(db.query(SellPrice).all())

    results = []
    for customer in customers:
        margins = [line_margin(line, prices.get((customer.id, line.sku))) for line in customer.license_lines]
        totals = aggregate_totals(margins)
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
            )
        )
    return results


@router.get("/{customer_id}", response_model=CustomerDetailOut)
def get_customer(customer_id: int, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
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
    )
