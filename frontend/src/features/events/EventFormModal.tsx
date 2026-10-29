import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router";

import { eventsApi } from "@/api/endpoints";
import { useCampuses, useUsers } from "@/api/queries";
import type { AcademyEvent, EventKind, EventStatus } from "@/api/types";
import { Button } from "@/components/ui/Button";
import { ErrorAlert } from "@/components/ui/Feedback";
import { Field, inputClass } from "@/components/ui/Field";
import { Modal } from "@/components/ui/Modal";
import { EVENT_KIND_LABELS, EVENT_STATUS, options } from "@/lib/labels";
import { useInvalidate } from "@/lib/useInvalidate";

export function EventFormModal({
  open,
  onClose,
  event,
  defaultCampusId,
}: {
  open: boolean;
  onClose: () => void;
  event?: AcademyEvent | null;
  defaultCampusId?: string;
}) {
  return (
    <Modal open={open} onClose={onClose} title={event ? "Editar evento" : "Nuevo evento"}>
      <EventForm key={event?.id ?? "new"} event={event} defaultCampusId={defaultCampusId} onDone={onClose} />
    </Modal>
  );
}

function EventForm({
  event,
  defaultCampusId,
  onDone,
}: {
  event?: AcademyEvent | null;
  defaultCampusId?: string;
  onDone: () => void;
}) {
  const invalidate = useInvalidate();
  const navigate = useNavigate();
  const campuses = useCampuses();
  const users = useUsers();
  const [form, setForm] = useState({
    campus_id: event?.campus.id ?? defaultCampusId ?? "",
    title: event?.title ?? "",
    kind: event?.kind ?? ("campus" as EventKind),
    status: event?.status ?? ("planned" as EventStatus),
    start_date: event?.start_date ?? "",
    end_date: event?.end_date ?? "",
    responsible_id: event?.responsible?.id ?? "",
    expected_participants: event?.expected_participants?.toString() ?? "",
    notes_md: event?.notes_md ?? "",
  });
  const set = (field: keyof typeof form) => (value: string) => setForm((f) => ({ ...f, [field]: value }));

  const save = useMutation({
    mutationFn: () => {
      const data = {
        ...form,
        end_date: form.end_date || form.start_date,
        responsible_id: form.responsible_id || null,
        expected_participants: form.expected_participants ? Number(form.expected_participants) : null,
      };
      return event ? eventsApi.update(event.id, data) : eventsApi.create(data);
    },
    onSuccess: async (saved) => {
      await invalidate(["events"], ["todos"], ["home"], ["shipments"]);
      onDone();
      if (!event) navigate(`/eventos/${saved.id}`);
    },
  });

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    save.mutate();
  }

  // Al editar, el campus actual puede estar desactivado: lo mantenemos en la lista.
  const campusOptions = campuses.data ?? [];
  const showCurrentCampus = event && !campusOptions.some((c) => c.id === event.campus.id);

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <ErrorAlert error={save.error} />
      <Field label="Título" htmlFor="event-title">
        <input
          id="event-title"
          required
          maxLength={200}
          value={form.title}
          onChange={(e) => set("title")(e.target.value)}
          className={inputClass}
          placeholder="Ej.: Campus de verano Ámsterdam"
        />
      </Field>
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Campus" htmlFor="event-campus">
          <select id="event-campus" required value={form.campus_id} onChange={(e) => set("campus_id")(e.target.value)} className={inputClass}>
            <option value="">Elige campus…</option>
            {showCurrentCampus && <option value={event.campus.id}>{event.campus.name}</option>}
            {campusOptions.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Tipo" htmlFor="event-kind">
          <select id="event-kind" value={form.kind} onChange={(e) => set("kind")(e.target.value)} className={inputClass}>
            {options(EVENT_KIND_LABELS).map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Empieza" htmlFor="event-start">
          <input id="event-start" type="date" required value={form.start_date} onChange={(e) => set("start_date")(e.target.value)} className={inputClass} />
        </Field>
        <Field label="Termina" htmlFor="event-end" hint="Vacío si dura un día">
          <input id="event-end" type="date" min={form.start_date || undefined} value={form.end_date} onChange={(e) => set("end_date")(e.target.value)} className={inputClass} />
        </Field>
        <Field label="Responsable" htmlFor="event-responsible">
          <select id="event-responsible" value={form.responsible_id} onChange={(e) => set("responsible_id")(e.target.value)} className={inputClass}>
            <option value="">Sin responsable</option>
            {users.data?.map((u) => (
              <option key={u.id} value={u.id}>
                {u.full_name}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Participantes previstos" htmlFor="event-participants">
          <input id="event-participants" type="number" min={0} value={form.expected_participants} onChange={(e) => set("expected_participants")(e.target.value)} className={inputClass} />
        </Field>
        <Field label="Estado" htmlFor="event-status">
          <select id="event-status" value={form.status} onChange={(e) => set("status")(e.target.value)} className={inputClass}>
            {options(EVENT_STATUS).map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </Field>
      </div>
      <Field label="Notas" htmlFor="event-notes" hint="Admite markdown.">
        <textarea id="event-notes" rows={3} value={form.notes_md} onChange={(e) => set("notes_md")(e.target.value)} className={inputClass} />
      </Field>
      {!event && (
        <p className="text-xs text-stone-500">
          Se creará la tarea «Apartar material» para el responsable, con vencimiento 3 semanas antes del inicio.
        </p>
      )}
      <div className="flex justify-end gap-2 pt-2">
        <Button variant="secondary" onClick={onDone}>
          Cancelar
        </Button>
        <Button type="submit" loading={save.isPending}>
          {event ? "Guardar" : "Crear evento"}
        </Button>
      </div>
    </form>
  );
}
