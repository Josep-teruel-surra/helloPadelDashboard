import { useState } from "react";

import { useSentMaterial } from "@/api/queries";
import type { SentMaterialRow } from "@/api/types";
import { CountryFlag } from "@/components/ui/Country";
import { ErrorAlert } from "@/components/ui/Feedback";
import { inlineSelectClass } from "@/components/ui/Field";
import { Spinner } from "@/components/ui/Spinner";

const CURRENT_YEAR = new Date().getFullYear();
const YEARS = [CURRENT_YEAR, CURRENT_YEAR - 1, CURRENT_YEAR - 2];

function groupBy<T>(rows: T[], key: (row: T) => string): [string, T[]][] {
  const groups = new Map<string, T[]>();
  for (const row of rows) groups.set(key(row), [...(groups.get(key(row)) ?? []), row]);
  return [...groups.entries()];
}

function ProductLines({ rows }: { rows: SentMaterialRow[] }) {
  return (
    <ul className="space-y-1.5">
      {groupBy(rows, (r) => r.product_name).map(([product, items]) => (
        <li key={product} className="text-sm">
          <span className="font-medium">{product}</span>
          <span className="ml-2 text-stone-500">
            {items.map((i) => `${i.label}: ${i.quantity}`).join(" · ")}
          </span>
          <span className="ml-2 text-xs font-semibold text-stone-400">
            ({items.reduce((sum, i) => sum + i.quantity, 0)} uds)
          </span>
        </li>
      ))}
    </ul>
  );
}

/** Material que ha recibido un campus (o todos, agrupados por campus) con filtro por año. */
export function SentMaterialTable({ campusId }: { campusId?: string }) {
  const [year, setYear] = useState<number | "">("");
  const rows = useSentMaterial({ campus_id: campusId, year: year || undefined });

  return (
    <div className="space-y-3">
      <select
        aria-label="Año"
        value={year}
        onChange={(e) => setYear(e.target.value ? Number(e.target.value) : "")}
        className={inlineSelectClass}
      >
        <option value="">Desde siempre</option>
        {YEARS.map((y) => (
          <option key={y} value={y}>
            {y}
          </option>
        ))}
      </select>

      <ErrorAlert error={rows.error} />
      {rows.isPending ? (
        <Spinner />
      ) : !rows.data?.length ? (
        <p className="py-4 text-sm text-stone-400">No se ha enviado material en este periodo.</p>
      ) : campusId ? (
        <ProductLines rows={rows.data} />
      ) : (
        <ul className="divide-y divide-stone-100">
          {groupBy(rows.data, (r) => r.campus.id).map(([id, campusRows]) => {
            const campus = campusRows[0]!.campus;
            return (
              <li key={id} className="py-3">
                <p className="mb-1.5 font-semibold">
                  <CountryFlag code={campus.country_code} /> {campus.name}
                </p>
                <ProductLines rows={campusRows} />
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
