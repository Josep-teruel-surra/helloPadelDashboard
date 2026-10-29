import { useQuery } from "@tanstack/react-query";

import { notesApi, todosApi, usersApi } from "./endpoints";
import type { NoteFilters, TodoFilters } from "./endpoints";

// Claves de caché centralizadas: invalidar ["todos"] refresca cualquier listado de tareas.
export const queryKeys = {
  users: (includeInactive = false) => ["users", { includeInactive }] as const,
  todos: (filters: TodoFilters = {}) => ["todos", filters] as const,
  notes: (filters: NoteFilters = {}) => ["notes", filters] as const,
  note: (id: string) => ["notes", "detail", id] as const,
};

export function useUsers(includeInactive = false) {
  return useQuery({
    queryKey: queryKeys.users(includeInactive),
    queryFn: () => usersApi.list(includeInactive),
    staleTime: 5 * 60_000,
  });
}

export function useTodos(filters: TodoFilters) {
  return useQuery({ queryKey: queryKeys.todos(filters), queryFn: () => todosApi.list(filters) });
}

export function useNotes(filters: NoteFilters) {
  return useQuery({ queryKey: queryKeys.notes(filters), queryFn: () => notesApi.list(filters) });
}

export function useNote(id: string) {
  return useQuery({ queryKey: queryKeys.note(id), queryFn: () => notesApi.get(id) });
}
