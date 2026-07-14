from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class SyncLogResponse(BaseModel):
    id: int
    started_at: datetime
    finished_at: Optional[datetime]
    status: str
    customers_synced: int
    lines_synced: int
    error_message: Optional[str]

    class Config:
        from_attributes = True


class NinjaSyncLogResponse(BaseModel):
    id: int
    started_at: datetime
    finished_at: Optional[datetime]
    status: str
    orgs_matched: int
    orgs_unmatched: int
    error_message: Optional[str]

    class Config:
        from_attributes = True


class LicenseLineOut(BaseModel):
    id: int
    sku: str
    product_name: str
    vendor: str
    quantity: int
    unit_cost: Decimal
    unit_price: Optional[Decimal] = None
    unit_margin: Optional[Decimal] = None
    total_cost: Decimal
    total_price: Optional[Decimal] = None
    total_margin: Optional[Decimal] = None
    margin_pct: Optional[Decimal] = None
    term_start: Optional[date] = None
    term_end: Optional[date] = None
    billing_period: Optional[str] = None
    last_synced_at: datetime


class CustomerSummaryOut(BaseModel):
    id: int
    name: str
    ion_customer_id: str
    total_cost: Decimal
    total_price: Optional[Decimal] = None
    total_margin: Optional[Decimal] = None
    margin_pct: Optional[Decimal] = None
    line_count: int
    device_count: Optional[int] = None
    sentinelone_count: Optional[int] = None


class CustomerDetailOut(BaseModel):
    id: int
    name: str
    ion_customer_id: str
    license_lines: list[LicenseLineOut]
    total_cost: Decimal
    total_price: Optional[Decimal] = None
    total_margin: Optional[Decimal] = None
    margin_pct: Optional[Decimal] = None
    device_count: Optional[int] = None
    sentinelone_count: Optional[int] = None


class ReportSummaryOut(BaseModel):
    customer_count: int
    total_cost: Decimal
    total_price: Optional[Decimal] = None
    total_margin: Optional[Decimal] = None
    margin_pct: Optional[Decimal] = None


class SellPriceUpsert(BaseModel):
    customer_id: int
    sku: str
    unit_price: Decimal


class NinjaOrgStatOut(BaseModel):
    org_name: str
    device_count: int
    sentinelone_count: int
    synced_at: datetime

    class Config:
        from_attributes = True


class NinjaOrgMappingUpsert(BaseModel):
    org_name: str
    customer_id: int
