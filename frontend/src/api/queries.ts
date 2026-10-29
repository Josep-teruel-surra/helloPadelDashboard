import { useQuery } from "@tanstack/react-query";

import {
  campusesApi,
  eventsApi,
  homeApi,
  inventoryApi,
  notesApi,
  shipmentsApi,
  todosApi,
  usersApi,
  weatherApi,
} from "./endpoints";
import type {
  Coordinates,
  EventFilters,
  NoteFilters,
  ShipmentFilters,
  TodoFilters,
} from "./endpoints";

// Claves de caché centralizadas: invalidar ["todos"] refresca cualquier listado de tareas.
export const queryKeys = {
  users: (includeInactive = false) => ["users", { includeInactive }] as const,
  todos: (filters: TodoFilters = {}) => ["todos", filters] as const,
  notes: (filters: NoteFilters = {}) => ["notes", filters] as const,
  note: (id: string) => ["notes", "detail", id] as const,
  home: () => ["home"] as const,
  weather: (coords: Coordinates | null) => ["weather", coords] as const,
  campuses: (filters: object = {}) => ["campuses", filters] as const,
  campus: (id: string) => ["campuses", "detail", id] as const,
  events: (filters: EventFilters = {}) => ["events", filters] as const,
  event: (id: string) => ["events", "detail", id] as const,
  products: (filters: object = {}) => ["products", filters] as const,
  movements: (filters: object = {}) => ["products", "movements", filters] as const,
  shipments: (filters: ShipmentFilters = {}) => ["shipments", filters] as const,
  shipment: (id: string) => ["shipments", "detail", id] as const,
  sentMaterial: (filters: object = {}) => ["shipments", "sent-material", filters] as const,
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

export function useCampuses(filters: { include_inactive?: boolean; q?: string } = {}) {
  return useQuery({ queryKey: queryKeys.campuses(filters), queryFn: () => campusesApi.list(filters) });
}

export function useCampus(id: string) {
  return useQuery({ queryKey: queryKeys.campus(id), queryFn: () => campusesApi.get(id) });
}

export function useEvents(filters: EventFilters = {}) {
  return useQuery({ queryKey: queryKeys.events(filters), queryFn: () => eventsApi.list(filters) });
}

export function useEvent(id: string) {
  return useQuery({ queryKey: queryKeys.event(id), queryFn: () => eventsApi.get(id) });
}

export function useProducts(filters: { include_inactive?: boolean; category?: "clothing" | "book" | "other" } = {}) {
  return useQuery({ queryKey: queryKeys.products(filters), queryFn: () => inventoryApi.list(filters) });
}

export function useMovements(filters: { variant_id?: string; product_id?: string; limit?: number }, enabled = true) {
  return useQuery({
    queryKey: queryKeys.movements(filters),
    queryFn: () => inventoryApi.movements(filters),
    enabled,
  });
}

export function useShipments(filters: ShipmentFilters = {}) {
  return useQuery({ queryKey: queryKeys.shipments(filters), queryFn: () => shipmentsApi.list(filters) });
}

export function useShipment(id: string) {
  return useQuery({ queryKey: queryKeys.shipment(id), queryFn: () => shipmentsApi.get(id) });
}

export function useSentMaterial(filters: { campus_id?: string; year?: number }) {
  return useQuery({
    queryKey: queryKeys.sentMaterial(filters),
    queryFn: () => shipmentsApi.sentMaterial(filters),
  });
}

/** Tras tocar envíos o stock: refresca todo lo que depende de ellos. */
export const LOGISTICS_KEYS = [["shipments"], ["products"], ["events"], ["todos"], ["home"]] as const;
