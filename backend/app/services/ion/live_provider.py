"""Real StreamOne ION API client.

Exact endpoint paths and response shapes are not yet confirmed against ION API
documentation (no credentials were available at build time). Everything about
where to call is env-configurable via `Settings` (see app/config.py); the only
thing that should need to change once real docs/credentials arrive is the
`_map_customer` / `_map_line` response-mapping methods below, and possibly the
token request shape in `_fetch_token` if ION deviates from standard OAuth2
client-credentials.
"""

import time
from datetime import datetime

import httpx

from app.config import Settings
from app.services.ion.base import IonApiError, IonCustomerDTO, IonLicenseLineDTO


class LiveIonProvider:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._token: str | None = None
        self._token_expires_at: float = 0.0

    def get_customers(self) -> list[IonCustomerDTO]:
        data = self._get(self._settings.ion_customers_path)
        items = data.get("items", data) if isinstance(data, dict) else data
        return [self._map_customer(item) for item in items]

    def get_license_lines(self) -> list[IonLicenseLineDTO]:
        data = self._get(self._settings.ion_subscriptions_path)
        items = data.get("items", data) if isinstance(data, dict) else data
        return [self._map_line(item) for item in items]

    # -- internals -----------------------------------------------------

    def _map_customer(self, raw: dict) -> IonCustomerDTO:
        return IonCustomerDTO(
            ion_customer_id=str(raw.get("id") or raw.get("customer_id")),
            name=raw.get("name") or raw.get("company_name", ""),
        )

    def _map_line(self, raw: dict) -> IonLicenseLineDTO:
        def _parse_date(value):
            if not value:
                return None
            return datetime.fromisoformat(str(value)[:10]).date()

        return IonLicenseLineDTO(
            ion_line_id=str(raw.get("id") or raw.get("subscription_id")),
            ion_customer_id=str(raw.get("customer_id")),
            sku=raw.get("sku") or raw.get("product_code", ""),
            product_name=raw.get("product_name") or raw.get("name", ""),
            vendor=raw.get("vendor") or raw.get("vendor_name", ""),
            quantity=int(raw.get("quantity", 0)),
            unit_cost=raw.get("unit_cost") or raw.get("cost", 0),
            term_start=_parse_date(raw.get("term_start") or raw.get("start_date")),
            term_end=_parse_date(raw.get("term_end") or raw.get("end_date")),
            billing_period=raw.get("billing_period") or raw.get("period"),
        )

    def _fetch_token(self) -> str:
        now = time.time()
        if self._token and now < self._token_expires_at - 60:
            return self._token

        payload = {
            "grant_type": "client_credentials",
            "client_id": self._settings.ion_client_id,
            "client_secret": self._settings.ion_client_secret,
        }
        if self._settings.ion_scope:
            payload["scope"] = self._settings.ion_scope

        try:
            with httpx.Client(timeout=30) as client:
                resp = client.post(self._settings.ion_token_url, data=payload)
                resp.raise_for_status()
                body = resp.json()
        except httpx.HTTPError as exc:
            raise IonApiError(f"Failed to obtain ION access token: {exc}") from exc

        token = body.get("access_token")
        if not token:
            raise IonApiError("ION token response did not contain an access_token")

        self._token = token
        self._token_expires_at = now + int(body.get("expires_in", 3600))
        return token

    def _get(self, path: str) -> dict | list:
        token = self._fetch_token()
        url = f"{self._settings.ion_base_url.rstrip('/')}{path}"
        headers = {"Authorization": f"Bearer {token}"}

        last_error: Exception | None = None
        for attempt in range(2):
            try:
                with httpx.Client(timeout=30) as client:
                    resp = client.get(url, headers=headers)
                if resp.status_code >= 500 and attempt == 0:
                    last_error = IonApiError(f"ION returned {resp.status_code} for {url}")
                    continue
                resp.raise_for_status()
                return resp.json()
            except httpx.HTTPError as exc:
                last_error = IonApiError(f"ION request to {url} failed: {exc}")

        raise last_error or IonApiError(f"ION request to {url} failed")
