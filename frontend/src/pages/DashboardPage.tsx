import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getCustomers, getReportSummary } from "../api/customers";
import { AppShell } from "../components/AppShell";
import { MoneyCell, formatMoney } from "../components/MoneyCell";
import { BytesCell } from "../components/BytesCell";
import { MailboxCoverageCell } from "../components/MailboxCoverageCell";
import { MachineBreakdownCell } from "../components/MachineBreakdownCell";
import { MarginBadge } from "../components/MarginBadge";
import { HorizontalBarChart } from "../components/BarChart";
import { CoverageMeter } from "../components/CoverageMeter";
import { SkeletonStatBar, SkeletonTable } from "../components/Skeleton";
import { useLanguage } from "../i18n/LanguageContext";
import { useSync } from "../sync/SyncContext";
import { CloudIcon, DeviceIcon, ShieldIcon } from "../components/icons";
import type { CustomerSummary, ReportSummary } from "../api/types";

export function DashboardPage() {
  const { t } = useLanguage();
  const { version } = useSync();
  const [customers, setCustomers] = useState<CustomerSummary[]>([]);
  const [summary, setSummary] = useState<ReportSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");

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

  const query = search.trim().toLowerCase();
  const filteredCustomers = query
    ? customers.filter((c) => c.name.toLowerCase().includes(query))
    : customers;

  return (
    <AppShell>
      <div className="dash-page">
        <header className="dash-band">
          <div className="dash-band-inner">
          <div className="dash-band-top">
            <span className="dash-mark">BillingReport</span>
            <label className="dash-search-label">
              {t("dashboard.table.searchLabel")}
              <input
                type="search"
                className="dash-search"
                placeholder={t("dashboard.table.searchPlaceholder")}
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
            </label>
          </div>

          <div className="dash-band-heading">
            <h1 className="dash-title">{t("dashboard.title")}</h1>
            {summary && <span className="dash-client-count">{summary.customer_count} {t("common.customers").toLowerCase()}</span>}
          </div>

          {loading && !summary ? (
            <SkeletonStatBar count={3} />
          ) : summary ? (
            <div className="dash-statement reveal">
              <div className="dash-statement-item">
                <span className="dash-statement-label">{t("common.totalCost")}</span>
                <span className="dash-statement-value"><MoneyCell value={summary.total_cost} /></span>
              </div>
              <div className="dash-statement-item">
                <span className="dash-statement-label">{t("common.totalPrice")}</span>
                <span className="dash-statement-value"><MoneyCell value={summary.total_price} /></span>
              </div>
              <div className="dash-statement-item dash-statement-result">
                <span className="dash-statement-label">{t("common.margin")}</span>
                <span className="dash-statement-value">
                  <MarginBadge margin={summary.total_margin} marginPct={summary.margin_pct} />
                </span>
              </div>
            </div>
          ) : null}
          </div>
        </header>

        <div className="dash-body">
          <div className="dash-body-inner">
          {error && <div className="error-text" role="alert">{error}</div>}

          {!loading && customers.length > 0 && (
            <div className="dash-charts reveal">
              <section className="dash-chart">
                <h2>{t("dashboard.topMargin.title")}</h2>
                <p className="dash-chart-subtitle">{t("dashboard.topMargin.subtitle")}</p>
                <HorizontalBarChart items={topMargin} formatValue={(v) => formatMoney(String(v))} noDataLabel={t("dashboard.topMargin.empty")} />
              </section>
              <section className="dash-chart">
                <h2>
                  <ShieldIcon width={15} height={15} style={{ verticalAlign: "-2px", marginRight: 4 }} />
                  {t("dashboard.coverage.title")}
                </h2>
                <p className="dash-chart-subtitle">{t("dashboard.coverage.subtitle")}</p>
                {coverage.length > 0 ? (
                  <div className="bar-chart">
                    {coverage.map((c, index) => (
                      <CoverageMeter key={c.id} label={c.name} covered={c.sentinelone_count ?? 0} total={c.device_count ?? 0} index={index} />
                    ))}
                  </div>
                ) : (
                  <p className="empty-row">{t("dashboard.coverage.empty")}</p>
                )}
              </section>
            </div>
          )}

          {loading ? (
            <SkeletonTable rows={6} cols={10} />
          ) : (
            <div className="table-scroll reveal">
            <table className="data-table dash-ledger">
              <thead>
                <tr>
                  <th>{t("dashboard.table.customer")}</th>
                  <th className="num">{t("dashboard.table.lines")}</th>
                  <th className="num">{t("common.totalCost")}</th>
                  <th className="num">{t("common.totalPrice")}</th>
                  <th className="num">{t("common.margin")}</th>
                  <th className="num"><DeviceIcon width={13} height={13} style={{ verticalAlign: "-2px" }} /> {t("dashboard.table.devices")}</th>
                  <th className="num"><ShieldIcon width={13} height={13} style={{ verticalAlign: "-2px" }} /> {t("common.sentinelone")}</th>
                  <th className="num"><CloudIcon width={13} height={13} style={{ verticalAlign: "-2px" }} /> {t("common.backupUsedTotal")}</th>
                  <th>{t("dashboard.table.machines")}</th>
                  <th className="num">{t("common.mailboxes")}</th>
                </tr>
              </thead>
              <tbody>
                {filteredCustomers.map((c) => (
                  <tr key={c.id}>
                    <td data-label={t("dashboard.table.customer")}>
                      <Link to={`/customers/${c.id}`} title={!c.ion_customer_id ? t("dashboard.table.ninjaOnlyTooltip") : undefined}>
                        {c.name}
                      </Link>
                    </td>
                    <td className="num" data-label={t("dashboard.table.lines")}>{c.line_count}</td>
                    <td className="num" data-label={t("common.totalCost")}><MoneyCell value={c.total_cost} /></td>
                    <td className="num" data-label={t("common.totalPrice")}><MoneyCell value={c.total_price} /></td>
                    <td className="num" data-label={t("common.margin")}>
                      <MarginBadge margin={c.total_margin} marginPct={c.margin_pct} />
                    </td>
                    <td className="num" data-label={t("dashboard.table.devices")}>{c.device_count ?? "—"}</td>
                    <td className="num" data-label={t("common.sentinelone")}>{c.sentinelone_count ?? "—"}</td>
                    <td className="num" data-label={t("common.backupUsedTotal")}>
                      {c.backup_used_bytes !== null ? (
                        <>
                          <BytesCell value={c.backup_used_bytes} /> / <BytesCell value={c.backup_total_bytes} />
                        </>
                      ) : (
                        "—"
                      )}
                    </td>
                    <td data-label={t("dashboard.table.machines")}>
                      <MachineBreakdownCell
                        serverCount={c.backup_server_count}
                        workstationCount={c.backup_workstation_count}
                        vmCount={c.backup_vm_count}
                      />
                    </td>
                    <td className="num" data-label={t("common.mailboxes")}>
                      <MailboxCoverageCell backedUp={c.backup_mailboxes_count} />
                    </td>
                  </tr>
                ))}
                {filteredCustomers.length === 0 && (
                  <tr>
                    <td colSpan={10} className="empty-row">
                      {customers.length === 0 ? t("dashboard.table.empty") : t("dashboard.table.noMatches")}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
            </div>
          )}
          </div>
        </div>
      </div>
    </AppShell>
  );
}
