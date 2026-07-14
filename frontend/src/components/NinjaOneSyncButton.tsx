import { useState } from "react";
import { triggerNinjaOneSync } from "../api/ninjaone";
import type { NinjaSyncLog } from "../api/types";

export function NinjaOneSyncButton({ lastSync, onSynced }: { lastSync: NinjaSyncLog | null; onSynced: (log: NinjaSyncLog) => void }) {
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSync() {
    setSyncing(true);
    setError(null);
    try {
      const log = await triggerNinjaOneSync();
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
        {syncing ? "Syncing…" : "Sync NinjaOne"}
      </button>
      <span className="sync-status">
        {lastSync
          ? `Last synced: ${new Date(lastSync.started_at).toLocaleString()} (${lastSync.status}, ${lastSync.orgs_matched} matched / ${lastSync.orgs_unmatched} unmatched)`
          : "Never synced"}
      </span>
      {error && <span className="error-text">{error}</span>}
    </div>
  );
}
