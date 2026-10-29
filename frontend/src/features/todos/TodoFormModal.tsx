import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import type { FormEvent } from "react";

import { todosApi } from "@/api/endpoints";
import { useUsers } from "@/api/queries";
import type { Scope, Todo } from "@/api/types";
import { Button } from "@/components/ui/Button";
import { ErrorAlert } from "@/components/ui/Feedback";
import { Field, inputClass } from "@/components/ui/Field";
import { Modal } from "@/components/ui/Modal";
import { Segmented } from "@/components/ui/Layout";
import { SCOPE_OPTIONS } from "@/lib/scope";

interface TodoFormModalProps {
  open: boolean;
  onClose: () => void;
  /** Tarea a editar; si no hay, se crea una nueva. */
  todo?: Todo | null;
  defaultScope: Scope;
}

export function TodoFormModal({ open, onClose, todo, defaultScope }: TodoFormModalProps) {
  return (
    <Modal open={open} onClose={onClose} title={todo ? "Editar tarea" : "Nueva tarea"}>
      {/* key: reinicia el formulario cada vez que cambia la tarea */}
      <TodoForm key={todo?.id ?? `new-${defaultScope}`} todo={todo} defaultScope={defaultScope} onDone={onClose} />
    </Modal>
  );
}

function TodoForm({
  todo,
  defaultScope,
  onDone,
}: {
  todo?: Todo | null;
  defaultScope: Scope;
  onDone: () => void;
}) {
  const queryClient = useQueryClient();
  const [scope, setScope] = useState<Scope>(todo?.scope ?? defaultScope);
  const [title, setTitle] = useState(todo?.title ?? "");
  const [description, setDescription] = useState(todo?.description ?? "");
  const [dueDate, setDueDate] = useState(todo?.due_date ?? "");
  const [assigneeId, setAssigneeId] = useState(todo?.assignee?.id ?? "");
  const users = useUsers();

  const save = useMutation({
    mutationFn: () => {
      const fields = {
        title,
        description: description.trim() || null,
        due_date: dueDate || null,
        ...(scope === "company" && { assignee_id: assigneeId || null }),
      };
      return todo ? todosApi.update(todo.id, fields) : todosApi.create({ scope, ...fields });
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["todos"] });
      onDone();
    },
  });

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    save.mutate();
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <ErrorAlert error={save.error} />

      {!todo && (
        <Segmented label="Ámbito" options={SCOPE_OPTIONS} value={scope} onChange={setScope} />
      )}

      <Field label="Título" htmlFor="todo-title">
        <input
          id="todo-title"
          required
          maxLength={200}
          autoFocus
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className={inputClass}
          placeholder="Ej.: Revisar redes de la pista 3"
        />
      </Field>

      <Field label="Descripción" htmlFor="todo-description" hint="Opcional">
        <textarea
          id="todo-description"
          rows={3}
          maxLength={5000}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className={inputClass}
        />
      </Field>

      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Fecha límite" htmlFor="todo-due" hint="Opcional">
          <input
            id="todo-due"
            type="date"
            value={dueDate}
            onChange={(e) => setDueDate(e.target.value)}
            className={inputClass}
          />
        </Field>

        {scope === "company" && (
          <Field label="Asignada a" htmlFor="todo-assignee">
            <select
              id="todo-assignee"
              value={assigneeId}
              onChange={(e) => setAssigneeId(e.target.value)}
              className={inputClass}
            >
              <option value="">Sin asignar</option>
              {users.data?.map((user) => (
                <option key={user.id} value={user.id}>
                  {user.full_name}
                </option>
              ))}
            </select>
          </Field>
        )}
      </div>

      {scope === "personal" && !todo && (
        <p className="text-xs text-stone-500">Las tareas personales solo las ves tú.</p>
      )}

      <div className="flex justify-end gap-2 pt-2">
        <Button variant="secondary" onClick={onDone}>
          Cancelar
        </Button>
        <Button type="submit" loading={save.isPending}>
          {todo ? "Guardar" : "Crear tarea"}
        </Button>
      </div>
    </form>
  );
}
