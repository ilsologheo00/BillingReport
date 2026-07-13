from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import SyncLog, User
from app.schemas import SyncLogResponse
from app.security import get_current_user
from app.services.ion.base import IonProvider
from app.services.ion.factory import get_ion_provider
from app.services.sync_service import sync_all

router = APIRouter(prefix="/api/sync", tags=["sync"])


@router.post("", response_model=SyncLogResponse)
def trigger_sync(
    db: Session = Depends(get_db),
    _user: User = Depends(get_current_user),
    provider: IonProvider = Depends(get_ion_provider),
):
    log = sync_all(db, provider)
    if log.status == "failed":
        raise HTTPException(status_code=502, detail=log.error_message or "ION sync failed")
    return log


@router.get("/status", response_model=SyncLogResponse)
def sync_status(db: Session = Depends(get_db), _user: User = Depends(get_current_user)):
    log = db.query(SyncLog).order_by(SyncLog.started_at.desc()).first()
    if log is None:
        raise HTTPException(status_code=404, detail="No sync has run yet")
    return log
