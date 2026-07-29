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
    po_name: Optional[str] = None


class CustomerSummaryOut(BaseModel):
    id: int
    name: str
    ion_customer_id: Optional[str] = None
    total_cost: Decimal
    total_price: Optional[Decimal] = None
    total_margin: Optional[Decimal] = None
    margin_pct: Optional[Decimal] = None
    line_count: int
    device_count: Optional[int] = None
    sentinelone_count: Optional[int] = None
    backup_total_bytes: Optional[Decimal] = None
    backup_used_bytes: Optional[Decimal] = None
    backup_available_bytes: Optional[Decimal] = None
    backup_server_count: Optional[int] = None
    backup_workstation_count: Optional[int] = None
    backup_vm_count: Optional[int] = None
    backup_mailboxes_count: Optional[int] = None


class CustomerDetailOut(BaseModel):
    id: int
    name: str
    ion_customer_id: Optional[str] = None
    license_lines: list[LicenseLineOut]
    total_cost: Decimal
    total_price: Optional[Decimal] = None
    total_margin: Optional[Decimal] = None
    margin_pct: Optional[Decimal] = None
    device_count: Optional[int] = None
    sentinelone_count: Optional[int] = None
    backup_total_bytes: Optional[Decimal] = None
    backup_used_bytes: Optional[Decimal] = None
    backup_available_bytes: Optional[Decimal] = None
    backup_server_count: Optional[int] = None
    backup_workstation_count: Optional[int] = None
    backup_vm_count: Optional[int] = None
    backup_mailboxes_count: Optional[int] = None
    dr_storage_total_bytes: Optional[Decimal] = None
    dr_storage_used_bytes: Optional[Decimal] = None
    dr_storage_available_bytes: Optional[Decimal] = None
    consolidate_license_lines: bool = True


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


class PurchaseOrderUpsert(BaseModel):
    license_line_id: int
    po_name: str


class CustomerMergeRequest(BaseModel):
    keep_customer_id: int
    merge_customer_id: int


class CustomerConsolidationUpdate(BaseModel):
    consolidate: bool


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


class NinjaOrgStandaloneCreate(BaseModel):
    org_name: str


class AcronisSyncLogResponse(BaseModel):
    id: int
    started_at: datetime
    finished_at: Optional[datetime]
    status: str
    tenants_matched: int
    tenants_unmatched: int
    error_message: Optional[str]

    class Config:
        from_attributes = True


class AcronisOrgStatOut(BaseModel):
    tenant_id: str
    tenant_name: str
    backup_total_bytes: Optional[Decimal] = None
    backup_used_bytes: Decimal
    backup_server_count: int
    backup_workstation_count: int
    backup_vm_count: int
    backup_mailboxes_count: int
    synced_at: datetime

    class Config:
        from_attributes = True


class AcronisTenantMappingUpsert(BaseModel):
    tenant_id: str
    customer_id: int


class AcronisTenantStandaloneCreate(BaseModel):
    tenant_id: str
