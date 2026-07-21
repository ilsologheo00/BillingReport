import { apiFetch } from "./client";
import type { AcronisOrgStat, AcronisSyncLog } from "./types";

export function triggerAcronisSync(): Promise<AcronisSyncLog> {
  return apiFetch<AcronisSyncLog>("/api/acronis/sync", { method: "POST" });
}

export function getAcronisSyncStatus(): Promise<AcronisSyncLog> {
  return apiFetch<AcronisSyncLog>("/api/acronis/sync/status");
}

export function getUnmappedTenants(): Promise<AcronisOrgStat[]> {
  return apiFetch<AcronisOrgStat[]>("/api/acronis/unmapped");
}

export function saveTenantMapping(tenantId: string, customerId: number): Promise<AcronisOrgStat> {
  return apiFetch<AcronisOrgStat>("/api/acronis/mapping", {
    method: "POST",
    body: JSON.stringify({ tenant_id: tenantId, customer_id: customerId }),
  });
}

export function createStandaloneCustomer(tenantId: string): Promise<AcronisOrgStat> {
  return apiFetch<AcronisOrgStat>("/api/acronis/mapping/standalone", {
    method: "POST",
    body: JSON.stringify({ tenant_id: tenantId }),
  });
}
