import { LoaderCircle } from "lucide-react";
import type { ButtonHTMLAttributes } from "react";

import { cn } from "@/lib/cn";

type Variant = "primary" | "secondary" | "danger" | "ghost";
type Size = "sm" | "md";

const VARIANTS: Record<Variant, string> = {
  primary: "bg-brand text-carbon hover:bg-brand-dark",
  secondary: "border border-stone-300 bg-white text-stone-800 hover:bg-stone-50",
  danger: "bg-red-600 text-white hover:bg-red-700",
  ghost: "text-stone-600 hover:bg-stone-200/70 hover:text-stone-900",
};

const SIZES: Record<Size, string> = {
  sm: "h-8 gap-1.5 px-2.5 text-sm",
  md: "h-10 gap-2 px-4 text-sm",
};

export function buttonClass(variant: Variant = "primary", size: Size = "md"): string {
  return cn(
    "inline-flex shrink-0 items-center justify-center rounded-lg font-semibold transition-colors",
    "disabled:cursor-not-allowed disabled:opacity-50",
    VARIANTS[variant],
    SIZES[size],
  );
}

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: Variant;
  size?: Size;
  loading?: boolean;
}

export function Button({
  variant = "primary",
  size = "md",
  loading = false,
  disabled,
  className,
  children,
  type = "button",
  ...props
}: ButtonProps) {
  return (
    <button
      type={type}
      disabled={disabled || loading}
      className={cn(buttonClass(variant, size), className)}
      {...props}
    >
      {loading && <LoaderCircle className="size-4 animate-spin" aria-hidden />}
      {children}
    </button>
  );
}

interface IconButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  label: string;
}

export function IconButton({ label, className, children, type = "button", ...props }: IconButtonProps) {
  return (
    <button
      type={type}
      aria-label={label}
      title={label}
      className={cn(
        "inline-flex size-8 items-center justify-center rounded-lg text-stone-500 transition-colors",
        "hover:bg-stone-200/70 hover:text-stone-900 disabled:opacity-50",
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}
