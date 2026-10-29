import { MapPin, Plus, Search } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router";

import { useCampuses } from "@/api/queries";
import { Button } from "@/components/ui/Button";
import { CountryFlag } from "@/components/ui/Country";
import { Badge, EmptyState, ErrorAlert } from "@/components/ui/Feedback";
import { inputClass } from "@/components/ui/Field";
import { PageHeader } from "@/components/ui/Layout";
import { Spinner } from "@/components/ui/Spinner";
import { cn } from "@/lib/cn";
import { countryName } from "@/lib/countries";
import { useDebouncedValue } from "@/lib/useDebouncedValue";
import { CampusFormModal } from "./CampusFormModal";

export function CampusesPage() {
  const [search, setSearch] = useState("");
  const [includeInactive, setIncludeInactive] = useState(false);
  const [creating, setCreating] = useState(false);
  const q = useDebouncedValue(search.trim());
  const campuses = useCampuses({ include_inactive: includeInactive, q: q || undefined });

  return (
    <>
      <PageHeader
        title="Campus"
        description="Sedes de la academia en cada país, sus coordinadores y direcciones de envío."
        actions={
          <Button onClick={() => setCreating(true)}>
            <Plus className="size-4" aria-hidden />
            Nuevo campus
          </Button>
        }
      />

      <div className="mb-4 flex flex-wrap items-center gap-3">
        <div className="relative w-full sm:w-72">
          <Search
            className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-stone-400"
            aria-hidden
          />
          <input
            type="search"
            aria-label="Buscar campus"
            placeholder="Buscar por nombre, ciudad o partner…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className={cn(inputClass, "pl-9")}
          />
        </div>
        <label className="flex cursor-pointer items-center gap-2 text-sm font-medium text-stone-700">
          <input
            type="checkbox"
            checked={includeInactive}
            onChange={(e) => setIncludeInactive(e.target.checked)}
            className="size-4 accent-amber-500"
          />
          Mostrar desactivados
        </label>
      </div>

      <ErrorAlert error={campuses.error} className="mb-4" />

      {campuses.isPending ? (
        <Spinner />
      ) : campuses.data && campuses.data.length > 0 ? (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {campuses.data.map((campus) => (
            <Link
              key={campus.id}
              to={`/campus/${campus.id}`}
              className={cn(
                "flex gap-3 rounded-2xl border border-stone-200 bg-white p-4 transition hover:border-stone-300 hover:shadow-sm",
                !campus.is_active && "opacity-60",
              )}
            >
              <CountryFlag code={campus.country_code} className="text-3xl leading-none" />
              <div className="min-w-0">
                <p className="flex flex-wrap items-center gap-2 font-bold">
                  {campus.name}
                  {!campus.is_active && <Badge tone="red">Desactivado</Badge>}
                </p>
                <p className="text-sm text-stone-500">
                  {campus.city} · {countryName(campus.country_code)}
                </p>
                {campus.partner && <p className="mt-1 truncate text-xs text-stone-500">{campus.partner}</p>}
                {campus.coordinator_name && (
                  <p className="truncate text-xs text-stone-500">Coordina: {campus.coordinator_name}</p>
                )}
              </div>
            </Link>
          ))}
        </div>
      ) : (
        !campuses.error && (
          <EmptyState
            icon={<MapPin className="size-8" />}
            title={q ? "Ningún campus coincide con la búsqueda" : "Todavía no hay campus"}
          />
        )
      )}

      <CampusFormModal open={creating} onClose={() => setCreating(false)} />
    </>
  );
}
