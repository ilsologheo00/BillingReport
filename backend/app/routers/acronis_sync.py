from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AcronisSyncLog, User
from app.schemas import (
    AcronisOrgStatOut,
    AcronisSyncLogResponse,
    AcronisTenantMappingUpsert,
    AcronisTenantStandaloneCreate,
)
from app.security import get_current_user
from app.services.acronis.base import AcronisProvider
from app.services.acronis.factory import get_acronis_provider
from app.services.acronis_sync_service import (
    acronis_sync_all,
    create_standalone_customer_for_tenant,
    get_unmapped_tenants,
    set_tenant_mapping,
)

router = APIRouter(prefix="/api/acronis", tags=["acronis"])


@router.post("/sync", response_model=AcronisSyncLogResponse)
def trigger_acronis_sync(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
    provider: AcronisProvider = Depends(get_acronis_provider),
):
    log = acronis_sync_all(db, provider)
    if log.status == "failed":
        raise HTTPException(status_code=502, detail=log.error_message or "Acronis sync failed")
    return log


@router.get("/sync/status", response_model=AcronisSyncLogResponse)
def acronis_sync_status(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    log = db.query(AcronisSyncLog).order_by(AcronisSyncLog.started_at.desc()).first()
    if log is None:
        raise HTTPException(status_code=404, detail="No Acronis sync has run yet")
    return log


@router.get("/unmapped", response_model=list[AcronisOrgStatOut])
def list_unmapped_tenants(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    return get_unmapped_tenants(db)


@router.post("/mapping", response_model=AcronisOrgStatOut)
def upsert_tenant_mapping(
    payload: AcronisTenantMappingUpsert,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    try:
        return set_tenant_mapping(db, payload.tenant_id, payload.customer_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/mapping/standalone", response_model=AcronisOrgStatOut)
def create_standalone_customer(
    payload: AcronisTenantStandaloneCreate,
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    try:
        return create_standalone_customer_for_tenant(db, payload.tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
