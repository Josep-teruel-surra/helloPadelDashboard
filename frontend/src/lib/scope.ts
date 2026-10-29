import type { Scope } from "@/api/types";

export const SCOPE_OPTIONS: { value: Scope; label: string }[] = [
  { value: "personal", label: "Personal" },
  { value: "company", label: "Empresa" },
];
