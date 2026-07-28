import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getCustomer, getCustomers, mergeCustomers } from "../api/customers";
import { updatePrice } from "../api/prices";
import { AppShell } from "../components/AppShell";
import { MoneyCell } from "../components/MoneyCell";
import { BytesCell } from "../components/BytesCell";
import { MailboxCoverageCell } from "../components/MailboxCoverageCell";
import { MarginBadge } from "../components/MarginBadge";
import { SkeletonStatBar, SkeletonTable } from "../components/Skeleton";
import { useLanguage } from "../i18n/LanguageContext";
import type { CustomerDetail, CustomerSummary, LicenseLine } from "../api/types";

function MergeControl({ customer, onMerged }: { customer: CustomerDetail; onMerged: () => void }) {
  const { t } = useLanguage();
  const [candidates, setCandidates] = useState<CustomerSummary[]>([]);
  const [otherId, setOtherId] = useState("");
  const [merging, setMerging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getCustomers()
      .then((all) => setCandidates(all.filter((c) => c.id !== customer.id)))
      .catch(() => {});
  }, [customer.id]);

  async function merge() {
    if (!otherId) return;
    const other = candidates.find((c) => String(c.id) === otherId);
    if (!other) return;
    if (!window.confirm(t("customerDetail.merge.confirm", { name: other.name }))) return;

    setMerging(true);
    setError(null);
    try {
      await mergeCustomers(customer.id, Number(otherId));
      setOtherId("");
      onMerged();
    } catch (err) {
      setError(err instanceof Error ? err.message : t("customerDetail.failedToSave"));
    } finally {
      setMerging(false);
    }
  }

  if (candidates.length === 0) return null;

  return (
    <div className="merge-control">
      <span>{t("customerDetail.merge.label")}</span>
      <select value={otherId} onChange={(e) => setOtherId(e.target.value)} disabled={merging}>
        <option value="">{t("customerDetail.merge.select")}</option>
        {candidates.map((c) => (
          <option key={c.id} value={c.id}>
            {c.name}
          </option>
        ))}
      </select>
      <button onClick={merge} disabled={merging || !otherId}>
        {merging ? t("customerDetail.merge.merging") : t("customerDetail.merge.button")}
      </button>
      {error && <span className="error-text small">{error}</span>}
    </div>
  );
}

