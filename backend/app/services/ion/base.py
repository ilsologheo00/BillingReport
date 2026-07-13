from datetime import date
from decimal import Decimal
from typing import Optional, Protocol

from pydantic import BaseModel


class IonCustomerDTO(BaseModel):
    ion_customer_id: str
    name: str


class IonLicenseLineDTO(BaseModel):
    ion_line_id: str
    ion_customer_id: str
    sku: str
    product_name: str
    vendor: str
    quantity: int
    unit_cost: Decimal
    term_start: Optional[date] = None
    term_end: Optional[date] = None
    billing_period: Optional[str] = None


class IonApiError(Exception):
    """Raised when the StreamOne ION API call fails (auth, network, or unexpected response shape)."""


class IonProvider(Protocol):
    def get_customers(self) -> list[IonCustomerDTO]: ...

    def get_license_lines(self) -> list[IonLicenseLineDTO]: ...
