import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import type { FormEvent, ReactNode } from "react";
import { useNavigate } from "react-router";

import { shipmentsApi } from "@/api/endpoints";
import { LOGISTICS_KEYS, useCampuses, useEvents, useUsers } from "@/api/queries";
import type { AcademyEvent, Shipment, ShipmentStatus } from "@/api/types";
import { Button } from "@/components/ui/Button";
import { ErrorAlert } from "@/components/ui/Feedback";
import { Field, inputClass } from "@/components/ui/Field";
import { formatDate } from "@/lib/format";
import { useInvalidate } from "@/lib/useInvalidate";
import { ItemsEditor, toItemInputs } from "./ItemsEditor";
import type { ItemDraft } from "./ItemsEditor";

function Actions({ saving, label, onCancel }: { saving: boolean; label: string; onCancel: () => void }) {
  return (
    <div className="flex justify-end gap-2 pt-2">
      <Button variant="secondary" onClick={onCancel}>
        Cancelar
      </Button>
      <Button type="submit" loading={saving}>
        {label}
      </Button>
    </div>
  );
}

function UserSelect({ id, value, onChange }: { id: string; value: string; onChange: (v: string) => void }) {
  const users = useUsers();
  return (
    <select id={id} value={value} onChange={(e) => onChange(e.target.value)} className={inputClass}>
      <option value="">Sin asignar</option>
      {users.data?.map((u) => (
        <option key={u.id} value={u.id}>
          {u.full_name}
        </option>
      ))}
    </select>
  );
}

const EMPTY_ITEMS: ItemDraft[] = [{ variant_id: "", quantity: "1" }];

/** Nuevo envío = apartar material. Con `event`, campus y fecha salen del evento. */
export function NewShipmentForm({ event, onDone }: { event?: AcademyEvent; onDone: () => void }) {
  const invalidate = useInvalidate();
  const navigate = useNavigate();
  const campuses = useCampuses();
  const [campusId, setCampusId] = useState(event?.campus.id ?? "");
  const [eventId, setEventId] = useState(event?.id ?? "");
  const events = useEvents({ campus_id: campusId || undefined, when: "upcoming" });
  const [items, setItems] = useState<ItemDraft[]>(EMPTY_ITEMS);
  const [neededBy, setNeededBy] = useState("");
  const [assigneeId, setAssigneeId] = useState("");
  const [notes, setNotes] = useState("");

  const save = useMutation({
    mutationFn: () =>
      shipmentsApi.create({
        campus_id: campusId || null,
        event_id: eventId || null,
        items: toItemInputs(items),
        // Vacíos: el backend toma la fecha y el responsable del evento.
        needed_by: neededBy || null,
        assignee_id: assigneeId || null,
        notes_md: notes,
      }),
    onSuccess: async (shipment) => {
      await invalidate(...LOGISTICS_KEYS);
      onDone();
      if (!event) navigate(`/envios/${shipment.id}`);
    },
  });

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    save.mutate();
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <ErrorAlert error={save.error} />

      {event ? (
        <p className="rounded-lg bg-stone-100 px-3 py-2 text-sm">
          Para <strong>{event.title}</strong> ({event.campus.name}, {formatDate(event.start_date)}).
          Al apartarlo, la tarea de material del evento se marcará como hecha.
        </p>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Campus" htmlFor="shipment-campus">
            <select
              id="shipment-campus"
              required
              value={campusId}
              onChange={(e) => {
                setCampusId(e.target.value);
                setEventId("");
              }}
              className={inputClass}
            >
              <option value="">Elige campus…</option>
              {campuses.data?.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Evento" htmlFor="shipment-event" hint="Opcional">
            <select
              id="shipment-event"
              value={eventId}
              disabled={!campusId}
              onChange={(e) => setEventId(e.target.value)}
              className={inputClass}
            >
              <option value="">Sin evento</option>
              {events.data?.map((ev) => (
                <option key={ev.id} value={ev.id}>
                  {ev.title} · {formatDate(ev.start_date)}
                </option>
              ))}
            </select>
          </Field>
        </div>
      )}

      <fieldset>
        <legend className="mb-2 text-sm font-medium text-stone-700">Material</legend>
        <ItemsEditor items={items} onChange={setItems} />
      </fieldset>

      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Lo necesitan antes del" htmlFor="shipment-needed" hint={eventId ? "Por defecto, el inicio del evento" : undefined}>
          <input id="shipment-needed" type="date" value={neededBy} onChange={(e) => setNeededBy(e.target.value)} className={inputClass} />
        </Field>
        <Field label="Lo prepara" htmlFor="shipment-assignee" hint={eventId ? "Por defecto, el responsable del evento" : undefined}>
          <UserSelect id="shipment-assignee" value={assigneeId} onChange={setAssigneeId} />
        </Field>
      </div>
      <Field label="Notas" htmlFor="shipment-notes" hint="Opcional">
        <textarea id="shipment-notes" rows={2} value={notes} onChange={(e) => setNotes(e.target.value)} className={inputClass} />
      </Field>

      <Actions saving={save.isPending} label="Apartar material" onCancel={onDone} />
    </form>
  );
}

