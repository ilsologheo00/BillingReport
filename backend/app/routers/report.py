from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Customer, SellPrice, User
from app.schemas import ReportSummaryOut
from app.security import get_current_user
from app.services.margin_service import aggregate_totals, line_margin, sell_price_lookup

router = APIRouter(prefix="/api/report", tags=["report"])


@router.get("/summary", response_model=ReportSummaryOut)
def report_summary(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    customers = db.query(Customer).all()
    prices = sell_price_lookup(db.query(SellPrice).all())

    all_margins = []
    for customer in customers:
        for line in customer.license_lines:
            all_margins.append(line_margin(line, prices.get((customer.id, line.sku))))

    totals = aggregate_totals(all_margins)
    return ReportSummaryOut(
        customer_count=len(customers),
        total_cost=totals.total_cost,
        total_price=totals.total_price,
        total_margin=totals.total_margin,
        margin_pct=totals.margin_pct,
    )
