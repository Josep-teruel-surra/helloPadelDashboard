const LOCALE = "es-ES";

/** "2026-11-07" → Date local a medianoche (evita el desfase de zona horaria de `new Date(iso)`). */
export function parseLocalDate(isoDate: string): Date {
  const [y, m, d] = isoDate.split("-").map(Number);
  return new Date(y ?? 1970, (m ?? 1) - 1, d ?? 1);
}

export function todayISO(): string {
  const now = new Date();
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
}

export function formatDate(isoDate: string): string {
  const date = parseLocalDate(isoDate);
  const sameYear = date.getFullYear() === new Date().getFullYear();
  return date.toLocaleDateString(LOCALE, {
    day: "numeric",
    month: "short",
    ...(sameYear ? {} : { year: "numeric" }),
  });
}

export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString(LOCALE, {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

const relative = new Intl.RelativeTimeFormat(LOCALE, { numeric: "auto" });

export function relativeTime(iso: string): string {
  const seconds = (new Date(iso).getTime() - Date.now()) / 1000;
  const abs = Math.abs(seconds);
  if (abs < 60) return "ahora mismo";
  if (abs < 3600) return relative.format(Math.round(seconds / 60), "minute");
  if (abs < 86400) return relative.format(Math.round(seconds / 3600), "hour");
  if (abs < 7 * 86400) return relative.format(Math.round(seconds / 86400), "day");
  return formatDateTime(iso);
}

export type DueStatus = "overdue" | "today" | "upcoming";

export function dueStatus(dueDate: string | null, isDone: boolean): DueStatus | null {
  if (!dueDate || isDone) return null;
  const today = todayISO();
  if (dueDate < today) return "overdue";
  if (dueDate === today) return "today";
  return "upcoming";
}

/** Texto plano aproximado de un markdown, para extractos. */
export function markdownExcerpt(markdown: string, maxLength = 160): string {
  const text = markdown
    .replace(/```[\s\S]*?```/g, " ")
    .replace(/^\s*\|?[\s:|-]+\|[\s:|-]*$/gm, " ") // separadores de tabla
    .replace(/\|/g, " ")
    .replace(/!\[[^\]]*\]\([^)]*\)/g, " ")
    .replace(/\[([^\]]*)\]\([^)]*\)/g, "$1")
    .replace(/^\s{0,3}(#{1,6}|>|[-*+]|\d+\.)\s+/gm, "")
    .replace(/[*_`~]/g, "")
    .replace(/\s+/g, " ")
    .trim();
  return text.length > maxLength ? `${text.slice(0, maxLength).trimEnd()}…` : text;
}
