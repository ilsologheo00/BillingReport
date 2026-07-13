from decimal import Decimal

from app.database import get_db
from app.main import app
from app.services.ion.factory import get_ion_provider
from app.services.ion.mock_provider import MockIonProvider


def _sync(client, auth_headers):
    app.dependency_overrides[get_ion_provider] = lambda: MockIonProvider()
    try:
        client.post("/api/sync", headers=auth_headers)
    finally:
        del app.dependency_overrides[get_ion_provider]


def test_report_summary_reflects_prices(client, auth_headers):
    _sync(client, auth_headers)

    summary_before = client.get("/api/report/summary", headers=auth_headers).json()
    assert summary_before["customer_count"] == 4
    assert summary_before["total_price"] is None

    customers = client.get("/api/customers", headers=auth_headers).json()
    acme = next(c for c in customers if c["name"] == "Acme Corp")
    client.put(
        "/api/prices",
        json={"customer_id": acme["id"], "sku": "MS365-E3", "unit_price": "25.00"},
        headers=auth_headers,
    )

    summary_after = client.get("/api/report/summary", headers=auth_headers).json()
    assert summary_after["total_price"] is not None
    assert Decimal(summary_after["total_price"]) == Decimal("25.00") * 120


def test_customer_detail_not_found(client, auth_headers):
    resp = client.get("/api/customers/9999", headers=auth_headers)
    assert resp.status_code == 404
