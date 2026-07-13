from decimal import Decimal

from app.database import get_db
from app.main import app
from app.services.ion.factory import get_ion_provider
from app.services.ion.mock_provider import MockIonProvider


def test_sync_with_mock_provider(client, auth_headers, db_session):
    app.dependency_overrides[get_ion_provider] = lambda: MockIonProvider()
    try:
        resp = client.post("/api/sync", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert body["customers_synced"] == 4
        assert body["lines_synced"] == 8
    finally:
        del app.dependency_overrides[get_ion_provider]

    customers_resp = client.get("/api/customers", headers=auth_headers)
    assert customers_resp.status_code == 200
    names = {c["name"] for c in customers_resp.json()}
    assert "Acme Corp" in names


def test_resync_preserves_sell_price(client, auth_headers):
    app.dependency_overrides[get_ion_provider] = lambda: MockIonProvider()
    try:
        client.post("/api/sync", headers=auth_headers)

        customers = client.get("/api/customers", headers=auth_headers).json()
        acme = next(c for c in customers if c["name"] == "Acme Corp")

        price_resp = client.put(
            "/api/prices",
            json={"customer_id": acme["id"], "sku": "MS365-E3", "unit_price": "25.00"},
            headers=auth_headers,
        )
        assert price_resp.status_code == 200

        # Re-run sync — price should survive since sync never touches SellPrice.
        client.post("/api/sync", headers=auth_headers)

        detail = client.get(f"/api/customers/{acme['id']}", headers=auth_headers).json()
        line = next(l for l in detail["license_lines"] if l["sku"] == "MS365-E3")
        assert Decimal(line["unit_price"]) == Decimal("25.00")
        assert line["unit_margin"] is not None
    finally:
        del app.dependency_overrides[get_ion_provider]
