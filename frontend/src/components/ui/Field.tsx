import type { ReactNode } from "react";

import { cn } from "@/lib/cn";

export const inputClass = cn(
  "block w-full rounded-lg border border-stone-300 bg-white px-3 py-2 text-sm text-stone-900",
  "placeholder:text-stone-400 focus:border-amber-500 focus:ring-2 focus:ring-brand/60 focus:outline-none",
  "disabled:bg-stone-100 disabled:text-stone-500",
);

/** Para selects de filtro en una fila: mismo estilo, pero solo el ancho de su contenido. */
export const inlineSelectClass = inputClass.replace("w-full", "w-auto max-w-full");

interface FieldProps {
  label: string;
  htmlFor: string;
  hint?: string;
  children: ReactNode;
  className?: string;
}

export function Field({ label, htmlFor, hint, children, className }: FieldProps) {
  return (
    <div className={cn("space-y-1.5", className)}>
      <label htmlFor={htmlFor} className="block text-sm font-medium text-stone-700">
        {label}
      </label>
      {children}
      {hint && <p className="text-xs text-stone-500">{hint}</p>}
    </div>
  );
}