/** Cambiar el contenido de un envío en preparación. */
export function EditItemsForm({ shipment, onDone }: { shipment: Shipment; onDone: () => void }) {
  const invalidate = useInvalidate();
  const [items, setItems] = useState<ItemDraft[]>(
    shipment.items.map((i) => ({ variant_id: i.variant_id, quantity: String(i.quantity) })),
  );
  const alreadyReserved = Object.fromEntries(shipment.items.map((i) => [i.variant_id, i.quantity]));

  const save = useMutation({
    mutationFn: () => shipmentsApi.replaceItems(shipment.id, toItemInputs(items)),
    onSuccess: async () => {
      await invalidate(...LOGISTICS_KEYS);
      onDone();
    },
  });

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        save.mutate();
      }}
      className="space-y-4"
    >
      <ErrorAlert error={save.error} />
      <ItemsEditor items={items} onChange={setItems} alreadyReserved={alreadyReserved} />
      <Actions saving={save.isPending} label="Guardar contenido" onCancel={onDone} />
    </form>
  );
}

/** Datos del envío: responsable, fecha, transporte, coste y notas. */
export function ShipmentDetailsForm({ shipment, onDone }: { shipment: Shipment; onDone: () => void }) {
  const invalidate = useInvalidate();
  const [form, setForm] = useState({
    assignee_id: shipment.assignee?.id ?? "",
    needed_by: shipment.needed_by ?? "",
    carrier: shipment.carrier ?? "",
    tracking_number: shipment.tracking_number ?? "",
    tracking_url: shipment.tracking_url ?? "",
    cost_amount: shipment.cost_amount ?? "",
    cost_currency: shipment.cost_currency,
    notes_md: shipment.notes_md,
  });
  const set = (field: keyof typeof form) => (value: string) => setForm((f) => ({ ...f, [field]: value }));

  const save = useMutation({
    mutationFn: () =>
      shipmentsApi.update(shipment.id, {
        ...form,
        assignee_id: form.assignee_id || null,
        needed_by: form.needed_by || null,
        carrier: form.carrier || null,
        tracking_number: form.tracking_number || null,
        tracking_url: form.tracking_url || null,
        cost_amount: form.cost_amount || null,
      }),
    onSuccess: async () => {
      await invalidate(["shipments"], ["home"]);
      onDone();
    },
  });

  const input = (id: keyof typeof form, label: string, props: Record<string, unknown> = {}): ReactNode => (
    <Field label={label} htmlFor={`sd-${id}`}>
      <input id={`sd-${id}`} value={form[id]} onChange={(e) => set(id)(e.target.value)} className={inputClass} {...props} />
    </Field>
  );

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        save.mutate();
      }}
      className="space-y-4"
    >
      <ErrorAlert error={save.error} />
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Lo prepara" htmlFor="sd-assignee">
          <UserSelect id="sd-assignee" value={form.assignee_id} onChange={set("assignee_id")} />
        </Field>
        {input("needed_by", "Lo necesitan antes del", { type: "date" })}
        {input("carrier", "Transportista", { maxLength: 80, placeholder: "DHL, Correos, lo lleva el coach…" })}
        {input("tracking_number", "Nº de seguimiento", { maxLength: 120 })}
      </div>
      {input("tracking_url", "Enlace de seguimiento", { type: "url", maxLength: 500, placeholder: "https://…" })}
      <div className="grid grid-cols-[1fr_6rem] gap-4">
        {input("cost_amount", "Coste", { type: "number", min: 0, step: "0.01" })}
        {input("cost_currency", "Moneda", { maxLength: 3, pattern: "[A-Za-z]{3}" })}
      </div>
      <Field label="Notas" htmlFor="sd-notes">
        <textarea id="sd-notes" rows={3} value={form.notes_md} onChange={(e) => set("notes_md")(e.target.value)} className={inputClass} />
      </Field>
      <Actions saving={save.isPending} label="Guardar" onCancel={onDone} />
    </form>
  );
}

