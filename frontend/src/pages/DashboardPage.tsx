import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getCustomers, getReportSummary } from "../api/customers";
import { AppShell } from "../components/AppShell";
import { MoneyCell, formatMoney } from "../components/MoneyCell";
import { BytesCell } from "../components/BytesCell";
import { MarginBadge } from "../components/MarginBadge";
import { HorizontalBarChart } from "../components/BarChart";
import { CoverageMeter } from "../components/CoverageMeter";
import { SkeletonStatBar, SkeletonTable } from "../components/Skeleton";
import { useLanguage } from "../i18n/LanguageContext";
import { useSync } from "../sync/SyncContext";
import { CloudIcon, CustomersIcon, DeviceIcon, ShieldIcon, TrendUpIcon } from "../components/icons";
import type { CustomerSummary, ReportSummary } from "../api/types";

export function DashboardPage() {
  const { t } = useLanguage();
  const { version } = useSync();
  const [customers, setCustomers] = useState<CustomerSummary[]>([]);
  const [summary, setSummary] = useState<ReportSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    setLoading(true);
    setError(null);
    try {
      const [customerList, reportSummary] = await Promise.all([getCustomers(), getReportSummary()]);
      setCustomers(customerList);
      setSummary(reportSummary);
    } catch (err) {
      setError(err instanceof Error ? err.message : t("common.failedToLoadData"));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
    // Re-fetch whenever a sync completes anywhere in the app (buttons live in the sidebar now, not on this page).
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [version]);

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
            <p className="page-eyebrow">{t("dashboard.eyebrow")}</p>
            <h1>{t("dashboard.title")}</h1>
          </div>
        </header>

        {error && <div className="error-text">{error}</div>}

        {loading && !summary ? (
          <SkeletonStatBar count={4} />
        ) : summary ? (
          <div className="summary-bar">
            <div>
              <span className="summary-label"><CustomersIcon width={14} height={14} /> {t("common.customers")}</span>
              <span className="summary-value">{summary.customer_count}</span>
            </div>
            <div>
              <span className="summary-label">{t("common.totalCost")}</span>
              <span className="summary-value"><MoneyCell value={summary.total_cost} /></span>
            </div>
            <div>
              <span className="summary-label">{t("common.totalPrice")}</span>
              <span className="summary-value"><MoneyCell value={summary.total_price} /></span>
            </div>
            <div>
              <span className="summary-label"><TrendUpIcon width={14} height={14} /> {t("dashboard.totalMargin")}</span>
              <span className="summary-value">
                <MarginBadge margin={summary.total_margin} marginPct={summary.margin_pct} />
              </span>
            </div>
          </div>
        ) : null}

        {!loading && customers.length > 0 && (
          <div className="charts-grid">
            <div className="chart-card">
              <h2>{t("dashboard.topMargin.title")}</h2>
              <p className="chart-subtitle">{t("dashboard.topMargin.subtitle")}</p>
              <HorizontalBarChart items={topMargin} formatValue={(v) => formatMoney(String(v))} noDataLabel={t("dashboard.topMargin.empty")} />
            </div>
            <div className="chart-card">
              <h2>
                <ShieldIcon width={15} height={15} style={{ verticalAlign: "-2px", marginRight: 4 }} />
                {t("dashboard.coverage.title")}
              </h2>
              <p className="chart-subtitle">{t("dashboard.coverage.subtitle")}</p>
              {coverage.length > 0 ? (
                <div className="bar-chart">
                  {coverage.map((c) => (
                    <CoverageMeter key={c.id} label={c.name} covered={c.sentinelone_count ?? 0} total={c.device_count ?? 0} />
                  ))}
                </div>
              ) : (
                <p className="empty-row">{t("dashboard.coverage.empty")}</p>
              )}
            </div>
          </div>
        )}

        {loading ? (
          <SkeletonTable rows={6} cols={10} />
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>{t("dashboard.table.customer")}</th>
                <th>{t("dashboard.table.lines")}</th>
                <th>{t("common.totalCost")}</th>
                <th>{t("common.totalPrice")}</th>
                <th>{t("common.margin")}</th>
                <th><DeviceIcon width={13} height={13} style={{ verticalAlign: "-2px" }} /> {t("common.devices")}</th>
                <th><ShieldIcon width={13} height={13} style={{ verticalAlign: "-2px" }} /> {t("common.sentinelone")}</th>
                <th><CloudIcon width={13} height={13} style={{ verticalAlign: "-2px" }} /> {t("common.backupUsedTotal")}</th>
                <th>{t("common.machines")}</th>
                <th>{t("common.mailboxes")}</th>
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
                  <td>
                    {c.backup_used_bytes !== null ? (
                      <>
                        <BytesCell value={c.backup_used_bytes} /> / <BytesCell value={c.backup_total_bytes} />
                      </>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td>{c.backup_machines_count ?? "—"}</td>
                  <td>{c.backup_mailboxes_count ?? "—"}</td>
                </tr>
              ))}
              {customers.length === 0 && (
                <tr>
                  <td colSpan={10} className="empty-row">
                    {t("dashboard.table.empty")}
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
