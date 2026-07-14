interface BarChartItem {
  label: string;
  value: number;
  sublabel?: string;
}

export function HorizontalBarChart({
  items,
  formatValue,
  maxValue,
}: {
  items: BarChartItem[];
  formatValue: (value: number) => string;
  maxValue?: number;
}) {
  const max = maxValue ?? Math.max(...items.map((i) => i.value), 1);

  return (
    <div className="bar-chart">
      {items.map((item) => {
        const pct = max > 0 ? Math.max((item.value / max) * 100, item.value > 0 ? 2 : 0) : 0;
        return (
          <div className="bar-row" key={item.label} tabIndex={0}>
            <span className="bar-label" title={item.label}>
              {item.label}
            </span>
            <div className="bar-track">
              <div className="bar-fill" style={{ width: `${pct}%` }} />
            </div>
            <span className="bar-value">{formatValue(item.value)}</span>
            <div className="bar-tooltip" role="tooltip">
              <strong>{formatValue(item.value)}</strong>
              <span>{item.label}</span>
              {item.sublabel && <span className="bar-tooltip-sub">{item.sublabel}</span>}
            </div>
          </div>
        );
      })}
      {items.length === 0 && <p className="empty-row">No data yet.</p>}
    </div>
  );
}