/** Marcar como enviado (con datos de transporte) u otro cambio de estado con confirmación. */
export function StatusForm({
  shipment,
  status,
  onDone,
}: {
  shipment: Shipment;
  status: ShipmentStatus;
  onDone: () => void;
}) {
  const invalidate = useInvalidate();
  const [carrier, setCarrier] = useState(shipment.carrier ?? "");
  const [trackingNumber, setTrackingNumber] = useState(shipment.tracking_number ?? "");
  const [trackingUrl, setTrackingUrl] = useState(shipment.tracking_url ?? "");
  const shipping = status === "shipped";

  const save = useMutation({
    mutationFn: () =>
      shipmentsApi.changeStatus(shipment.id, {
        status,
        ...(shipping && {
          carrier: carrier || null,
          tracking_number: trackingNumber || null,
          tracking_url: trackingUrl || null,
        }),
      }),
    onSuccess: async () => {
      await invalidate(...LOGISTICS_KEYS);
      onDone();
    },
  });

  const explanation: Partial<Record<ShipmentStatus, string>> = {
    shipped:
      shipment.status === "preparing"
        ? `Se descontarán ${shipment.total_units} unidades del almacén.`
        : "Se marca como reenviado tras la incidencia.",
    delivered: "El campus ha recibido el material.",
    incident: "Algo ha ido mal (retraso, aduanas, material dañado…). Explícalo en las notas del envío.",
    cancelled:
      shipment.status === "preparing"
        ? "Se libera el material apartado."
        : `El material vuelve al almacén (+${shipment.total_units} unidades).`,
  };

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        save.mutate();
      }}
      className="space-y-4"
    >
      <ErrorAlert error={save.error} />
      <p className="text-sm text-stone-600">{explanation[status]}</p>
      {shipping && (
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Transportista" htmlFor="st-carrier">
            <input id="st-carrier" maxLength={80} value={carrier} onChange={(e) => setCarrier(e.target.value)} className={inputClass} placeholder="DHL, Correos, lo lleva el coach…" />
          </Field>
          <Field label="Nº de seguimiento" htmlFor="st-number">
            <input id="st-number" maxLength={120} value={trackingNumber} onChange={(e) => setTrackingNumber(e.target.value)} className={inputClass} />
          </Field>
          <Field label="Enlace de seguimiento" htmlFor="st-url" className="sm:col-span-2">
            <input id="st-url" type="url" maxLength={500} value={trackingUrl} onChange={(e) => setTrackingUrl(e.target.value)} className={inputClass} placeholder="https://…" />
          </Field>
        </div>
      )}
      <Actions saving={save.isPending} label="Confirmar" onCancel={onDone} />
    </form>
  );
}