function PriceCell({ customerId, line, onUpdated }: { customerId: number; line: LicenseLine; onUpdated: () => void }) {
  const { t } = useLanguage();
  const [value, setValue] = useState(line.unit_price ?? "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function save() {
    if (value === "" || Number.isNaN(Number(value))) {
      setError(t("customerDetail.enterValidNumber"));
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await updatePrice(customerId, line.sku, value);
      onUpdated();
    } catch (err) {
      setError(err instanceof Error ? err.message : t("customerDetail.failedToSave"));
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="price-cell">
      <input
        type="number"
        step="0.01"
        value={value}
        placeholder={t("customerDetail.setPricePlaceholder")}
        onChange={(e) => setValue(e.target.value)}
        onBlur={save}
        onKeyDown={(e) => {
          if (e.key === "Enter") (e.target as HTMLInputElement).blur();
        }}
        disabled={saving}
      />
      {error && <span className="error-text small">{error}</span>}
    </div>
  );
}

export function CustomerDetailPage() {
  const { t } = useLanguage();
  const { id } = useParams<{ id: string }>();
  const customerId = Number(id);
  const [customer, setCustomer] = useState<CustomerDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    setError(null);
    try {
      setCustomer(await getCustomer(customerId));
    } catch (err) {
      setError(err instanceof Error ? err.message : t("customerDetail.failedToLoadCustomer"));
    }
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [customerId]);

  if (error) {
    return (
      <AppShell>
        <div className="page error-text">{error}</div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="page">
        <header className="page-header">
          <div>
            <Link to="/" className="link-button">
              {t("common.back")}
            </Link>
            <h1>{customer?.name ?? t("common.loading")}</h1>
          </div>
          {customer && <MergeControl customer={customer} onMerged={refresh} />}
        </header>

        {!customer ? (
          <>
            <SkeletonStatBar count={5} />
            <SkeletonTable rows={5} cols={8} />
          </>
        ) : (
          <>
            <div className="summary-bar">
              <div>
                <span className="summary-label">{t("common.totalCost")}</span>
                <span className="summary-value"><MoneyCell value={customer.total_cost} /></span>
              </div>
              <div>
                <span className="summary-label">{t("common.totalPrice")}</span>
                <span className="summary-value"><MoneyCell value={customer.total_price} /></span>
              </div>
              <div>
                <span className="summary-label">{t("common.margin")}</span>
                <span className="summary-value">
                  <MarginBadge margin={customer.total_margin} marginPct={customer.margin_pct} />
                </span>
              </div>
            </div>

            <div className="charts-grid">
              <div className="chart-card">
                <h2>{t("customerDetail.ninjaone.title")}</h2>
                <div className="card-stat">
                  <span className="summary-label">{t("common.devices")}</span>
                  <span className="summary-value">{customer.device_count ?? "—"}</span>
                </div>
              </div>

              <div className="chart-card">
                <h2>{t("customerDetail.sentinelone.title")}</h2>
                <div className="card-stat">
                  <span className="summary-label">{t("customerDetail.sentinelone.protected")}</span>
                  <span className="summary-value">
                    {customer.sentinelone_count ?? "—"}{customer.device_count ? ` / ${customer.device_count}` : ""}
                  </span>
                </div>
              </div>

              <div className="chart-card">
                <h2>{t("customerDetail.acronis.title")}</h2>
                <div className="card-stat">
                  <span className="summary-label">{t("common.backupUsedTotal")}</span>
                  <span className="summary-value">
                    {customer.backup_used_bytes !== null ? (
                      <>
                        <BytesCell value={customer.backup_used_bytes} /> / <BytesCell value={customer.backup_total_bytes} />
                      </>
                    ) : (
                      "—"
                    )}
                  </span>
                </div>
                <div className="card-stat">
                  <span className="summary-label">{t("common.backupAvailable")}</span>
                  <span className="summary-value"><BytesCell value={customer.backup_available_bytes} /></span>
                </div>
                <div className="card-stat">
                  <span className="summary-label">{t("customerDetail.backedUpServers")}</span>
                  <span className="summary-value">{customer.backup_server_count ?? "—"}</span>
                </div>
                <div className="card-stat">
                  <span className="summary-label">{t("customerDetail.backedUpWorkstations")}</span>
                  <span className="summary-value">{customer.backup_workstation_count ?? "—"}</span>
                </div>
                <div className="card-stat">
                  <span className="summary-label">{t("customerDetail.backedUpVms")}</span>
                  <span className="summary-value">{customer.backup_vm_count ?? "—"}</span>
                </div>
                <div className="card-stat">
                  <span className="summary-label">{t("customerDetail.backedUpMailboxes")}</span>
                  <span className="summary-value">
                    <MailboxCoverageCell backedUp={customer.backup_mailboxes_count} />
                  </span>
                </div>
              </div>
            </div>

            <table className="data-table">
              <thead>
                <tr>
                  <th>{t("customerDetail.table.product")}</th>
                  <th>{t("customerDetail.table.vendor")}</th>
                  <th>{t("customerDetail.table.sku")}</th>
                  <th>{t("customerDetail.table.qty")}</th>
                  <th>{t("customerDetail.table.unitCost")}</th>
                  <th>{t("customerDetail.table.unitPrice")}</th>
                  <th>{t("common.margin")}</th>
                  <th>{t("customerDetail.table.billing")}</th>
                </tr>
              </thead>
              <tbody>
                {customer.license_lines.map((line) => (
                  <tr key={line.id}>
                    <td>{line.product_name}</td>
                    <td>{line.vendor}</td>
                    <td>{line.sku}</td>
                    <td>{line.quantity}</td>
                    <td><MoneyCell value={line.unit_cost} /></td>
                    <td>
                      <PriceCell customerId={customer.id} line={line} onUpdated={refresh} />
                    </td>
                    <td>
                      <MarginBadge margin={line.total_margin} marginPct={line.margin_pct} />
                    </td>
                    <td>{line.billing_period ?? "—"}</td>
                  </tr>
                ))}
                {customer.license_lines.length === 0 && (
                  <tr>
                    <td colSpan={8} className="empty-row">
                      {t("customerDetail.noLines")}
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </>
        )}
      </div>
    </AppShell>
  );
}
