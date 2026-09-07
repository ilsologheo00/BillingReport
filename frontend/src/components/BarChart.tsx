import { useId } from "react";

interface BarChartItem {
  label: string;
  value: number;
  sublabel?: string;
}

function BarRow({ item, pct, formatValue }: { item: BarChartItem; pct: number; formatValue: (value: number) => string }) {
  const tooltipId = useId();
  return (
    <div className="bar-row" tabIndex={0} aria-describedby={tooltipId}>
      <span className="bar-label" title={item.label}>
        {item.label}
      </span>
      <div className="bar-track">
        <div className="bar-fill" style={{ width: `${pct}%` }} />
      </div>
      <span className="bar-value">{formatValue(item.value)}</span>
      <div className="bar-tooltip" role="tooltip" id={tooltipId}>
        <strong>{formatValue(item.value)}</strong>
        <span>{item.label}</span>
        {item.sublabel && <span className="bar-tooltip-sub">{item.sublabel}</span>}
      </div>
    </div>
  );
}

export function HorizontalBarChart({
  items,
  formatValue,
  maxValue,
  noDataLabel = "No data yet.",
}: {
  items: BarChartItem[];
  formatValue: (value: number) => string;
  maxValue?: number;
  noDataLabel?: string;
}) {
  const max = maxValue ?? Math.max(...items.map((i) => i.value), 1);

  return (
    <div className="bar-chart">
      {items.map((item) => {
        const pct = max > 0 ? Math.max((item.value / max) * 100, item.value > 0 ? 2 : 0) : 0;
        return <BarRow key={item.label} item={item} pct={pct} formatValue={formatValue} />;
      })}
      {items.length === 0 && <p className="empty-row">{noDataLabel}</p>}
    </div>
  );
}
