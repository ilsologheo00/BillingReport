import { useLanguage } from "../i18n/LanguageContext";

export function MarginBadge({ margin, marginPct }: { margin: string | null; marginPct: string | null }) {
  const { t } = useLanguage();
  if (margin === null) {
    return <span className="badge badge-neutral">{t("common.notSet")}</span>;
  }
  const numMargin = Number(margin);
  const cls = numMargin > 0 ? "badge badge-positive" : numMargin < 0 ? "badge badge-negative" : "badge badge-neutral";
  const pct = marginPct !== null ? ` (${Number(marginPct).toFixed(1)}%)` : "";
  return (
    <span className={cls}>
      {numMargin.toLocaleString(undefined, { style: "currency", currency: "EUR" })}
      {pct}
    </span>
  );
}
