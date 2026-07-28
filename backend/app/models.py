from datetime import datetime, date

from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    String,
    Numeric,
    DateTime,
    Date,
    ForeignKey,
    UniqueConstraint,
    Text,
)
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True)
    # Nullable: customers seen only in NinjaOne (no StreamOne/ION counterpart) are
    # kept as standalone rows with ion_customer_id=None - see create_standalone_customer_for_org.
    ion_customer_id = Column(String, unique=True, nullable=True, index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Nullable, treated as True when unset: ION splits each purchase batch of the
    # same product into its own subscription, which sync_service normally merges
    # into one license_line per (customer, sku). Set to False to keep this
    # customer's batches as separate lines instead - e.g. so each batch can carry
    # its own PurchaseOrder note.
    consolidate_license_lines = Column(Boolean, nullable=True)

    ninja_org_name = Column(String, nullable=True)
    device_count = Column(Integer, nullable=True)
    sentinelone_count = Column(Integer, nullable=True)
    ninja_synced_at = Column(DateTime, nullable=True)

    acronis_tenant_name = Column(String, nullable=True)
    backup_total_bytes = Column(Numeric(20, 0), nullable=True)
    backup_used_bytes = Column(Numeric(20, 0), nullable=True)
    backup_server_count = Column(Integer, nullable=True)
    backup_workstation_count = Column(Integer, nullable=True)
    backup_vm_count = Column(Integer, nullable=True)
    backup_mailboxes_count = Column(Integer, nullable=True)
    acronis_synced_at = Column(DateTime, nullable=True)

    license_lines = relationship("LicenseLine", back_populates="customer", cascade="all, delete-orphan")
    sell_prices = relationship("SellPrice", back_populates="customer", cascade="all, delete-orphan")


class LicenseLine(Base):
    __tablename__ = "license_lines"

    id = Column(Integer, primary_key=True)
    ion_line_id = Column(String, unique=True, nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    sku = Column(String, nullable=False, index=True)
    product_name = Column(String, nullable=False)
    vendor = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False, default=0)
    unit_cost = Column(Numeric(12, 4), nullable=False, default=0)
    term_start = Column(Date, nullable=True)
    term_end = Column(Date, nullable=True)
    billing_period = Column(String, nullable=True)
    last_synced_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    customer = relationship("Customer", back_populates="license_lines")
    purchase_order = relationship("PurchaseOrder", back_populates="license_line", uselist=False, cascade="all, delete-orphan")


class SellPrice(Base):
    __tablename__ = "sell_prices"
    __table_args__ = (UniqueConstraint("customer_id", "sku", name="uq_sell_price_customer_sku"),)

    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    sku = Column(String, nullable=False, index=True)
    unit_price = Column(Numeric(12, 4), nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer = relationship("Customer", back_populates="sell_prices")


class PurchaseOrder(Base):
    """Manually-entered PO reference per license line - StreamOne/ION does not
    expose a purchase-order field on subscriptions or orders via the public API
    (confirmed live), so this is tracked entirely within the app. Keyed by
    license_line_id (not customer+sku) so that a customer with consolidation
    disabled - see Customer.consolidate_license_lines - can carry a distinct PO
    per purchase batch of the same product, not just one per SKU."""

    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True)
    license_line_id = Column(Integer, ForeignKey("license_lines.id"), unique=True, nullable=False, index=True)
    po_name = Column(String, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    license_line = relationship("LicenseLine", back_populates="purchase_order")


class SyncLog(Base):
    __tablename__ = "sync_logs"

    id = Column(Integer, primary_key=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    status = Column(String, default="running")  # running | success | failed
    customers_synced = Column(Integer, default=0)
    lines_synced = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)


class NinjaSyncLog(Base):
    __tablename__ = "ninja_sync_logs"

    id = Column(Integer, primary_key=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    status = Column(String, default="running")  # running | success | failed
    orgs_matched = Column(Integer, default=0)
    orgs_unmatched = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)


class NinjaOrgStat(Base):
    """Latest per-organization stats from NinjaOne, plus the customer it's
    linked to (via automatic name matching or a manual mapping). Kept for
    every org NinjaOne returns, matched or not, so unmatched orgs can be
    shown for manual mapping without re-hitting the NinjaOne API."""

    __tablename__ = "ninja_org_stats"

    id = Column(Integer, primary_key=True)
    org_name = Column(String, unique=True, nullable=False, index=True)
    device_count = Column(Integer, default=0)
    sentinelone_count = Column(Integer, default=0)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    synced_at = Column(DateTime, default=datetime.utcnow)

    customer = relationship("Customer")


class AcronisSyncLog(Base):
    __tablename__ = "acronis_sync_logs"

    id = Column(Integer, primary_key=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    status = Column(String, default="running")  # running | success | failed
    tenants_matched = Column(Integer, default=0)
    tenants_unmatched = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)


class AcronisOrgStat(Base):
    """Latest per-tenant backup stats from Acronis, plus the customer it's
    linked to (via automatic name matching or a manual mapping). Kept for
    every customer-kind tenant Acronis returns, matched or not, so unmatched
    tenants can be shown for manual mapping without re-hitting the API."""

    __tablename__ = "acronis_org_stats"

    id = Column(Integer, primary_key=True)
    tenant_id = Column(String, unique=True, nullable=False, index=True)
    tenant_name = Column(String, nullable=False)
    backup_total_bytes = Column(Numeric(20, 0), default=0)
    backup_used_bytes = Column(Numeric(20, 0), default=0)
    backup_server_count = Column(Integer, default=0)
    backup_workstation_count = Column(Integer, default=0)
    backup_vm_count = Column(Integer, default=0)
    backup_mailboxes_count = Column(Integer, default=0)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)
    synced_at = Column(DateTime, default=datetime.utcnow)

    customer = relationship("Customer")
