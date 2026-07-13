from datetime import date

from app.services.ion.base import IonCustomerDTO, IonLicenseLineDTO

_CUSTOMERS = [
    IonCustomerDTO(ion_customer_id="mock-cust-001", name="Acme Corp"),
    IonCustomerDTO(ion_customer_id="mock-cust-002", name="Northwind Traders"),
    IonCustomerDTO(ion_customer_id="mock-cust-003", name="Contoso Ltd"),
    IonCustomerDTO(ion_customer_id="mock-cust-004", name="Globex Inc"),
]

_LICENSE_LINES = [
    IonLicenseLineDTO(
        ion_line_id="mock-line-001", ion_customer_id="mock-cust-001",
        sku="MS365-E3", product_name="Microsoft 365 E3", vendor="Microsoft",
        quantity=120, unit_cost="18.50",
        term_start=date(2026, 1, 1), term_end=date(2026, 12, 31), billing_period="annual",
    ),
    IonLicenseLineDTO(
        ion_line_id="mock-line-002", ion_customer_id="mock-cust-001",
        sku="ADOBE-CC", product_name="Adobe Creative Cloud", vendor="Adobe",
        quantity=15, unit_cost="42.00",
        term_start=date(2026, 3, 1), term_end=date(2027, 2, 28), billing_period="annual",
    ),
    IonLicenseLineDTO(
        ion_line_id="mock-line-003", ion_customer_id="mock-cust-002",
        sku="ZOOM-BIZ", product_name="Zoom Business", vendor="Zoom",
        quantity=40, unit_cost="14.25",
        term_start=date(2026, 5, 1), term_end=date(2027, 4, 30), billing_period="annual",
    ),
    IonLicenseLineDTO(
        ion_line_id="mock-line-004", ion_customer_id="mock-cust-002",
        sku="DUO-SEC", product_name="Duo Security", vendor="Cisco",
        quantity=40, unit_cost="3.00",
        term_start=date(2026, 5, 1), term_end=date(2027, 4, 30), billing_period="monthly",
    ),
    IonLicenseLineDTO(
        ion_line_id="mock-line-005", ion_customer_id="mock-cust-003",
        sku="MS365-E3", product_name="Microsoft 365 E3", vendor="Microsoft",
        quantity=200, unit_cost="18.50",
        term_start=date(2025, 11, 1), term_end=date(2026, 10, 31), billing_period="annual",
    ),
    IonLicenseLineDTO(
        ion_line_id="mock-line-006", ion_customer_id="mock-cust-003",
        sku="ADOBE-CC", product_name="Adobe Creative Cloud", vendor="Adobe",
        quantity=8, unit_cost="42.00",
        term_start=date(2026, 2, 1), term_end=date(2027, 1, 31), billing_period="annual",
    ),
    IonLicenseLineDTO(
        ion_line_id="mock-line-007", ion_customer_id="mock-cust-003",
        sku="ZOOM-BIZ", product_name="Zoom Business", vendor="Zoom",
        quantity=25, unit_cost="14.25",
        term_start=date(2026, 6, 1), term_end=date(2027, 5, 31), billing_period="monthly",
    ),
    IonLicenseLineDTO(
        ion_line_id="mock-line-008", ion_customer_id="mock-cust-004",
        sku="DUO-SEC", product_name="Duo Security", vendor="Cisco",
        quantity=60, unit_cost="3.00",
        term_start=date(2026, 4, 1), term_end=date(2027, 3, 31), billing_period="monthly",
    ),
]


class MockIonProvider:
    """Deterministic fake ION data so the app is fully demoable without real API credentials."""

    def get_customers(self) -> list[IonCustomerDTO]:
        return list(_CUSTOMERS)

    def get_license_lines(self) -> list[IonLicenseLineDTO]:
        return list(_LICENSE_LINES)
