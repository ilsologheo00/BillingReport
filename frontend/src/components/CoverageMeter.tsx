import { useId } from "react";

export function CoverageMeter({
  label,
  covered,
  total,
  index = 0,
}: {
  label: string;
  covered: number;
  total: number;
  index?: number;
}) {
  const pct = total > 0 ? Math.round((covered / total) * 100) : 0;
  const tooltipId = useId();

  return (
    <div
      className="meter-row"
      tabIndex={0}
      aria-describedby={tooltipId}
      style={{ animationDelay: `${Math.min(index, 8) * 30}ms` }}
    >
      <span className="bar-label" title={label}>
        {label}
      </span>
      <div className="meter-track">
        <div className="meter-fill" style={{ width: `${pct}%` }} />
      </div>
      <span className="bar-value">{pct}%</span>
      <div className="bar-tooltip" role="tooltip" id={tooltipId}>
        <strong>
          {covered} / {total}
        </strong>
        <span>{label}</span>
        <span className="bar-tooltip-sub">devices with SentinelOne</span>
      </div>
    </div>
  );
}
