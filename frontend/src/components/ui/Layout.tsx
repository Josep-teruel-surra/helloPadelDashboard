import { ArrowRight } from "lucide-react";
import type { ReactNode } from "react";
import { Link } from "react-router";

import { cn } from "@/lib/cn";

export function PageHeader({
  title,
  description,
  actions,
}: {
  title: string;
  description?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="text-2xl font-extrabold tracking-tight">{title}</h1>
        {description && <p className="mt-1 text-sm text-stone-500">{description}</p>}
      </div>
      {actions && <div className="flex gap-2">{actions}</div>}
    </div>
  );
}

export function Card({
  title,
  icon,
  actions,
  children,
  className,
}: {
  title?: string;
  icon?: ReactNode;
  actions?: ReactNode;
  children: ReactNode;
  className?: string;
}) {
  return (
    <section
      className={cn("min-w-0 rounded-2xl border border-stone-200 bg-white p-4 sm:p-5", className)}
    >
      {(title || actions) && (
        <div className="mb-3 flex items-center justify-between gap-2">
          {title && (
            <h2 className="flex min-w-0 items-center gap-2 text-sm font-bold tracking-wide whitespace-nowrap text-stone-500 uppercase">
              {icon}
              {title}
            </h2>
          )}
          {actions}
        </div>
      )}
      {children}
    </section>
  );
}

interface SegmentedOption<T extends string> {
  value: T;
  label: string;
}

export function Segmented<T extends string>({
  options,
  value,
  onChange,
  label,
}: {
  options: SegmentedOption<T>[];
  value: T;
  onChange: (value: T) => void;
  label: string;
}) {
  return (
    <div role="radiogroup" aria-label={label} className="inline-flex rounded-lg bg-stone-200/70 p-1">
      {options.map((option) => (
        <button
          key={option.value}
          type="button"
          role="radio"
          aria-checked={value === option.value}
          onClick={() => onChange(option.value)}
          className={cn(
            "rounded-md px-3 py-1.5 text-sm font-semibold transition-colors",
            value === option.value
              ? "bg-white text-stone-900 shadow-sm"
              : "text-stone-600 hover:text-stone-900",
          )}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}

/** Enlace "Ver todas →" para la cabecera de una tarjeta. */
export function SeeAll({ to, children }: { to: string; children: ReactNode }) {
  return (
    <Link
      to={to}
      className="inline-flex shrink-0 items-center gap-1 text-xs font-semibold whitespace-nowrap text-stone-500 hover:text-stone-900"
    >
      {children}
      <ArrowRight className="size-3.5" aria-hidden />
    </Link>
  );
}

