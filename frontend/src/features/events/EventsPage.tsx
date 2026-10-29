import { CalendarDays, Plus } from "lucide-react";
import { useState } from "react";

import type { EventWhen } from "@/api/endpoints";
import { useCampuses, useEvents } from "@/api/queries";
import { Button } from "@/components/ui/Button";
import { EmptyState, ErrorAlert } from "@/components/ui/Feedback";
import { inlineSelectClass } from "@/components/ui/Field";
import { PageHeader, Segmented } from "@/components/ui/Layout";
import { Spinner } from "@/components/ui/Spinner";
import { EventFormModal } from "./EventFormModal";
import { EventRow } from "./EventRow";

export function EventsPage() {
  const [when, setWhen] = useState<Exclude<EventWhen, "all">>("upcoming");
  const [campusId, setCampusId] = useState("");
  const [creating, setCreating] = useState(false);
  const campuses = useCampuses({ include_inactive: true });
  const events = useEvents({ when, campus_id: campusId || undefined });

  return (
    <>
      <PageHeader
        title="Eventos"
        description="Campus, formaciones y exámenes en cada sede, con su material, tareas y notas."
        actions={
          <Button onClick={() => setCreating(true)}>
            <Plus className="size-4" aria-hidden />
            Nuevo evento
          </Button>
        }
      />

      <div className="mb-4 flex flex-wrap items-center gap-3">
        <Segmented
          label="Cuándo"
          options={[
            { value: "upcoming", label: "Próximos" },
            { value: "past", label: "Pasados" },
          ]}
          value={when}
          onChange={setWhen}
        />
        <select
          aria-label="Campus"
          value={campusId}
          onChange={(e) => setCampusId(e.target.value)}
          className={inlineSelectClass}
        >
          <option value="">Todos los campus</option>
          {campuses.data?.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
      </div>

      <ErrorAlert error={events.error} className="mb-4" />

      {events.isPending ? (
        <Spinner />
      ) : events.data?.length ? (
        <ul className="divide-y divide-stone-100 overflow-hidden rounded-2xl border border-stone-200 bg-white">
          {events.data.map((event) => (
            <EventRow key={event.id} event={event} />
          ))}
        </ul>
      ) : (
        !events.error && (
          <EmptyState
            icon={<CalendarDays className="size-8" />}
            title={when === "upcoming" ? "No hay eventos próximos" : "No hay eventos pasados"}
          />
        )
      )}

      <EventFormModal open={creating} onClose={() => setCreating(false)} defaultCampusId={campusId || undefined} />
    </>
  );
}
