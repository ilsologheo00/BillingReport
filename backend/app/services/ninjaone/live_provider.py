"""Real NinjaOne API client.

Auth is OAuth2 client_credentials against {ninjaone_token_url}. Organizations
come from GET /v2/organizations and devices from GET /v2/devices (paginated
via an "after" cursor on device id) - both verified against a live tenant.

The bulk GET /v2/queries/software endpoint currently 500s on this tenant
(server-side "DataIntegrityViolationException", reproduced with and without
query params) - but GET /v2/queries/antivirus-status works fine and is used
to detect SentinelOne coverage instead of the old per-device software-list
approach. It returns one row per (deviceId, installed AV product) - a device
can have more than one row if it has several AV products installed (e.g.
SentinelOne alongside a still-present Microsoft Defender Antivirus row) - with
`productState` ("ON"/"OFF") telling active from merely-installed-but-disabled.
Paginated via a `cursor` object ({name, offset, count}), not a plain cursor
string like the other endpoints - `cursor.name` is passed back as the
`cursor` query param for the next page, until offset reaches count.
"""

import time

import httpx

from app.config import Settings
from app.services.ninjaone.base import NinjaApiError, NinjaOrgStatsDTO


class LiveNinjaOneProvider:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._token: str | None = None
        self._token_expires_at: float = 0.0

    def get_org_stats(self) -> list[NinjaOrgStatsDTO]:
        orgs = self._get_all_pages("/v2/organizations")
        org_name_by_id = {str(org.get("id")): org.get("name", "") for org in orgs}

        devices = self._get_all_pages("/v2/devices", after_field="id")
        org_id_by_device_id = {str(d.get("id")): str(d.get("organizationId")) for d in devices}
        device_count_by_org: dict[str, int] = {}
        for org_id in org_id_by_device_id.values():
            device_count_by_org[org_id] = device_count_by_org.get(org_id, 0) + 1

        match = self._settings.ninjaone_sentinelone_match.lower()
        protected_device_ids: set[str] = set()
        for item in self._get_antivirus_status():
            if item.get("productState") != "ON":
                continue
            if match not in str(item.get("productName", "")).lower():
                continue
            device_id = item.get("deviceId")
            if device_id is not None:
                protected_device_ids.add(str(device_id))

        sentinelone_count_by_org: dict[str, int] = {}
        for device_id in protected_device_ids:
            org_id = org_id_by_device_id.get(device_id)
            if org_id is None:
                continue
            sentinelone_count_by_org[org_id] = sentinelone_count_by_org.get(org_id, 0) + 1

        results = []
        for org_id, org_name in org_name_by_id.items():
            results.append(NinjaOrgStatsDTO(
                org_name=org_name,
                device_count=device_count_by_org.get(org_id, 0),
                sentinelone_count=sentinelone_count_by_org.get(org_id, 0),
            ))
        return results

    # -- internals -----------------------------------------------------

    def _get_antivirus_status(self) -> list[dict]:
        results: list[dict] = []
        params: dict = {"pageSize": 1000}
        while True:
            data = self._get("/v2/queries/antivirus-status", params)
            batch = data.get("results", []) if isinstance(data, dict) else []
            if not batch:
                break
            results.extend(batch)

            cursor = data.get("cursor") if isinstance(data, dict) else None
            if not cursor or cursor.get("offset", 0) >= cursor.get("count", 0):
                break
            params = {"pageSize": 1000, "cursor": cursor.get("name")}
        return results

    def _fetch_token(self) -> str:
        now = time.time()
        if self._token and now < self._token_expires_at - 60:
            return self._token

        payload = {
            "grant_type": "client_credentials",
            "client_id": self._settings.ninjaone_client_id,
            "client_secret": self._settings.ninjaone_client_secret,
            "scope": self._settings.ninjaone_scope,
        }

        try:
            with httpx.Client(timeout=30) as client:
                resp = client.post(self._settings.ninjaone_token_url, data=payload)
                resp.raise_for_status()
                body = resp.json()
        except httpx.HTTPError as exc:
            raise NinjaApiError(f"Failed to obtain NinjaOne access token: {exc}") from exc

        token = body.get("access_token")
        if not token:
            raise NinjaApiError("NinjaOne token response did not contain an access_token")

        self._token = token
        self._token_expires_at = now + int(body.get("expires_in", 3600))
        return token

    def _get_all_pages(self, path: str, after_field: str | None = None, cursor_field: str | None = None) -> list[dict]:
        results: list[dict] = []
        params: dict = {}
        while True:
            data = self._get(path, params)
            batch = data.get("results", data) if isinstance(data, dict) else data
            if not isinstance(batch, list) or not batch:
                break
            results.extend(batch)

            if after_field:
                params = {"after": batch[-1].get(after_field)}
            elif cursor_field:
                next_cursor = data.get("cursor") if isinstance(data, dict) else None
                if not next_cursor:
                    break
                params = {"cursor": next_cursor}
            else:
                break
        return results

    def _get(self, path: str, params: dict | None = None) -> dict | list:
        token = self._fetch_token()
        url = f"{self._settings.ninjaone_base_url.rstrip('/')}{path}"
        headers = {"Authorization": f"Bearer {token}"}

        last_error: Exception | None = None
        for attempt in range(2):
            try:
                with httpx.Client(timeout=30, follow_redirects=True) as client:
                    resp = client.get(url, headers=headers, params=params)
                if resp.status_code >= 500 and attempt == 0:
                    last_error = NinjaApiError(f"NinjaOne returned {resp.status_code} for {url}")
                    continue
                resp.raise_for_status()
                return resp.json()
            except httpx.HTTPError as exc:
                last_error = NinjaApiError(f"NinjaOne request to {url} failed: {exc}")

        raise last_error or NinjaApiError(f"NinjaOne request to {url} failed")
