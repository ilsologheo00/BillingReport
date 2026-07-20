"""Real StreamOne ION (TD SYNNEX) v3 API client.

Auth flow per the official "STREAMONE ION V3 API's Consumption guide": there is
no client_id/client_secret client_credentials grant. Instead an initial
refresh_token is issued from the ION admin portal, and is exchanged for an
access_token (valid 7200s) plus a *new* refresh_token (single-use, valid 32
days) via POST {ion_token_url} with grant_type=refresh_token. The rotated
refresh_token must be persisted, or the next sync will fail because the old
one was already consumed.
"""

import json
import time
from datetime import datetime
from pathlib import Path

import httpx

from app.config import Settings
from app.services.ion.base import IonApiError, IonCustomerDTO, IonLicenseLineDTO


class LiveIonProvider:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._token: str | None = None
        self._token_expires_at: float = 0.0

    def get_customers(self) -> list[IonCustomerDTO]:
        path = self._settings.ion_customers_path.format(account_id=self._settings.ion_account_id)
        results = []
        page_token = None
        while True:
            params = {"page_size": 200}
            if page_token:
                params["page_token"] = page_token
            data = self._get(path, params)
            results.extend(data.get("customers", []))
            page_token = data.get("next_page_token") or data.get("nextPageToken")
            if not page_token:
                break
        return [self._map_customer(item) for item in results]

    def get_license_lines(self) -> list[IonLicenseLineDTO]:
        path = self._settings.ion_subscriptions_path.format(account_id=self._settings.ion_account_id)
        results = []
        offset = 0
        limit = 100
        while True:
            params = {"pagination.limit": limit, "pagination.offset": offset}
            data = self._get(path, params)
            batch = data.get("items", [])
            results.extend(batch)
            total = data.get("paginationResponse", {}).get("totalSize", len(results))
            offset += len(batch)
            if not batch or offset >= total:
                break
        # Cancelled/superseded subscriptions ("deleted") can still carry a residual
        # `cost` value with no customerCost/billingData - only "active" ones are
        # real, current licenses.
        active = [item for item in results if item.get("subscriptionStatus") == "active"]
        return [self._map_line(item) for item in active]

    # -- internals -----------------------------------------------------

    def _map_customer(self, raw: dict) -> IonCustomerDTO:
        # customerId referenced by subscriptions is the trailing segment of `name`
        # (e.g. "accounts/24549/customers/446444"), not the `uid` field.
        name = raw.get("name", "")
        customer_id = name.rsplit("/", 1)[-1] if name else str(raw.get("uid", ""))
        return IonCustomerDTO(
            ion_customer_id=customer_id,
            name=raw.get("customerOrganization") or raw.get("customerName", ""),
        )

    def _map_line(self, raw: dict) -> IonLicenseLineDTO:
        def _parse_date(value):
            if not value:
                return None
            return datetime.fromisoformat(str(value).replace("Z", "+00:00")).date()

        billing = (raw.get("billingData") or [{}])[0]
        quantity = int(raw.get("subscriptionTotalLicenses") or 0)

        # `cost` (reseller cost) is already per-license - unlike `sellerCost` in
        # billingData, which is the total across all licenses on the subscription
        # and must be divided by quantity to get a per-license figure.
        per_license_cost = raw.get("cost")
        if per_license_cost in (None, 0):
            total_cost = billing.get("sellerCost", 0)
            unit_cost = (total_cost or 0) / quantity if quantity else (total_cost or 0)
        else:
            unit_cost = per_license_cost

        return IonLicenseLineDTO(
            ion_line_id=str(raw.get("id") or raw.get("subscriptionId")),
            ion_customer_id=str(raw.get("customerId")),
            sku=raw.get("ccpSkuId") or raw.get("subscriptionSkuId", ""),
            product_name=raw.get("subscriptionName", ""),
            vendor=str(raw.get("cloudProviderId", "")),
            quantity=quantity,
            unit_cost=unit_cost,
            term_start=_parse_date(raw.get("subscriptionStartDate")),
            term_end=_parse_date(raw.get("subscriptionEndDate")),
            billing_period=raw.get("subscriptionBillingCycle"),
        )

    # -- token handling --------------------------------------------------

    def _cache_path(self) -> Path:
        path = Path(self._settings.ion_token_cache_path)
        if not path.is_absolute():
            path = Path(__file__).resolve().parents[3] / path
        return path

    def _load_cache(self) -> dict:
        path = self._cache_path()
        if path.exists():
            try:
                return json.loads(path.read_text())
            except (json.JSONDecodeError, OSError):
                pass
        return {}

    def _save_cache(self, refresh_token: str, access_token: str, expires_at: float) -> None:
        path = self._cache_path()
        path.write_text(json.dumps({
            "refresh_token": refresh_token,
            "access_token": access_token,
            "expires_at": expires_at,
        }))

    def _fetch_token(self) -> str:
        now = time.time()
        if self._token and now < self._token_expires_at - 60:
            return self._token

        cache = self._load_cache()
        if cache.get("access_token") and now < cache.get("expires_at", 0) - 60:
            self._token = cache["access_token"]
            self._token_expires_at = cache["expires_at"]
            return self._token

        refresh_token = cache.get("refresh_token") or self._settings.ion_refresh_token
        if not refresh_token:
            raise IonApiError("No ION refresh_token available (set ION_REFRESH_TOKEN or seed the token cache)")

        payload = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }

        try:
            with httpx.Client(timeout=30) as client:
                resp = client.post(self._settings.ion_token_url, data=payload)
                resp.raise_for_status()
                body = resp.json()
        except httpx.HTTPError as exc:
            raise IonApiError(f"Failed to obtain ION access token: {exc}") from exc

        token = body.get("access_token")
        new_refresh_token = body.get("refresh_token")
        if not token or not new_refresh_token:
            raise IonApiError("ION token response missing access_token or refresh_token")

        expires_at = now + int(body.get("expires_in", 7200))
        self._save_cache(new_refresh_token, token, expires_at)

        self._token = token
        self._token_expires_at = expires_at
        return token

    def _get(self, path: str, params: dict | None = None) -> dict | list:
        token = self._fetch_token()
        url = f"{self._settings.ion_base_url.rstrip('/')}{path}"
        headers = {"Authorization": f"Bearer {token}"}

        last_error: Exception | None = None
        for attempt in range(2):
            try:
                with httpx.Client(timeout=30, follow_redirects=True) as client:
                    resp = client.get(url, headers=headers, params=params)
                if resp.status_code >= 500 and attempt == 0:
                    last_error = IonApiError(f"ION returned {resp.status_code} for {url}")
                    continue
                resp.raise_for_status()
                return resp.json()
            except httpx.HTTPError as exc:
                last_error = IonApiError(f"ION request to {url} failed: {exc}")

        raise last_error or IonApiError(f"ION request to {url} failed")
