import { useLanguage } from "../i18n/LanguageContext";

export function MailboxCoverageCell({ backedUp, licensed }: { backedUp: number | null; licensed: number }) {
  const { t } = useLanguage();
  if (!backedUp && !licensed) return <span>—</span>;
  return (
    <span title={t("common.mailboxesTooltip")}>
      {backedUp ?? 0} / {licensed}
    </span>
  );
}
