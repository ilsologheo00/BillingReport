import { useLanguage } from "../i18n/LanguageContext";

export function SkeletonBlock({ height = 16, width = "100%" }: { height?: number; width?: number | string }) {
  return <div className="skeleton" style={{ height, width }} />;
}

export function SkeletonTable({ rows = 5, cols = 5 }: { rows?: number; cols?: number }) {
  const { t } = useLanguage();
  return (
    <div className="data-table skeleton-table" role="status" aria-busy="true">
      <span className="sr-only">{t("common.loading")}</span>
      {Array.from({ length: rows }).map((_, r) => (
        <div className="skeleton-table-row" key={r} aria-hidden="true">
          {Array.from({ length: cols }).map((_, c) => (
            <SkeletonBlock key={c} height={14} />
          ))}
        </div>
      ))}
    </div>
  );
}

export function SkeletonStatBar({ count = 4 }: { count?: number }) {
  const { t } = useLanguage();
  return (
    <div className="summary-bar" role="status" aria-busy="true">
      <span className="sr-only">{t("common.loading")}</span>
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} style={{ flex: 1 }} aria-hidden="true">
          <SkeletonBlock height={11} width="60%" />
          <div style={{ height: 8 }} />
          <SkeletonBlock height={22} width="45%" />
        </div>
      ))}
    </div>
  );
}
