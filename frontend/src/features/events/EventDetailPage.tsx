import { useMutation } from "@tanstack/react-query";
import {
  ArrowLeft,
  NotebookPen,
  Package,
  PackagePlus,
  Pencil,
  Plus,
  SquareCheckBig,
  Trash2,
  Users,
} from "lucide-react";
import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router";

import { eventsApi } from "@/api/endpoints";
import { useEvent, useNotes, useShipments, useTodos } from "@/api/queries";
import type { Todo } from "@/api/types";
import { Button, buttonClass } from "@/components/ui/Button";
import { CountryFlag } from "@/components/ui/Country";
import { Badge, ErrorAlert } from "@/components/ui/Feedback";
import { Card } from "@/components/ui/Layout";
import { Modal } from "@/components/ui/Modal";
import { Spinner } from "@/components/ui/Spinner";
import { formatDateRange } from "@/lib/format";
import { EVENT_KIND_LABELS, EVENT_STATUS } from "@/lib/labels";
import { useInvalidate } from "@/lib/useInvalidate";
import { Markdown } from "@/features/notes/Markdown";
import { NoteCard } from "@/features/notes/NotesPage";
import { NewShipmentForm } from "@/features/shipments/ShipmentForms";
import { ShipmentRow } from "@/features/shipments/ShipmentRow";
import { TodoFormModal } from "@/features/todos/TodoFormModal";
import { TodoItem } from "@/features/todos/TodoItem";
import { EventFormModal } from "./EventFormModal";
import { MaterialBadge } from "./EventRow";

