from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Customer, SellPrice, User
from app.schemas import SellPriceUpsert
from app.security import get_current_user

router = APIRouter(prefix="/api/prices", tags=["prices"])


@router.put("")
def upsert_price(payload: SellPriceUpsert, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    customer = db.query(Customer).filter(Customer.id == payload.customer_id).first()
    if customer is None:
        raise HTTPException(status_code=404, detail="Customer not found")

    price = (
        db.query(SellPrice)
        .filter(SellPrice.customer_id == payload.customer_id, SellPrice.sku == payload.sku)
        .first()
    )
    if price is None:
        price = SellPrice(customer_id=payload.customer_id, sku=payload.sku, unit_price=payload.unit_price)
        db.add(price)
    else:
        price.unit_price = payload.unit_price

    db.commit()
    return {"customer_id": payload.customer_id, "sku": payload.sku, "unit_price": str(payload.unit_price)}
