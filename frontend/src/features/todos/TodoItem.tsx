import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Check, Pencil, Trash2, UserRound } from "lucide-react";

import { errorMessage } from "@/api/client";
import { todosApi } from "@/api/endpoints";
import type { Todo } from "@/api/types";
import { IconButton } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Feedback";
import { cn } from "@/lib/cn";
import { dueStatus, formatDate } from "@/lib/format";

export function DueBadge({ todo }: { todo: Todo }) {
  if (!todo.due_date) return null;
  const status = dueStatus(todo.due_date, todo.is_done);
  if (status === "overdue") return <Badge tone="red">Vencida · {formatDate(todo.due_date)}</Badge>;
  if (status === "today") return <Badge tone="amber">Hoy</Badge>;
  return <Badge>{formatDate(todo.due_date)}</Badge>;
}

export function TodoCheckbox({ todo }: { todo: Todo }) {
  const queryClient = useQueryClient();
  const toggle = useMutation({
    mutationFn: () => todosApi.update(todo.id, { is_done: !todo.is_done }),
    onSuccess: () =>
      Promise.all([
        queryClient.invalidateQueries({ queryKey: ["todos"] }),
        queryClient.invalidateQueries({ queryKey: ["home"] }),
      ]),
    onError: (error) => window.alert(errorMessage(error)),
  });

  return (
    <button
      type="button"
      role="checkbox"
      aria-checked={todo.is_done}
      aria-label={todo.is_done ? `Marcar "${todo.title}" como pendiente` : `Completar "${todo.title}"`}
      disabled={toggle.isPending}
      onClick={() => toggle.mutate()}
      className={cn(
        "mt-0.5 flex size-5 shrink-0 items-center justify-center rounded-md border-2 transition-colors",
        todo.is_done
          ? "border-emerald-600 bg-emerald-600 text-white"
          : "border-stone-300 hover:border-stone-500",
        toggle.isPending && "opacity-50",
      )}
    >
      {todo.is_done && <Check className="size-3.5" strokeWidth={3} />}
    </button>
  );
}

interface TodoItemProps {
  todo: Todo;
  onEdit: (todo: Todo) => void;
}

export function TodoItem({ todo, onEdit }: TodoItemProps) {
  const queryClient = useQueryClient();
  const remove = useMutation({
    mutationFn: () => todosApi.remove(todo.id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["todos"] }),
    onError: (error) => window.alert(errorMessage(error)),
  });

  const isCompany = todo.scope === "company";

  return (
    <li className="flex gap-3 px-4 py-3">
      <TodoCheckbox todo={todo} />
      <div className="min-w-0 flex-1">
        <p
          className={cn(
            "font-medium break-words",
            todo.is_done && "text-stone-400 line-through",
          )}
        >
          {todo.title}
        </p>
        {todo.description && (
          <p className="mt-0.5 line-clamp-2 text-sm whitespace-pre-line text-stone-500">
            {todo.description}
          </p>
        )}
        <div className="mt-1.5 flex flex-wrap items-center gap-1.5 text-xs text-stone-500">
          <DueBadge todo={todo} />
          {isCompany && todo.assignee && (
            <Badge tone="blue">
              <UserRound className="size-3" aria-hidden />
              {todo.assignee.full_name}
            </Badge>
          )}
          {isCompany && <span>Creada por {todo.created_by.full_name}</span>}
        </div>
      </div>
      {todo.can_edit && (
        <div className="flex shrink-0 items-start gap-0.5">
          <IconButton label="Editar" onClick={() => onEdit(todo)}>
            <Pencil className="size-4" />
          </IconButton>
          <IconButton
            label="Borrar"
            disabled={remove.isPending}
            onClick={() => window.confirm(`¿Borrar "${todo.title}"?`) && remove.mutate()}
            className="hover:bg-red-50 hover:text-red-700"
          >
            <Trash2 className="size-4" />
          </IconButton>
        </div>
      )}
    </li>
  );
}
