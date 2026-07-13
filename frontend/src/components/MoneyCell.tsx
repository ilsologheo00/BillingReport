export function formatMoney(value: string | null): string {
  if (value === null) return "—";
  const num = Number(value);
  return num.toLocaleString(undefined, { style: "currency", currency: "USD" });
}

export function MoneyCell({ value }: { value: string | null }) {
  return <span>{formatMoney(value)}</span>;
}
