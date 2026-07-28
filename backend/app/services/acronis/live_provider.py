"""Real Acronis Cyber Protect Cloud API client.

Verified against Acronis's published OpenAPI specs (Account Management API v2
and Resource & Policy Management API v4) - not yet exercised against a live
tenant, so treat as a solid-but-unconfirmed starting point:

- Auth: POST https://{datacenter}/api/2/idp/token, Basic auth of
  client_id:client_secret, body grant_type=client_credentials. Response has
  `expires_on` as an absolute Unix timestamp (not `expires_in`).
- Tenants: GET https://{datacenter}/api/2/tenants (paginated via
  `paging.cursors.after`), filtered client-side to `kind == "customer"`.
  Requires one of uuids/parent_id/subtree_root_id/after - the partner's own
  tenant id (from the `owner_tuid` claim in the access token JWT) is used as
  `subtree_root_id` to fetch the whole hierarchy.
- Usage: GET https://{datacenter}/api/2/tenants/{id}/usages (no filter - the
  per-tenant offering can name its storage/mailbox line items differently,
  e.g. `pw_base_storage` vs `pg_base_storage`, so all items are fetched and
  the active one, `offering_item.status == 1`, is picked per usage_name).
  usage_name "storage" -> value (bytes used) / offering_item.quota.value
  (bytes quota, absent/None when the tenant's edition has no fixed cap, e.g.
  per-workload billing). usage_name "mailboxes" -> value (number of
  protected Microsoft 365 seats), summed with "m365_seats_shared" (protected
  shared mailboxes) and "o365_sharepoint_sites" (protected SharePoint Online
  sites) - all billed/tracked as separate line items by Acronis but shown
  here as one combined "Microsoft 365" protected-item count.
- Resources: GET https://{datacenter}/api/resource_management/v4/resources
  ?tenant_id={id}&applied_only=true (only resources with an active backup
  plan) - split into server/workstation/VM counts (see below). Confirmed
  against a live tenant: resources are registered against the "unit"
  tenant(s) nested under a "customer" tenant, never against the "customer"
  tenant itself (querying with the customer tenant id always returns zero
  items) - so each customer's resources are fetched by first finding all
  descendant "unit" tenants and querying each of those, aggregating the
  results. Microsoft 365 mailboxes never show up here (confirmed against
  multiple tenants known to have M365 seats) - Acronis's public API has no
  endpoint that lists individual protected mailbox addresses, only the
  aggregate seat count from the usages endpoint above.
- Machine type breakdown: each resource has a `type` field. Hypervisor-backed
  VMs (`resource.virtual_machine.*` - vmwesx/mshyperv/proxmox confirmed live)
  count directly as VMs, no extra call needed. NAS devices and any other
  non-machine resource type count as "server" (infrastructure-class, not a
  workstation). Agent-installed machines (`resource.machine`) can be either a
  server or a workstation - telling them apart needs one extra call per such
  resource, GET .../resource_management/v4/resources/{id}/attributes, whose
  "default" attribute group has `operating_system_product_type`: this is the
  classic Windows `GetVersionEx` ProductType enum (1 = workstation, 2 = domain
  controller, 3 = server - confirmed live: a Windows 11 Pro machine reports
  1). Anything else (missing value, non-Windows OS) defaults to "server"
  rather than silently miscounting it as a workstation.
"""

import base64
import json
import time
from concurrent.futures import ThreadPoolExecutor

import httpx

from app.config import Settings
from app.services.acronis.base import AcronisApiError, AcronisTenantStatsDTO

