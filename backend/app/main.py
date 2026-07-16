from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.routers import acronis_sync, auth, customers, ninjaone_sync, prices, report, sync
from app.seed import seed_admin_user

app = FastAPI(title="BillingReport API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(sync.router)
app.include_router(ninjaone_sync.router)
app.include_router(acronis_sync.router)
app.include_router(customers.router)
app.include_router(prices.router)
app.include_router(report.router)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_admin_user(db)
    finally:
        db.close()


@app.get("/api/health")
def health():
    return {"status": "ok", "ion_mode": settings.ion_mode}
