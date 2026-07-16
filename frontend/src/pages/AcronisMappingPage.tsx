import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getCustomers } from "../api/customers";
import { getUnmappedTenants, saveTenantMapping } from "../api/acronis";
import { AppShell } from "../components/AppShell";
import { BytesCell } from "../components/BytesCell";
import { SkeletonTable } from "../components/Skeleton";
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
      setError(err instanceof Error ? err.message : "Failed to save mapping");
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

export function AcronisMappingPage() {
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
      setError(err instanceof Error ? err.message : "Failed to load data");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  function handleMapped(tenantId: string) {
    setTenants((prev) => prev.filter((t) => t.tenant_id !== tenantId));
  }

  return (
    <AppShell>
      <div className="page">
        <header className="page-header">
          <div>
            <Link to="/" className="link-button">
              ← Back
            </Link>
            <h1>Map Acronis tenants</h1>
          </div>
        </header>

        {error && <div className="error-text">{error}</div>}

        {loading ? (
          <SkeletonTable rows={5} cols={6} />
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Acronis tenant</th>
                <th>Backup used / total</th>
                <th>Machines</th>
                <th>Mailboxes</th>
                <th>Customer</th>
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
                    No unmapped tenants — everything is matched.
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
