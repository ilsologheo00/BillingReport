from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import NinjaSyncLog, User
from app.schemas import NinjaOrgMappingUpsert, NinjaOrgStatOut, NinjaSyncLogResponse
from app.security import get_current_user
from app.services.ninjaone.base import NinjaOneProvider
from app.services.ninjaone.factory import get_ninjaone_provider
from app.services.ninjaone_sync_service import get_unmapped_orgs, ninjaone_sync_all, set_org_mapping

router = APIRouter(prefix="/api/ninjaone", tags=["ninjaone"])


@router.post("/sync", response_model=NinjaSyncLogResponse)
def trigger_ninjaone_sync(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
    provider: NinjaOneProvider = Depends(get_ninjaone_provider),
):
    log = ninjaone_sync_all(db, provider)
    if log.status == "failed":
        raise HTTPException(status_code=502, detail=log.error_message or "NinjaOne sync failed")
    return log


@router.get("/sync/status", response_model=NinjaSyncLogResponse)
def ninjaone_sync_status(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    log = db.query(NinjaSyncLog).order_by(NinjaSyncLog.started_at.desc()).first()
    if log is None:
        raise HTTPException(status_code=404, detail="No NinjaOne sync has run yet")
    return log


@router.get("/unmapped", response_model=list[NinjaOrgStatOut])
def list_unmapped_orgs(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return get_unmapped_orgs(db)


@router.post("/mapping", response_model=NinjaOrgStatOut)
def upsert_org_mapping(
    payload: NinjaOrgMappingUpsert,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    try:
        return set_org_mapping(db, payload.org_name, payload.customer_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
