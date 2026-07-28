import { useLanguage } from "../i18n/LanguageContext";

export function MachineBreakdownCell({
  serverCount,
  workstationCount,
  vmCount,
}: {
  serverCount: number | null;
  workstationCount: number | null;
  vmCount: number | null;
}) {
  const { t } = useLanguage();
  const server = serverCount ?? 0;
  const workstation = workstationCount ?? 0;
  const vm = vmCount ?? 0;
  if (!server && !workstation && !vm) return <span>—</span>;
  return (
    <span title={t("machineBreakdown.tooltip")}>
      {t("machineBreakdown.compact", { server, workstation, vm })}
    </span>
  );
}
