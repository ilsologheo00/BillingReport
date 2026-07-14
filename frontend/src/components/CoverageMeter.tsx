export function CoverageMeter({
  label,
  covered,
  total,
}: {
  label: string;
  covered: number;
  total: number;
}) {
  const pct = total > 0 ? Math.round((covered / total) * 100) : 0;

  return (
    <div className="meter-row" tabIndex={0}>
      <span className="bar-label" title={label}>
        {label}
      </span>
      <div className="meter-track">
        <div className="meter-fill" style={{ width: `${pct}%` }} />
      </div>
      <span className="bar-value">{pct}%</span>
      <div className="bar-tooltip" role="tooltip">
        <strong>
          {covered} / {total}
        </strong>
        <span>{label}</span>
        <span className="bar-tooltip-sub">devices with SentinelOne</span>
      </div>
    </div>
  );
}
