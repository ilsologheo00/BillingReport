import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getCustomer } from "../api/customers";
import { updatePrice } from "../api/prices";
import { AppShell } from "../components/AppShell";
import { MoneyCell } from "../components/MoneyCell";
import { BytesCell } from "../components/BytesCell";
import { MarginBadge } from "../components/MarginBadge";
import { SkeletonStatBar, SkeletonTable } from "../components/Skeleton";
import { useLanguage } from "../i18n/LanguageContext";
import type { CustomerDetail, LicenseLine } from "../api/types";

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
              <div>
                <span className="summary-label">{t("common.devices")}</span>
                <span className="summary-value">{customer.device_count ?? "—"}</span>
              </div>
              <div>
                <span className="summary-label">{t("common.sentinelone")}</span>
                <span className="summary-value">{customer.sentinelone_count ?? "—"}</span>
              </div>
              <div>
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
              <div>
                <span className="summary-label">{t("common.backupAvailable")}</span>
                <span className="summary-value"><BytesCell value={customer.backup_available_bytes} /></span>
              </div>
              <div>
                <span className="summary-label">{t("customerDetail.backedUpMachines")}</span>
                <span className="summary-value">{customer.backup_machines_count ?? "—"}</span>
              </div>
              <div>
                <span className="summary-label">{t("customerDetail.backedUpMailboxes")}</span>
                <span className="summary-value">{customer.backup_mailboxes_count ?? "—"}</span>
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
