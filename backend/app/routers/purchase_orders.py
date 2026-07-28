from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import LicenseLine, PurchaseOrder, User
from app.schemas import PurchaseOrderUpsert
from app.security import get_current_user

router = APIRouter(prefix="/api/purchase-orders", tags=["purchase-orders"])


@router.put("")
def upsert_purchase_order(payload: PurchaseOrderUpsert, db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    line = db.query(LicenseLine).filter(LicenseLine.id == payload.license_line_id).first()
    if line is None:
        raise HTTPException(status_code=404, detail="License line not found")

    po = db.query(PurchaseOrder).filter(PurchaseOrder.license_line_id == payload.license_line_id).first()
    if po is None:
        po = PurchaseOrder(license_line_id=payload.license_line_id, po_name=payload.po_name)
        db.add(po)
    else:
        po.po_name = payload.po_name

    db.commit()
    return {"license_line_id": payload.license_line_id, "po_name": payload.po_name}
