export function MarginBadge({ margin, marginPct }: { margin: string | null; marginPct: string | null }) {
  if (margin === null) {
    return <span className="badge badge-neutral">not set</span>;
  }
  const numMargin = Number(margin);
  const cls = numMargin > 0 ? "badge badge-positive" : numMargin < 0 ? "badge badge-negative" : "badge badge-neutral";
  const pct = marginPct !== null ? ` (${Number(marginPct).toFixed(1)}%)` : "";
  return (
    <span className={cls}>
      {numMargin.toLocaleString(undefined, { style: "currency", currency: "USD" })}
      {pct}
    </span>
  );
}
