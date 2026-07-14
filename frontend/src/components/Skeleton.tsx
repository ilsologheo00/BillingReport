export function SkeletonBlock({ height = 16, width = "100%" }: { height?: number; width?: number | string }) {
  return <div className="skeleton" style={{ height, width }} />;
}

export function SkeletonTable({ rows = 5, cols = 5 }: { rows?: number; cols?: number }) {
  return (
    <div className="data-table skeleton-table">
      {Array.from({ length: rows }).map((_, r) => (
        <div className="skeleton-table-row" key={r}>
          {Array.from({ length: cols }).map((_, c) => (
            <SkeletonBlock key={c} height={14} />
          ))}
        </div>
      ))}
    </div>
  );
}

export function SkeletonStatBar({ count = 4 }: { count?: number }) {
  return (
    <div className="summary-bar">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} style={{ flex: 1 }}>
          <SkeletonBlock height={11} width="60%" />
          <div style={{ height: 8 }} />
          <SkeletonBlock height={22} width="45%" />
        </div>
      ))}
    </div>
  );
}
