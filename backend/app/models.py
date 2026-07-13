from datetime import datetime, date

from sqlalchemy import (
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
    ion_customer_id = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

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


class SellPrice(Base):
    __tablename__ = "sell_prices"
    __table_args__ = (UniqueConstraint("customer_id", "sku", name="uq_sell_price_customer_sku"),)

    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    sku = Column(String, nullable=False, index=True)
    unit_price = Column(Numeric(12, 4), nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    customer = relationship("Customer", back_populates="sell_prices")


class SyncLog(Base):
    __tablename__ = "sync_logs"

    id = Column(Integer, primary_key=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)
    status = Column(String, default="running")  # running | success | failed
    customers_synced = Column(Integer, default=0)
    lines_synced = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
