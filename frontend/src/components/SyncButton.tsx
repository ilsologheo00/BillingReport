import { useState } from "react";
import { triggerSync } from "../api/sync";
import type { SyncLog } from "../api/types";

export function SyncButton({ lastSync, onSynced }: { lastSync: SyncLog | null; onSynced: (log: SyncLog) => void }) {
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSync() {
    setSyncing(true);
    setError(null);
    try {
      const log = await triggerSync();
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
        {syncing ? "Syncing…" : "Sync Now"}
      </button>
      <span className="sync-status">
        {lastSync
          ? `Last synced: ${new Date(lastSync.started_at).toLocaleString()} (${lastSync.status})`
          : "Never synced"}
      </span>
      {error && <span className="error-text">{error}</span>}
    </div>
  );
}
