import { useLanguage } from "../i18n/LanguageContext";

export function MailboxCoverageCell({ backedUp }: { backedUp: number | null }) {
  const { t } = useLanguage();
  if (!backedUp) return <span>—</span>;
  return <span title={t("common.mailboxesTooltip")}>{backedUp}</span>;
}