export function EventDetailPage() {
  const { eventId = "" } = useParams();
  const navigate = useNavigate();
  const invalidate = useInvalidate();
  const event = useEvent(eventId);
  const shipments = useShipments({ event_id: eventId });
  const todos = useTodos({ event_id: eventId });
  const notes = useNotes({ event_id: eventId });

  const [editing, setEditing] = useState(false);
  const [reserving, setReserving] = useState(false);
  const [todoDialog, setTodoDialog] = useState<{ todo: Todo | null } | null>(null);

  const remove = useMutation({
    mutationFn: () => eventsApi.remove(eventId),
    onSuccess: async () => {
      await invalidate(["events"], ["todos"], ["home"]);
      navigate("/eventos", { replace: true });
    },
  });

  const back = (
    <Link to="/eventos" className="mb-4 inline-flex items-center gap-1.5 text-sm font-medium text-stone-500 hover:text-stone-900">
      <ArrowLeft className="size-4" aria-hidden />
      Eventos
    </Link>
  );

  if (event.isPending) return <Spinner />;
  if (event.isError) {
    return (
      <>
        {back}
        <ErrorAlert error={event.error} />
      </>
    );
  }
  const data = event.data;
  const status = EVENT_STATUS[data.status];
  const activeShipments = shipments.data?.filter((s) => s.status !== "cancelled") ?? [];

  return (
    <>
      {back}
      <div className="mb-6 flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <h1 className="text-2xl font-extrabold tracking-tight break-words">{data.title}</h1>
          <p className="mt-1 text-sm text-stone-500">
            <Link to={`/campus/${data.campus.id}`} className="hover:underline">
              <CountryFlag code={data.campus.country_code} /> {data.campus.name}
            </Link>{" "}
            · {formatDateRange(data.start_date, data.end_date)}
          </p>
          <div className="mt-2 flex flex-wrap gap-1.5">
            <Badge>{EVENT_KIND_LABELS[data.kind]}</Badge>
            <Badge tone={status.tone}>{status.label}</Badge>
            <MaterialBadge event={data} />
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={() => setEditing(true)}>
            <Pencil className="size-4" aria-hidden />
            Editar
          </Button>
          {data.can_delete && (
            <Button
              variant="ghost"
              loading={remove.isPending}
              onClick={() => window.confirm("¿Borrar este evento?") && remove.mutate()}
              className="hover:bg-red-50 hover:text-red-700"
            >
              <Trash2 className="size-4" aria-hidden />
              Borrar
            </Button>
          )}
        </div>
      </div>

      <ErrorAlert error={remove.error} className="mb-4" />

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="min-w-0 space-y-4 lg:col-span-2">
          <Card
            title="Material"
            icon={<Package className="size-4" aria-hidden />}
            actions={
              data.status !== "cancelled" && (
                <Button size="sm" onClick={() => setReserving(true)}>
                  <PackagePlus className="size-4" aria-hidden />
                  {activeShipments.length ? "Apartar más" : "Apartar material"}
                </Button>
              )
            }
          >
            {shipments.isPending ? (
              <Spinner />
            ) : shipments.data?.length ? (
              <ul className="-mx-4 divide-y divide-stone-100 sm:-mx-5">
                {shipments.data.map((s) => (
                  <ShipmentRow key={s.id} shipment={s} showCampus={false} showEvent={false} />
                ))}
              </ul>
            ) : (
              <p className="text-sm text-stone-500">
                Todavía no hay material apartado. Al apartarlo se crea un envío en preparación y la tarea
                de material queda hecha.
              </p>
            )}
          </Card>

          <Card
            title="Tareas del evento"
            icon={<SquareCheckBig className="size-4" aria-hidden />}
            actions={
              <Button size="sm" variant="secondary" onClick={() => setTodoDialog({ todo: null })}>
                <Plus className="size-4" aria-hidden />
                Añadir
              </Button>
            }
          >
            {todos.data?.length ? (
              <ul className="-mx-4 divide-y divide-stone-100 sm:-mx-5">
                {todos.data.map((todo) => (
                  <TodoItem
                    key={todo.id}
                    todo={todo}
                    showEvent={false}
                    onEdit={(t) => setTodoDialog({ todo: t })}
                  />
                ))}
              </ul>
            ) : (
              !todos.isPending && <p className="text-sm text-stone-400">Sin tareas.</p>
            )}
          </Card>

          <Card
            title="Notas del evento"
            icon={<NotebookPen className="size-4" aria-hidden />}
            actions={
              <Link
                to={`/notas/nueva?ambito=empresa&evento=${data.id}`}
                className={buttonClass("secondary", "sm")}
              >
                <Plus className="size-4" aria-hidden />
                Nueva nota
              </Link>
            }
          >
            {notes.data?.length ? (
              <div className="grid gap-3 sm:grid-cols-2">
                {notes.data.map((note) => (
                  <NoteCard key={note.id} note={note} />
                ))}
              </div>
            ) : (
              !notes.isPending && <p className="text-sm text-stone-400">Sin notas.</p>
            )}
          </Card>
        </div>

        <Card title="Información">
          <dl className="space-y-3 text-sm">
            <div>
              <dt className="text-xs text-stone-500">Responsable</dt>
              <dd className="font-medium">{data.responsible?.full_name ?? "Sin responsable"}</dd>
            </div>
            {data.expected_participants != null && (
              <div>
                <dt className="text-xs text-stone-500">Participantes previstos</dt>
                <dd className="flex items-center gap-1.5 font-medium">
                  <Users className="size-4 text-stone-400" aria-hidden />
                  {data.expected_participants}
                </dd>
              </div>
            )}
            <div>
              <dt className="text-xs text-stone-500">Creado por</dt>
              <dd className="font-medium">{data.created_by.full_name}</dd>
            </div>
          </dl>
          {data.notes_md.trim() && (
            <div className="mt-4 border-t border-stone-100 pt-3">
              <Markdown content={data.notes_md} className="prose-sm" />
            </div>
          )}
        </Card>
      </div>

      <EventFormModal open={editing} event={data} onClose={() => setEditing(false)} />
      <Modal open={reserving} onClose={() => setReserving(false)} title="Apartar material">
        <NewShipmentForm event={data} onDone={() => setReserving(false)} />
      </Modal>
      <TodoFormModal
        open={todoDialog !== null}
        todo={todoDialog?.todo}
        defaultScope="company"
        defaultEventId={data.id}
        onClose={() => setTodoDialog(null)}
      />
    </>
  );
}
