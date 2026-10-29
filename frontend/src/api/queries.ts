import { useQuery } from "@tanstack/react-query";

import { homeApi, notesApi, todosApi, usersApi, weatherApi } from "./endpoints";
import type { Coordinates, NoteFilters, TodoFilters } from "./endpoints";

// Claves de caché centralizadas: invalidar ["todos"] refresca cualquier listado de tareas.
export const queryKeys = {
  users: (includeInactive = false) => ["users", { includeInactive }] as const,
  todos: (filters: TodoFilters = {}) => ["todos", filters] as const,
  notes: (filters: NoteFilters = {}) => ["notes", filters] as const,
  note: (id: string) => ["notes", "detail", id] as const,
  home: () => ["home"] as const,
  weather: (coords: Coordinates | null) => ["weather", coords] as const,
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

export function useHomeSummary() {
  // staleTime 0: al volver a la home siempre refleja lo último de tareas y notas.
  return useQuery({ queryKey: queryKeys.home(), queryFn: homeApi.summary, staleTime: 0 });
}

export function useWeather(coords: Coordinates | null, enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.weather(coords),
    queryFn: () => weatherApi.get(coords),
    enabled,
    // El backend cachea 15 min; refrescamos con la misma cadencia.
    staleTime: 10 * 60_000,
    refetchInterval: 15 * 60_000,
  });
}
