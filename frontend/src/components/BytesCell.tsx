const UNITS = ["B", "KB", "MB", "GB", "TB", "PB"];

export function formatBytes(value: string | null): string {
  if (value === null) return "—";
  let num = Number(value);
  if (num === 0) return "0 B";
  let unitIndex = 0;
  while (num >= 1024 && unitIndex < UNITS.length - 1) {
    num /= 1024;
    unitIndex += 1;
  }
  return `${num.toLocaleString(undefined, { maximumFractionDigits: 1 })} ${UNITS[unitIndex]}`;
}

export function BytesCell({ value }: { value: string | null }) {
  return <span>{formatBytes(value)}</span>;
}
