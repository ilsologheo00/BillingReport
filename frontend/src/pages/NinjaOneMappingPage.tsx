import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getCustomers } from "../api/customers";
import { getUnmappedOrgs, saveOrgMapping } from "../api/ninjaone";
import { AppShell } from "../components/AppShell";
import { SkeletonTable } from "../components/Skeleton";
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
      setError(err instanceof Error ? err.message : "Failed to save mapping");
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
          <option value="">Select customer…</option>
          {customers.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
      </td>
      <td>
        <button onClick={save} disabled={saving || !customerId}>
          {saving ? "Saving…" : "Save"}
        </button>
        {error && <span className="error-text small">{error}</span>}
      </td>
    </tr>
  );
}

export function NinjaOneMappingPage() {
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
      setError(err instanceof Error ? err.message : "Failed to load data");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
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
              ← Back
            </Link>
            <h1>Map NinjaOne organizations</h1>
          </div>
        </header>

        {error && <div className="error-text">{error}</div>}

        {loading ? (
          <SkeletonTable rows={5} cols={5} />
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>NinjaOne organization</th>
                <th>Devices</th>
                <th>SentinelOne</th>
                <th>Customer</th>
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
                    No unmapped organizations — everything is matched.
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
