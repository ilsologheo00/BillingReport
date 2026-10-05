"""Real Acronis Cyber Protect Cloud API client.

Verified against a live tenant:

- Auth: POST https://{datacenter}/api/2/idp/token, Basic auth of
  client_id:client_secret, body grant_type=client_credentials. Response has
  `expires_on` as an absolute Unix timestamp (not `expires_in`). `_fetch_token`
  retries once on a transient failure (network blip, timeout, 5xx) rather than
  failing the whole sync over a single bad connection attempt.
- Tenants: GET https://{datacenter}/api/2/tenants (paginated via
  `paging.cursors.after`), filtered client-side to `kind == "customer"`.
  Requires one of uuids/parent_id/subtree_root_id/after - the partner's own
  tenant id (from the `owner_tuid` claim in the access token JWT) is used as
  `subtree_root_id` to fetch the whole hierarchy.
- Usage: GET https://{datacenter}/api/2/tenants/{id}/usages (no filter - the
  per-tenant offering can name its line items differently, e.g.
  `pw_base_storage` vs `pg_base_storage`, so all items are fetched and the
  active one, `offering_item.status == 1`, is picked per usage_name). This one
  endpoint covers everything shown per customer:
  - "storage" -> value (bytes used) / offering_item.quota.value (bytes quota,
    absent/None when the tenant's edition has no fixed cap, e.g. per-workload
    billing).
  - "mailboxes" -> value (protected Microsoft 365 seats), summed with
    "m365_seats_shared" (protected shared mailboxes) and
    "o365_sharepoint_sites" (protected SharePoint Online sites) - all
    billed/tracked as separate line items by Acronis but shown here as one
    combined "Microsoft 365" protected-item count.
  - "dr_storage" -> value (bytes used in Disaster Recovery storage) /
    offering_item.quota.value (always None/no fixed cap on every tenant
    checked live in this account - per-workload billing - but read the same
    way as "storage" in case some edition does cap it).
  - "servers" / "workstations" / "vms" -> value (protected-workload counts).
    This is the exact figure Acronis's own console shows (e.g. "Virtual
    machines 2/Unlimited") - deliberately *not* derived from the resource
    inventory API (GET .../resource_management/v4/resources), which was the
    original approach here: classify each resource by its `type` field
    (resource.virtual_machine.* -> VM, resource.machine -> server/workstation
    via the Windows GetVersionEx ProductType enum). That looked right on every
    tenant checked - until one turned up a VM protected through an in-guest
    agent (type resource.machine) rather than agentless hypervisor-level
    backup, which the heuristic then counted as a server, silently diverging
    from Acronis's own console for that one customer (confirmed live:
    BillingReport showed 2 servers/1 VM where Acronis's console, and this
    usages endpoint, both say 1 server/2 VMs). Reading the counts straight
    from usages can't have that failure mode - it's Acronis's own figure, not
    a reimplementation of it - and it's cheaper too: one call per tenant
    instead of one per sub-tenant plus one per agent-installed machine.
"""

import base64
import json
import time
from concurrent.futures import ThreadPoolExecutor
from typing import NamedTuple

import httpx

from app.config import Settings
from app.services.acronis.base import AcronisApiError, AcronisTenantStatsDTO

_TENANT_FETCH_CONCURRENCY = 10


class _UsageStats(NamedTuple):
    storage_total_bytes: int | None
    storage_used_bytes: int
    mailboxes_count: int
    dr_storage_total_bytes: int | None
    dr_storage_used_bytes: int
    server_count: int
    workstation_count: int
    vm_count: int


