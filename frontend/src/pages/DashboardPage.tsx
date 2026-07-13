import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getCustomers, getReportSummary } from "../api/customers";
import { getSyncStatus } from "../api/sync";
import { useAuth } from "../auth/AuthContext";
import { MoneyCell } from "../components/MoneyCell";
import { MarginBadge } from "../components/MarginBadge";
import { SyncButton } from "../components/SyncButton";
import type { CustomerSummary, ReportSummary, SyncLog } from "../api/types";

export function DashboardPage() {
  const { logout } = useAuth();
  const [customers, setCustomers] = useState<CustomerSummary[]>([]);
  const [summary, setSummary] = useState<ReportSummary | null>(null);
  const [lastSync, setLastSync] = useState<SyncLog | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    setLoading(true);
    setError(null);
    try {
      const [customerList, reportSummary] = await Promise.all([getCustomers(), getReportSummary()]);
      setCustomers(customerList);
      setSummary(reportSummary);
      try {
        setLastSync(await getSyncStatus());
      } catch {
        setLastSync(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load data");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="page">
      <header className="page-header">
        <h1>BillingReport</h1>
        <button className="link-button" onClick={logout}>
          Sign out
        </button>
      </header>

      <SyncButton lastSync={lastSync} onSynced={(log) => { setLastSync(log); refresh(); }} />

      {error && <div className="error-text">{error}</div>}

      {summary && (
        <div className="summary-bar">
          <div>
            <span className="summary-label">Customers</span>
            <span className="summary-value">{summary.customer_count}</span>
          </div>
          <div>
            <span className="summary-label">Total cost</span>
            <span className="summary-value"><MoneyCell value={summary.total_cost} /></span>
          </div>
          <div>
            <span className="summary-label">Total price</span>
            <span className="summary-value"><MoneyCell value={summary.total_price} /></span>
          </div>
          <div>
            <span className="summary-label">Total margin</span>
            <span className="summary-value">
              <MarginBadge margin={summary.total_margin} marginPct={summary.margin_pct} />
            </span>
          </div>
        </div>
      )}

      {loading ? (
        <p>Loading…</p>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>Customer</th>
              <th># Lines</th>
              <th>Total cost</th>
              <th>Total price</th>
              <th>Margin</th>
            </tr>
          </thead>
          <tbody>
            {customers.map((c) => (
              <tr key={c.id}>
                <td>
                  <Link to={`/customers/${c.id}`}>{c.name}</Link>
                </td>
                <td>{c.line_count}</td>
                <td><MoneyCell value={c.total_cost} /></td>
                <td><MoneyCell value={c.total_price} /></td>
                <td>
                  <MarginBadge margin={c.total_margin} marginPct={c.margin_pct} />
                </td>
              </tr>
            ))}
            {customers.length === 0 && (
              <tr>
                <td colSpan={5} className="empty-row">
                  No customers yet — click "Sync Now" to pull data from ION.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      )}
    </div>
  );
}
