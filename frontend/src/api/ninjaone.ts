import { apiFetch } from "./client";
import type { NinjaOrgStat, NinjaSyncLog } from "./types";

export function triggerNinjaOneSync(): Promise<NinjaSyncLog> {
  return apiFetch<NinjaSyncLog>("/api/ninjaone/sync", { method: "POST" });
}

export function getNinjaOneSyncStatus(): Promise<NinjaSyncLog> {
  return apiFetch<NinjaSyncLog>("/api/ninjaone/sync/status");
}

export function getUnmappedOrgs(): Promise<NinjaOrgStat[]> {
  return apiFetch<NinjaOrgStat[]>("/api/ninjaone/unmapped");
}

export function saveOrgMapping(orgName: string, customerId: number): Promise<NinjaOrgStat> {
  return apiFetch<NinjaOrgStat>("/api/ninjaone/mapping", {
    method: "POST",
    body: JSON.stringify({ org_name: orgName, customer_id: customerId }),
  });
}

export function createStandaloneCustomer(orgName: string): Promise<NinjaOrgStat> {
  return apiFetch<NinjaOrgStat>("/api/ninjaone/mapping/standalone", {
    method: "POST",
    body: JSON.stringify({ org_name: orgName }),
  });
}