class LiveAcronisProvider:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._token: str | None = None
        self._token_expires_at: float = 0.0
        self._root_tenant_id: str | None = None

    def get_tenant_stats(self) -> list[AcronisTenantStatsDTO]:
        self._fetch_token()  # ensures self._root_tenant_id is populated
        tenants = self._get_all_pages(
            self._account_url("/tenants"),
            params={"lod": "basic", "subtree_root_id": self._root_tenant_id},
        )
        customer_tenants = [t for t in tenants if t.get("kind") == "customer"]

        def fetch_one(tenant: dict) -> AcronisTenantStatsDTO:
            tenant_id = tenant["id"]
            usage = self._get_usages(tenant_id)
            return AcronisTenantStatsDTO(
                tenant_id=tenant_id,
                tenant_name=tenant.get("name", ""),
                backup_total_bytes=usage.storage_total_bytes,
                backup_used_bytes=usage.storage_used_bytes,
                backup_server_count=usage.server_count,
                backup_workstation_count=usage.workstation_count,
                backup_vm_count=usage.vm_count,
                backup_mailboxes_count=usage.mailboxes_count,
                dr_storage_total_bytes=usage.dr_storage_total_bytes,
                dr_storage_used_bytes=usage.dr_storage_used_bytes,
            )

        with ThreadPoolExecutor(max_workers=_TENANT_FETCH_CONCURRENCY) as pool:
            return list(pool.map(fetch_one, customer_tenants))

    # -- internals -----------------------------------------------------

    def _datacenter_host(self) -> str:
        return self._settings.acronis_datacenter.strip().removeprefix("https://").removeprefix("http://").rstrip("/")

    def _account_url(self, path: str) -> str:
        return f"https://{self._datacenter_host()}/api/2{path}"

    def _get_usages(self, tenant_id: str) -> _UsageStats:
        data = self._get(self._account_url(f"/tenants/{tenant_id}/usages"))
        items = data.get("items", []) if isinstance(data, dict) else []

        def active_item(usage_name: str) -> dict | None:
            return next(
                (i for i in items if i.get("usage_name") == usage_name and (i.get("offering_item") or {}).get("status") == 1),
                None,
            )

        def active_value(usage_name: str) -> int:
            item = active_item(usage_name)
            return int(item.get("value") or 0) if item is not None else 0

        storage = active_item("storage")
        used = int(storage.get("value") or 0) if storage is not None else 0
        quota_value = (storage.get("offering_item") or {}).get("quota", {}).get("value") if storage is not None else None
        total = int(quota_value) if quota_value is not None else None

        mailboxes_count = active_value("mailboxes") + active_value("m365_seats_shared") + active_value("o365_sharepoint_sites")

        dr_storage = active_item("dr_storage")
        dr_used = int(dr_storage.get("value") or 0) if dr_storage is not None else 0
        dr_quota_value = (dr_storage.get("offering_item") or {}).get("quota", {}).get("value") if dr_storage is not None else None
        dr_total = int(dr_quota_value) if dr_quota_value is not None else None

        return _UsageStats(
            storage_total_bytes=total,
            storage_used_bytes=used,
            mailboxes_count=mailboxes_count,
            dr_storage_total_bytes=dr_total,
            dr_storage_used_bytes=dr_used,
            server_count=active_value("servers"),
            workstation_count=active_value("workstations"),
            vm_count=active_value("vms"),
        )

    def _fetch_token(self) -> str:
        now = time.time()
        if self._token and now < self._token_expires_at - 60:
            return self._token

        creds = f"{self._settings.acronis_client_id}:{self._settings.acronis_client_secret}"
        basic = base64.b64encode(creds.encode()).decode()
        headers = {
            "Authorization": f"Basic {basic}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        # Retry once on a transient failure (network blip, timeout, 5xx) rather
        # than failing the whole sync on a single bad connection attempt - the
        # same resilience already applied to every other call in this class.
        last_error: Exception | None = None
        body = None
        for attempt in range(2):
            try:
                with httpx.Client(timeout=30) as client:
                    resp = client.post(self._account_url("/idp/token"), headers=headers, data={"grant_type": "client_credentials"})
                if resp.status_code >= 500 and attempt == 0:
                    last_error = AcronisApiError(f"Acronis token endpoint returned {resp.status_code}")
                    continue
                resp.raise_for_status()
                body = resp.json()
                break
            except httpx.HTTPError as exc:
                last_error = AcronisApiError(f"Failed to obtain Acronis access token: {exc}")

        if body is None:
            raise last_error or AcronisApiError("Failed to obtain Acronis access token")

        token = body.get("access_token")
        if not token:
            raise AcronisApiError("Acronis token response did not contain an access_token")

        self._token = token
        self._token_expires_at = float(body.get("expires_on") or (now + 3600))
        self._root_tenant_id = self._extract_owner_tenant_id(token)
        return token

    @staticmethod
    def _extract_owner_tenant_id(access_token: str) -> str | None:
        """The API client's own (partner) tenant id, needed as subtree_root_id
        since GET /tenants requires an explicit scope - it isn't returned
        anywhere else, only as the `owner_tuid` claim in the access token."""
        try:
            payload_b64 = access_token.split(".")[1]
            padded = payload_b64 + "=" * (-len(payload_b64) % 4)
            claims = json.loads(base64.urlsafe_b64decode(padded))
            return claims.get("owner_tuid")
        except (IndexError, ValueError):
            return None

    def _get_all_pages(self, url: str, params: dict) -> list[dict]:
        results: list[dict] = []
        page_params = dict(params)
        while True:
            data = self._get(url, page_params)
            items = data.get("items", []) if isinstance(data, dict) else data
            if not items:
                break
            results.extend(items)
            after = (data.get("paging") or {}).get("cursors", {}).get("after") if isinstance(data, dict) else None
            if not after:
                break
            page_params = {**params, "after": after}
        return results

    def _get(self, url: str, params: dict | None = None) -> dict | list:
        token = self._fetch_token()
        headers = {"Authorization": f"Bearer {token}"}

        last_error: Exception | None = None
        for attempt in range(2):
            try:
                with httpx.Client(timeout=30, follow_redirects=True) as client:
                    resp = client.get(url, headers=headers, params=params)
                if resp.status_code >= 500 and attempt == 0:
                    last_error = AcronisApiError(f"Acronis returned {resp.status_code} for {url}")
                    continue
                resp.raise_for_status()
                return resp.json()
            except httpx.HTTPError as exc:
                last_error = AcronisApiError(f"Acronis request to {url} failed: {exc}")

        raise last_error or AcronisApiError(f"Acronis request to {url} failed")
