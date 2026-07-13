import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { getCustomer } from "../api/customers";
import { updatePrice } from "../api/prices";
import { MoneyCell } from "../components/MoneyCell";
import { MarginBadge } from "../components/MarginBadge";
import type { CustomerDetail, LicenseLine } from "../api/types";

function PriceCell({ customerId, line, onUpdated }: { customerId: number; line: LicenseLine; onUpdated: () => void }) {
  const [value, setValue] = useState(line.unit_price ?? "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function save() {
    if (value === "" || Number.isNaN(Number(value))) {
      setError("Enter a valid number");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await updatePrice(customerId, line.sku, value);
      onUpdated();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save");
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
        placeholder="Set price"
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
  const { id } = useParams<{ id: string }>();
  const customerId = Number(id);
  const [customer, setCustomer] = useState<CustomerDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    setError(null);
    try {
      setCustomer(await getCustomer(customerId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load customer");
    }
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [customerId]);

  if (error) return <div className="page error-text">{error}</div>;
  if (!customer) return <div className="page">Loading…</div>;

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <Link to="/" className="link-button">
            ← Back
          </Link>
          <h1>{customer.name}</h1>
        </div>
      </header>

      <div className="summary-bar">
        <div>
          <span className="summary-label">Total cost</span>
          <span className="summary-value"><MoneyCell value={customer.total_cost} /></span>
        </div>
        <div>
          <span className="summary-label">Total price</span>
          <span className="summary-value"><MoneyCell value={customer.total_price} /></span>
        </div>
        <div>
          <span className="summary-label">Margin</span>
          <span className="summary-value">
            <MarginBadge margin={customer.total_margin} marginPct={customer.margin_pct} />
          </span>
        </div>
      </div>

      <table className="data-table">
        <thead>
          <tr>
            <th>Product</th>
            <th>Vendor</th>
            <th>SKU</th>
            <th>Qty</th>
            <th>Unit cost</th>
            <th>Unit price</th>
            <th>Margin</th>
            <th>Billing</th>
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
                No license lines for this customer.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}
