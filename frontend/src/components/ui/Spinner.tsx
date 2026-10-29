import { LoaderCircle } from "lucide-react";

export function Spinner({ label = "Cargando…" }: { label?: string }) {
  return (
    <div role="status" className="flex items-center justify-center gap-2 py-10 text-sm text-stone-500">
      <LoaderCircle className="size-5 animate-spin" aria-hidden />
      {label}
    </div>
  );
}

export function FullPageSpinner() {
  return (
    <div className="flex min-h-dvh items-center justify-center">
      <Spinner />
    </div>
  );
}
