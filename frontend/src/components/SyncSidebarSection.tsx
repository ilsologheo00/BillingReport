import { useSync } from "../sync/SyncContext";
import { useLanguage } from "../i18n/LanguageContext";
import { RefreshIcon } from "./icons";
import type { AcronisSyncLog, NinjaSyncLog, SyncLog } from "../api/types";

function statusDot(lastSync: { status: string } | null): "none" | "success" | "failed" | "running" {
  if (lastSync === null) return "none";
  if (lastSync.status === "success") return "success";
  if (lastSync.status === "failed") return "failed";
  return "running";
}

function SyncItem({
  label,
  syncing,
  lastSync,
  tooltip,
  onClick,
}: {
  label: string;
  syncing: boolean;
  lastSync: { status: string } | null;
  tooltip: string;
  onClick: () => void;
}) {
  return (
    <button className="sidebar-link sidebar-sync-link" onClick={onClick} disabled={syncing} title={tooltip}>
      <RefreshIcon className={syncing ? "spin" : undefined} />
      {label}
      <span className={`sync-dot sync-dot-${syncing ? "running" : statusDot(lastSync)}`} />
    </button>
  );
}

export function SyncSidebarSection() {
  const { t, lang } = useLanguage();
  const { ion, ninjaone, acronis } = useSync();

  function tooltipFor(lastSync: SyncLog | null): string {
    if (!lastSync) return t("sync.never");
    return t("sync.lastSynced", {
      date: new Date(lastSync.started_at).toLocaleString(lang),
      status: t(`status.${lastSync.status}`),
    });
  }

  function tooltipForMatch(lastSync: NinjaSyncLog | AcronisSyncLog | null, matched: number, unmatched: number): string {
    if (!lastSync) return t("sync.never");
    return t("sync.lastSyncedMatch", {
      date: new Date(lastSync.started_at).toLocaleString(lang),
      status: t(`status.${lastSync.status}`),
      matched,
      unmatched,
    });
  }

  return (
    <div className="sidebar-section">
      <p className="sidebar-section-label">{t("nav.sync")}</p>
      <SyncItem label="ION" syncing={ion.syncing} lastSync={ion.lastSync} tooltip={tooltipFor(ion.lastSync)} onClick={ion.sync} />
      <SyncItem
        label="NinjaOne"
        syncing={ninjaone.syncing}
        lastSync={ninjaone.lastSync}
        tooltip={tooltipForMatch(ninjaone.lastSync, ninjaone.lastSync?.orgs_matched ?? 0, ninjaone.lastSync?.orgs_unmatched ?? 0)}
        onClick={ninjaone.sync}
      />
      <SyncItem
        label="Acronis"
        syncing={acronis.syncing}
        lastSync={acronis.lastSync}
        tooltip={tooltipForMatch(acronis.lastSync, acronis.lastSync?.tenants_matched ?? 0, acronis.lastSync?.tenants_unmatched ?? 0)}
        onClick={acronis.sync}
      />
      {(ion.error || ninjaone.error || acronis.error) && (
        <span className="error-text small" role="alert">{ion.error || ninjaone.error || acronis.error}</span>
      )}
    </div>
  );
}
