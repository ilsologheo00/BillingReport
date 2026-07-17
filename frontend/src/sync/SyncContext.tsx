import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { getSyncStatus, triggerSync } from "../api/sync";
import { getNinjaOneSyncStatus, triggerNinjaOneSync } from "../api/ninjaone";
import { getAcronisSyncStatus, triggerAcronisSync } from "../api/acronis";
import { useLanguage } from "../i18n/LanguageContext";
import type { AcronisSyncLog, NinjaSyncLog, SyncLog } from "../api/types";

interface SyncSlice<T> {
  lastSync: T | null;
  syncing: boolean;
  error: string | null;
  sync: () => void;
}

interface SyncContextValue {
  ion: SyncSlice<SyncLog>;
  ninjaone: SyncSlice<NinjaSyncLog>;
  acronis: SyncSlice<AcronisSyncLog>;
  /** Bumped after every successful sync, so pages can watch it to know when to refetch their own data. */
  version: number;
}

const SyncContext = createContext<SyncContextValue | undefined>(undefined);

function useSyncSlice<T>(
  getStatus: () => Promise<T>,
  trigger: () => Promise<T>,
  onSynced: () => void
): SyncSlice<T> {
  const { t } = useLanguage();
  const [lastSync, setLastSync] = useState<T | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getStatus()
      .then(setLastSync)
      .catch(() => setLastSync(null));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const sync = useCallback(async () => {
    setSyncing(true);
    setError(null);
    try {
      const log = await trigger();
      setLastSync(log);
      onSynced();
    } catch (err) {
      setError(err instanceof Error ? err.message : t("sync.failed"));
    } finally {
      setSyncing(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [t]);

  return { lastSync, syncing, error, sync };
}

export function SyncProvider({ children }: { children: ReactNode }) {
  const [version, setVersion] = useState(0);
  const bump = useCallback(() => setVersion((v) => v + 1), []);

  const ion = useSyncSlice(getSyncStatus, triggerSync, bump);
  const ninjaone = useSyncSlice(getNinjaOneSyncStatus, triggerNinjaOneSync, bump);
  const acronis = useSyncSlice(getAcronisSyncStatus, triggerAcronisSync, bump);

  const value = useMemo<SyncContextValue>(
    () => ({ ion, ninjaone, acronis, version }),
    [ion, ninjaone, acronis, version]
  );

  return <SyncContext.Provider value={value}>{children}</SyncContext.Provider>;
}

export function useSync(): SyncContextValue {
  const ctx = useContext(SyncContext);
  if (!ctx) throw new Error("useSync must be used within SyncProvider");
  return ctx;
}
