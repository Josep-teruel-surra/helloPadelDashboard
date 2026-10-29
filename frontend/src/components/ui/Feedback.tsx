import { CircleAlert } from "lucide-react";
import type { ReactNode } from "react";

import { errorMessage } from "@/api/client";
import { cn } from "@/lib/cn";

/** Muestra un error de la API, o directamente un texto. */
export function ErrorAlert({ error, className }: { error: unknown; className?: string }) {
  if (!error) return null;
  return (
    <div
      role="alert"
      className={cn(
        "flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-800",
        className,
      )}
    >
      <CircleAlert className="mt-0.5 size-4 shrink-0" aria-hidden />
      <span>{typeof error === "string" ? error : errorMessage(error)}</span>
    </div>
  );
}

interface EmptyStateProps {
  icon: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
}

export function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center gap-2 rounded-xl border border-dashed border-stone-300 px-6 py-12 text-center">
      <div className="text-stone-400">{icon}</div>
      <p className="font-semibold text-stone-800">{title}</p>
      {description && <p className="max-w-sm text-sm text-stone-500">{description}</p>}
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}

type BadgeTone = "neutral" | "brand" | "red" | "amber" | "green" | "blue";

const TONES: Record<BadgeTone, string> = {
  neutral: "bg-stone-100 text-stone-700",
  brand: "bg-brand/30 text-stone-900",
  red: "bg-red-100 text-red-800",
  amber: "bg-amber-100 text-amber-900",
  green: "bg-emerald-100 text-emerald-800",
  blue: "bg-sky-100 text-sky-800",
};

export function Badge({ tone = "neutral", children }: { tone?: BadgeTone; children: ReactNode }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-xs font-medium whitespace-nowrap",
        TONES[tone],
      )}
    >
      {children}
    </span>
  );
}
