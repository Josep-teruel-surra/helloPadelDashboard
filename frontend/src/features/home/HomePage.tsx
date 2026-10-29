import { ArrowRight, Building2, NotebookPen, SquareCheckBig } from "lucide-react";
import type { ReactNode } from "react";
import { Link } from "react-router";

import { useHomeSummary } from "@/api/queries";
import type { Todo } from "@/api/types";
import { useCurrentUser } from "@/auth/AuthContext";
import { Badge, ErrorAlert } from "@/components/ui/Feedback";
import { Card } from "@/components/ui/Layout";
import { Spinner } from "@/components/ui/Spinner";
import { NoteCard } from "@/features/notes/NotesPage";
import { DueBadge, TodoCheckbox } from "@/features/todos/TodoItem";
import { WeatherWidget } from "@/features/weather/WeatherWidget";

function greeting(): string {
  const hour = new Date().getHours();
  if (hour < 6 || hour >= 21) return "Buenas noches";
  if (hour < 14) return "Buenos días";
  return "Buenas tardes";
}

function SeeAll({ to, children }: { to: string; children: ReactNode }) {
  return (
    <Link
      to={to}
      className="inline-flex shrink-0 items-center gap-1 text-xs font-semibold whitespace-nowrap text-stone-500 hover:text-stone-900"
    >
      {children}
      <ArrowRight className="size-3.5" aria-hidden />
    </Link>
  );
}

function CompactTodoList({ todos, empty }: { todos: Todo[]; empty: string }) {
  if (todos.length === 0) return <p className="py-6 text-center text-sm text-stone-400">{empty}</p>;
  return (
    <ul className="-mx-1 divide-y divide-stone-100">
      {todos.map((todo) => (
        <li key={todo.id} className="flex gap-3 px-1 py-2.5">
          <TodoCheckbox todo={todo} />
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium">{todo.title}</p>
            {(todo.due_date || (todo.scope === "company" && todo.assignee)) && (
              <div className="mt-1 flex flex-wrap gap-1.5">
                <DueBadge todo={todo} />
                {todo.scope === "company" && todo.assignee && (
                  <Badge tone="blue">{todo.assignee.full_name}</Badge>
                )}
              </div>
            )}
          </div>
        </li>
      ))}
    </ul>
  );
}

export function HomePage() {
  const user = useCurrentUser();
  const summary = useHomeSummary();
  const today = new Date().toLocaleDateString("es-ES", {
    weekday: "long",
    day: "numeric",
    month: "long",
  });

  const todos = summary.data?.todos;

  return (
    <>
      <div className="mb-6">
        <p className="text-sm font-medium text-stone-500 first-letter:uppercase">{today}</p>
        <h1 className="text-2xl font-extrabold tracking-tight">
          {greeting()}, {user.full_name.split(" ")[0]}
        </h1>
        {todos && todos.overdue > 0 && (
          <p className="mt-1 text-sm text-red-700">
            Tienes {todos.overdue} {todos.overdue === 1 ? "tarea vencida" : "tareas vencidas"}.
          </p>
        )}
      </div>

      <ErrorAlert error={summary.error} className="mb-4" />

      {/* 1 columna en móvil, 2 en tablet/portátil (tiempo a lo ancho) y 3 en pantallas grandes */}
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <WeatherWidget className="md:col-span-2 xl:col-span-1 xl:row-span-2" />

        <Card
          title="Mis tareas"
          icon={<SquareCheckBig className="size-4" aria-hidden />}
          actions={
            <SeeAll to="/tareas">
              {todos ? `Ver todas (${todos.personal_pending})` : "Ver todas"}
            </SeeAll>
          }
        >
          {summary.isPending ? (
            <Spinner />
          ) : (
            <CompactTodoList todos={todos?.personal ?? []} empty="No tienes tareas pendientes." />
          )}
        </Card>

        <Card
          title="Empresa"
          icon={<Building2 className="size-4" aria-hidden />}
          actions={
            <SeeAll to="/tareas?ambito=empresa">
              {todos ? `Ver todas (${todos.company_pending})` : "Ver todas"}
            </SeeAll>
          }
        >
          {todos && todos.assigned_to_me > 0 && (
            <p className="mb-2">
              <Badge tone="blue">
                {todos.assigned_to_me} {todos.assigned_to_me === 1 ? "asignada" : "asignadas"} a ti
              </Badge>
            </p>
          )}
          {summary.isPending ? (
            <Spinner />
          ) : (
            <CompactTodoList todos={todos?.company ?? []} empty="El equipo está al día." />
          )}
        </Card>

        <Card
          className="md:col-span-2"
          title="Últimas notas"
          icon={<NotebookPen className="size-4" aria-hidden />}
          actions={<SeeAll to="/notas">Ver todas</SeeAll>}
        >
          {summary.isPending ? (
            <Spinner />
          ) : summary.data && summary.data.notes.length > 0 ? (
            <div className="grid gap-3 sm:grid-cols-2">
              {summary.data.notes.map((note) => (
                <NoteCard key={note.id} note={note} />
              ))}
            </div>
          ) : (
            <p className="py-6 text-center text-sm text-stone-400">Todavía no hay notas.</p>
          )}
        </Card>
      </div>
    </>
  );
}
