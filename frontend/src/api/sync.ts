import { apiFetch } from "./client";
import type { SyncLog } from "./types";

export function triggerSync(): Promise<SyncLog> {
  return apiFetch<SyncLog>("/api/sync", { method: "POST" });
}

export function getSyncStatus(): Promise<SyncLog> {
  return apiFetch<SyncLog>("/api/sync/status");
}
