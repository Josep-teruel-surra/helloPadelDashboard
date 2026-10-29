import { cn } from "@/lib/cn";

export function Logo({ className }: { className?: string }) {
  return (
    <span className={cn("inline-flex items-center gap-2 font-extrabold tracking-tight", className)}>
      <span className="inline-block size-3 rounded-full bg-brand" aria-hidden />
      <span>
        HELLO <span className="text-brand">PADEL</span>
      </span>
    </span>
  );
}