_TENANT_FETCH_CONCURRENCY = 10


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

        children_by_parent: dict[str, list[dict]] = {}
        for t in tenants:
            children_by_parent.setdefault(t.get("parent_id"), []).append(t)

        def descendant_unit_ids(customer_id: str) -> list[str]:
            unit_ids: list[str] = []
            stack = list(children_by_parent.get(customer_id, []))
            while stack:
                t = stack.pop()
                if t.get("kind") == "unit":
                    unit_ids.append(t["id"])
                stack.extend(children_by_parent.get(t["id"], []))
            return unit_ids

        def fetch_one(tenant: dict) -> AcronisTenantStatsDTO:
            tenant_id = tenant["id"]
            total_bytes, used_bytes, mailboxes_count = self._get_usages(tenant_id)
            server_count, workstation_count, vm_count = self._get_machine_counts(descendant_unit_ids(tenant_id))
            return AcronisTenantStatsDTO(
                tenant_id=tenant_id,
                tenant_name=tenant.get("name", ""),
                backup_total_bytes=total_bytes,
                backup_used_bytes=used_bytes,
                backup_server_count=server_count,
                backup_workstation_count=workstation_count,
                backup_vm_count=vm_count,
                backup_mailboxes_count=mailboxes_count,
            )

        with ThreadPoolExecutor(max_workers=_TENANT_FETCH_CONCURRENCY) as pool:
            return list(pool.map(fetch_one, customer_tenants))

    # -- internals -----------------------------------------------------

    def _datacenter_host(self) -> str:
        return self._settings.acronis_datacenter.strip().removeprefix("https://").removeprefix("http://").rstrip("/")

    def _account_url(self, path: str) -> str:
        return f"https://{self._datacenter_host()}/api/2{path}"

    def _resource_url(self, path: str) -> str:
        return f"https://{self._datacenter_host()}/api{path}"

    def _get_usages(self, tenant_id: str) -> tuple[int | None, int, int]:
        data = self._get(self._account_url(f"/tenants/{tenant_id}/usages"))
        items = data.get("items", []) if isinstance(data, dict) else []

        def active_item(usage_name: str) -> dict | None:
            return next(
                (i for i in items if i.get("usage_name") == usage_name and (i.get("offering_item") or {}).get("status") == 1),
                None,
            )

        storage = active_item("storage")
        used = int(storage.get("value") or 0) if storage is not None else 0
        quota_value = (storage.get("offering_item") or {}).get("quota", {}).get("value") if storage is not None else None
        total = int(quota_value) if quota_value is not None else None

        mailboxes = active_item("mailboxes")
        mailboxes_count = int(mailboxes.get("value") or 0) if mailboxes is not None else 0

        shared_mailboxes = active_item("m365_seats_shared")
        shared_mailboxes_count = int(shared_mailboxes.get("value") or 0) if shared_mailboxes is not None else 0

        sharepoint_sites = active_item("o365_sharepoint_sites")
        sharepoint_sites_count = int(sharepoint_sites.get("value") or 0) if sharepoint_sites is not None else 0

        return total, used, mailboxes_count + shared_mailboxes_count + sharepoint_sites_count

    def _get_machine_counts(self, unit_tenant_ids: list[str]) -> tuple[int, int, int]:
        resources: list[dict] = []
        for unit_tenant_id in unit_tenant_ids:
            resources.extend(self._get_all_pages(
                self._resource_url("/resource_management/v4/resources"),
                params={"tenant_id": unit_tenant_id, "applied_only": "true"},
            ))

        server_count = 0
        workstation_count = 0
        vm_count = 0
        agent_machine_ids: list[str] = []
        for resource in resources:
            resource_type = resource.get("type", "")
            if resource_type.startswith("resource.virtual_machine"):
                vm_count += 1
            elif resource_type == "resource.machine":
                agent_machine_ids.append(resource["id"])
            else:
                server_count += 1

        for resource_id in agent_machine_ids:
            if self._get_os_product_type(resource_id) == 1:
                workstation_count += 1
            else:
                server_count += 1

        return server_count, workstation_count, vm_count

    def _get_os_product_type(self, resource_id: str) -> int | None:
        try:
            data = self._get(self._resource_url(f"/resource_management/v4/resources/{resource_id}/attributes"))
        except AcronisApiError:
            return None
        for group in data.get("items", []) if isinstance(data, dict) else []:
            if group.get("name") != "default":
                continue
            for kv in group.get("kvs", []):
                if kv.get("key") == "operating_system_product_type":
                    try:
                        return int(kv.get("value"))
                    except (TypeError, ValueError):
                        return None
        return None

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

        try:
            with httpx.Client(timeout=30) as client:
                resp = client.post(self._account_url("/idp/token"), headers=headers, data={"grant_type": "client_credentials"})
                resp.raise_for_status()
                body = resp.json()
        except httpx.HTTPError as exc:
            raise AcronisApiError(f"Failed to obtain Acronis access token: {exc}") from exc

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
