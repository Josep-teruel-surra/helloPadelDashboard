import { Plus, SquareCheckBig } from "lucide-react";
import { useState } from "react";
import { useSearchParams } from "react-router";

import { useTodos } from "@/api/queries";
import type { Scope, Todo } from "@/api/types";
import { Button } from "@/components/ui/Button";
import { EmptyState, ErrorAlert } from "@/components/ui/Feedback";
import { PageHeader, Segmented } from "@/components/ui/Layout";
import { Spinner } from "@/components/ui/Spinner";
import { cn } from "@/lib/cn";
import { TodoFormModal } from "./TodoFormModal";
import { TodoItem } from "./TodoItem";

type StatusFilter = "pending" | "done" | "all";

const SCOPE_TABS: { value: Scope; label: string }[] = [
  { value: "personal", label: "Mis tareas" },
  { value: "company", label: "Empresa" },
];

const STATUS_OPTIONS: { value: StatusFilter; label: string }[] = [
  { value: "pending", label: "Pendientes" },
  { value: "done", label: "Hechas" },
  { value: "all", label: "Todas" },
];

export function TodosPage() {
  // El ámbito va en la URL para poder enlazar directamente (p. ej. desde la home).
  const [searchParams, setSearchParams] = useSearchParams();
  const scope: Scope = searchParams.get("ambito") === "empresa" ? "company" : "personal";
  const [status, setStatus] = useState<StatusFilter>("pending");
  const [assignedToMe, setAssignedToMe] = useState(false);
  const [editing, setEditing] = useState<Todo | null>(null);
  const [creating, setCreating] = useState(false);

  const todos = useTodos({
    scope,
    is_done: status === "all" ? undefined : status === "done",
    assigned_to_me: scope === "company" && assignedToMe ? true : undefined,
  });

  function changeScope(value: Scope) {
    setSearchParams(value === "company" ? { ambito: "empresa" } : {}, { replace: true });
  }

  return (
    <>
      <PageHeader
        title="Tareas"
        description="Tus tareas personales y las compartidas por el equipo."
        actions={
          <Button onClick={() => setCreating(true)}>
            <Plus className="size-4" aria-hidden />
            Nueva tarea
          </Button>
        }
      />

      <div className="mb-4 flex flex-wrap items-center gap-3">
        <Segmented label="Ámbito" options={SCOPE_TABS} value={scope} onChange={changeScope} />
        <Segmented label="Estado" options={STATUS_OPTIONS} value={status} onChange={setStatus} />
        {scope === "company" && (
          <label className="flex cursor-pointer items-center gap-2 text-sm font-medium text-stone-700">
            <input
              type="checkbox"
              checked={assignedToMe}
              onChange={(e) => setAssignedToMe(e.target.checked)}
              className="size-4 rounded accent-amber-500"
            />
            Solo asignadas a mí
          </label>
        )}
      </div>

      <ErrorAlert error={todos.error} className="mb-4" />

      {todos.isPending ? (
        <Spinner />
      ) : todos.data && todos.data.length > 0 ? (
        <ul
          className={cn(
            "divide-y divide-stone-100 overflow-hidden rounded-2xl border border-stone-200 bg-white",
            todos.isFetching && "opacity-70",
          )}
        >
          {todos.data.map((todo) => (
            <TodoItem key={todo.id} todo={todo} onEdit={setEditing} />
          ))}
        </ul>
      ) : (
        !todos.error && (
          <EmptyState
            icon={<SquareCheckBig className="size-8" />}
            title={status === "done" ? "Nada completado todavía" : "No hay tareas pendientes"}
            description={
              scope === "personal"
                ? "Las tareas personales solo las ves tú."
                : "Las tareas de empresa las ve todo el equipo."
            }
            action={
              <Button variant="secondary" onClick={() => setCreating(true)}>
                <Plus className="size-4" aria-hidden />
                Añadir una
              </Button>
            }
          />
        )
      )}

      <TodoFormModal
        open={creating || editing !== null}
        todo={editing}
        defaultScope={scope}
        onClose={() => {
          setCreating(false);
          setEditing(null);
        }}
      />
    </>
  );
}
