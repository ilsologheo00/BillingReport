import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getCustomers } from "../api/customers";
import { getUnmappedTenants, saveTenantMapping } from "../api/acronis";
import { AppShell } from "../components/AppShell";
import { BytesCell } from "../components/BytesCell";
import { SkeletonTable } from "../components/Skeleton";
import { useLanguage } from "../i18n/LanguageContext";
import type { AcronisOrgStat, CustomerSummary } from "../api/types";

function MappingRow({
  tenant,
  customers,
  onMapped,
}: {
  tenant: AcronisOrgStat;
  customers: CustomerSummary[];
  onMapped: (tenantId: string) => void;
}) {
  const { t } = useLanguage();
  const [customerId, setCustomerId] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function save() {
    if (!customerId) return;
    setSaving(true);
    setError(null);
    try {
      await saveTenantMapping(tenant.tenant_id, Number(customerId));
      onMapped(tenant.tenant_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : t("common.failedToSaveMapping"));
    } finally {
      setSaving(false);
    }
  }

  return (
    <tr>
      <td>{tenant.tenant_name}</td>
      <td><BytesCell value={tenant.backup_used_bytes} /> / <BytesCell value={tenant.backup_total_bytes} /></td>
      <td>{tenant.backup_machines_count}</td>
      <td>{tenant.backup_mailboxes_count}</td>
      <td>
        <select value={customerId} onChange={(e) => setCustomerId(e.target.value)} disabled={saving}>
          <option value="">{t("common.selectCustomer")}</option>
          {customers.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
      </td>
      <td>
        <button onClick={save} disabled={saving || !customerId}>
          {saving ? t("common.saving") : t("common.save")}
        </button>
        {error && <span className="error-text small">{error}</span>}
      </td>
    </tr>
  );
}

export function AcronisMappingPage() {
  const { t } = useLanguage();
  const [tenants, setTenants] = useState<AcronisOrgStat[]>([]);
  const [customers, setCustomers] = useState<CustomerSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    setLoading(true);
    setError(null);
    try {
      const [unmapped, customerList] = await Promise.all([getUnmappedTenants(), getCustomers()]);
      setTenants(unmapped);
      setCustomers(customerList);
    } catch (err) {
      setError(err instanceof Error ? err.message : t("common.failedToLoadData"));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function handleMapped(tenantId: string) {
    setTenants((prev) => prev.filter((tenant) => tenant.tenant_id !== tenantId));
  }

  return (
    <AppShell>
      <div className="page">
        <header className="page-header">
          <div>
            <Link to="/" className="link-button">
              {t("common.back")}
            </Link>
            <h1>{t("acronisMapping.title")}</h1>
          </div>
        </header>

        {error && <div className="error-text">{error}</div>}

        {loading ? (
          <SkeletonTable rows={5} cols={6} />
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>{t("acronisMapping.table.tenant")}</th>
                <th>{t("common.backupUsedTotal")}</th>
                <th>{t("common.machines")}</th>
                <th>{t("common.mailboxes")}</th>
                <th>{t("dashboard.table.customer")}</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {tenants.map((tenant) => (
                <MappingRow key={tenant.tenant_id} tenant={tenant} customers={customers} onMapped={handleMapped} />
              ))}
              {tenants.length === 0 && (
                <tr>
                  <td colSpan={6} className="empty-row">
                    {t("acronisMapping.empty")}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        )}
      </div>
    </AppShell>
  );
}
