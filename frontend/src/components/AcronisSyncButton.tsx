import { useState } from "react";
import { triggerAcronisSync } from "../api/acronis";
import type { AcronisSyncLog } from "../api/types";

export function AcronisSyncButton({ lastSync, onSynced }: { lastSync: AcronisSyncLog | null; onSynced: (log: AcronisSyncLog) => void }) {
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSync() {
    setSyncing(true);
    setError(null);
    try {
      const log = await triggerAcronisSync();
      onSynced(log);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Sync failed");
    } finally {
      setSyncing(false);
    }
  }

  return (
    <div className="sync-panel">
      <button onClick={handleSync} disabled={syncing}>
        {syncing ? "Syncing…" : "Sync Acronis"}
      </button>
      <span className="sync-status">
        {lastSync
          ? `Last synced: ${new Date(lastSync.started_at).toLocaleString()} (${lastSync.status}, ${lastSync.tenants_matched} matched / ${lastSync.tenants_unmatched} unmatched)`
          : "Never synced"}
      </span>
      {error && <span className="error-text">{error}</span>}
    </div>
  );
}
