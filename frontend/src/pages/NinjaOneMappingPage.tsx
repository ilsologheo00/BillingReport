import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getCustomers } from "../api/customers";
import { getUnmappedOrgs, saveOrgMapping } from "../api/ninjaone";
import { AppShell } from "../components/AppShell";
import { SkeletonTable } from "../components/Skeleton";
import { useLanguage } from "../i18n/LanguageContext";
import type { CustomerSummary, NinjaOrgStat } from "../api/types";

function MappingRow({
  org,
  customers,
  onMapped,
}: {
  org: NinjaOrgStat;
  customers: CustomerSummary[];
  onMapped: (orgName: string) => void;
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
      await saveOrgMapping(org.org_name, Number(customerId));
      onMapped(org.org_name);
    } catch (err) {
      setError(err instanceof Error ? err.message : t("common.failedToSaveMapping"));
    } finally {
      setSaving(false);
    }
  }

  return (
    <tr>
      <td>{org.org_name}</td>
      <td>{org.device_count}</td>
      <td>{org.sentinelone_count}</td>
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

export function NinjaOneMappingPage() {
  const { t } = useLanguage();
  const [orgs, setOrgs] = useState<NinjaOrgStat[]>([]);
  const [customers, setCustomers] = useState<CustomerSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    setLoading(true);
    setError(null);
    try {
      const [unmapped, customerList] = await Promise.all([getUnmappedOrgs(), getCustomers()]);
      setOrgs(unmapped);
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

  function handleMapped(orgName: string) {
    setOrgs((prev) => prev.filter((o) => o.org_name !== orgName));
  }

  return (
    <AppShell>
      <div className="page">
        <header className="page-header">
          <div>
            <Link to="/" className="link-button">
              {t("common.back")}
            </Link>
            <h1>{t("ninjaMapping.title")}</h1>
          </div>
        </header>

        {error && <div className="error-text">{error}</div>}

        {loading ? (
          <SkeletonTable rows={5} cols={5} />
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>{t("ninjaMapping.table.org")}</th>
                <th>{t("common.devices")}</th>
                <th>{t("common.sentinelone")}</th>
                <th>{t("dashboard.table.customer")}</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {orgs.map((org) => (
                <MappingRow key={org.org_name} org={org} customers={customers} onMapped={handleMapped} />
              ))}
              {orgs.length === 0 && (
                <tr>
                  <td colSpan={5} className="empty-row">
                    {t("ninjaMapping.empty")}
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
