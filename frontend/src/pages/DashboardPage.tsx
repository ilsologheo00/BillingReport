import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getCustomers, getReportSummary } from "../api/customers";
import { getSyncStatus } from "../api/sync";
import { getNinjaOneSyncStatus } from "../api/ninjaone";
import { AppShell } from "../components/AppShell";
import { MoneyCell, formatMoney } from "../components/MoneyCell";
import { MarginBadge } from "../components/MarginBadge";
import { SyncButton } from "../components/SyncButton";
import { NinjaOneSyncButton } from "../components/NinjaOneSyncButton";
import { HorizontalBarChart } from "../components/BarChart";
import { CoverageMeter } from "../components/CoverageMeter";
import { SkeletonStatBar, SkeletonTable } from "../components/Skeleton";
import { CustomersIcon, DeviceIcon, ShieldIcon, TrendUpIcon } from "../components/icons";
import type { CustomerSummary, NinjaSyncLog, ReportSummary, SyncLog } from "../api/types";

export function DashboardPage() {
  const [customers, setCustomers] = useState<CustomerSummary[]>([]);
  const [summary, setSummary] = useState<ReportSummary | null>(null);
  const [lastSync, setLastSync] = useState<SyncLog | null>(null);
  const [lastNinjaSync, setLastNinjaSync] = useState<NinjaSyncLog | null>(null);
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
      try {
        setLastNinjaSync(await getNinjaOneSyncStatus());
      } catch {
        setLastNinjaSync(null);
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

  const topMargin = [...customers]
    .filter((c) => c.total_margin !== null)
    .sort((a, b) => Number(b.total_margin) - Number(a.total_margin))
    .slice(0, 8)
    .map((c) => ({ label: c.name, value: Number(c.total_margin) }));

  const coverage = [...customers]
    .filter((c) => (c.device_count ?? 0) > 0)
    .sort((a, b) => (b.device_count ?? 0) - (a.device_count ?? 0))
    .slice(0, 8);

  return (
    <AppShell>
      <div className="page">
        <header className="page-header">
          <div>
            <p className="page-eyebrow">Overview</p>
            <h1>Dashboard</h1>
          </div>
        </header>

        <div className="sync-panel">
          <SyncButton lastSync={lastSync} onSynced={(log) => { setLastSync(log); refresh(); }} />
          <NinjaOneSyncButton lastSync={lastNinjaSync} onSynced={(log) => { setLastNinjaSync(log); refresh(); }} />
          <Link to="/ninjaone-mapping" className="link-button">
            Map unmatched NinjaOne organizations{lastNinjaSync ? ` (${lastNinjaSync.orgs_unmatched})` : ""}
          </Link>
        </div>

        {error && <div className="error-text">{error}</div>}

        {loading && !summary ? (
          <SkeletonStatBar count={4} />
        ) : summary ? (
          <div className="summary-bar">
            <div>
              <span className="summary-label"><CustomersIcon width={14} height={14} /> Customers</span>
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
              <span className="summary-label"><TrendUpIcon width={14} height={14} /> Total margin</span>
              <span className="summary-value">
                <MarginBadge margin={summary.total_margin} marginPct={summary.margin_pct} />
              </span>
            </div>
          </div>
        ) : null}

        {!loading && customers.length > 0 && (
          <div className="charts-grid">
            <div className="chart-card">
              <h2>Top customers by margin</h2>
              <p className="chart-subtitle">Highest total margin, current pricing</p>
              <HorizontalBarChart items={topMargin} formatValue={(v) => formatMoney(String(v))} />
            </div>
            <div className="chart-card">
              <h2>
                <ShieldIcon width={15} height={15} style={{ verticalAlign: "-2px", marginRight: 4 }} />
                SentinelOne coverage
              </h2>
              <p className="chart-subtitle">Share of NinjaOne devices with SentinelOne, by customer</p>
              {coverage.length > 0 ? (
                <div className="bar-chart">
                  {coverage.map((c) => (
                    <CoverageMeter key={c.id} label={c.name} covered={c.sentinelone_count ?? 0} total={c.device_count ?? 0} />
                  ))}
                </div>
              ) : (
                <p className="empty-row">No NinjaOne device data yet.</p>
              )}
            </div>
          </div>
        )}

        {loading ? (
          <SkeletonTable rows={6} cols={7} />
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Customer</th>
                <th># Lines</th>
                <th>Total cost</th>
                <th>Total price</th>
                <th>Margin</th>
                <th><DeviceIcon width={13} height={13} style={{ verticalAlign: "-2px" }} /> Devices</th>
                <th><ShieldIcon width={13} height={13} style={{ verticalAlign: "-2px" }} /> SentinelOne</th>
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
                  <td>{c.device_count ?? "—"}</td>
                  <td>{c.sentinelone_count ?? "—"}</td>
                </tr>
              ))}
              {customers.length === 0 && (
                <tr>
                  <td colSpan={7} className="empty-row">
                    No customers yet — click "Sync Now" to pull data from ION.
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
