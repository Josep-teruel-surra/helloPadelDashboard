import { api } from "./client";
import type {
  AcademyEvent,
  Address,
  Campus,
  EventKind,
  EventStatus,
  HomeSummary,
  MovementKind,
  Note,
  Product,
  ProductCategory,
  Role,
  Scope,
  SentMaterialRow,
  Shipment,
  ShipmentStatus,
  StockMovement,
  Todo,
  TokenResponse,
  User,
  Weather,
} from "./types";

// --- Auth ---

export const authApi = {
  login: (email: string, password: string) =>
    api<TokenResponse>("/auth/login", { method: "POST", body: { email, password } }),
  logout: () => api<void>("/auth/logout", { method: "POST" }),
};

// --- Usuarios ---

export interface UserCreateInput {
  email: string;
  full_name: string;
  password: string;
  role: Role;
}

export type UserUpdateInput = Partial<UserCreateInput & { is_active: boolean }>;

export const usersApi = {
  me: () => api<User>("/users/me"),
  list: (includeInactive = false) =>
    api<User[]>("/users", { query: { include_inactive: includeInactive } }),
  create: (data: UserCreateInput) => api<User>("/users", { method: "POST", body: data }),
  update: (id: string, data: UserUpdateInput) =>
    api<User>(`/users/${id}`, { method: "PATCH", body: data }),
  changeMyPassword: (currentPassword: string, newPassword: string) =>
    api<void>("/users/me/password", {
      method: "POST",
      body: { current_password: currentPassword, new_password: newPassword },
    }),
};

// --- Tareas ---

export interface TodoFilters {
  scope?: Scope;
  is_done?: boolean;
  assigned_to_me?: boolean;
  event_id?: string;
  limit?: number;
}

export interface TodoCreateInput {
  scope: Scope;
  title: string;
  description?: string | null;
  due_date?: string | null;
  assignee_id?: string | null;
  event_id?: string | null;
}

export type TodoUpdateInput = Partial<Omit<TodoCreateInput, "scope"> & { is_done: boolean }>;

export const todosApi = {
  list: (filters: TodoFilters = {}) => api<Todo[]>("/todos", { query: { ...filters } }),
  create: (data: TodoCreateInput) => api<Todo>("/todos", { method: "POST", body: data }),
  update: (id: string, data: TodoUpdateInput) =>
    api<Todo>(`/todos/${id}`, { method: "PATCH", body: data }),
  remove: (id: string) => api<void>(`/todos/${id}`, { method: "DELETE" }),
};

// --- Notas ---

export interface NoteFilters {
  scope?: Scope;
  q?: string;
  event_id?: string;
  limit?: number;
}

export interface NoteCreateInput {
  scope: Scope;
  title: string;
  content_md: string;
  event_id?: string | null;
}

export const notesApi = {
  list: (filters: NoteFilters = {}) => api<Note[]>("/notes", { query: { ...filters } }),
  get: (id: string) => api<Note>(`/notes/${id}`),
  create: (data: NoteCreateInput) => api<Note>("/notes", { method: "POST", body: data }),
  update: (id: string, data: Partial<Omit<NoteCreateInput, "scope">>) =>
    api<Note>(`/notes/${id}`, { method: "PATCH", body: data }),
  remove: (id: string) => api<void>(`/notes/${id}`, { method: "DELETE" }),
};

// --- Home y tiempo ---

export const homeApi = {
  summary: () => api<HomeSummary>("/home"),
};

export interface Coordinates {
  lat: number;
  lon: number;
}

export const weatherApi = {
  get: (coords: Coordinates | null) => api<Weather>("/weather", { query: { ...coords } }),
};

// --- Campus ---

export interface CampusInput {
  name: string;
  country_code: string;
  city: string;
  partner: string | null;
  coordinator_name: string | null;
  coordinator_email: string | null;
  coordinator_phone: string | null;
  shipping_address: Address | null;
  notes_md: string;
  is_active?: boolean;
}

export const campusesApi = {
  list: (filters: { include_inactive?: boolean; q?: string } = {}) =>
    api<Campus[]>("/campuses", { query: { ...filters } }),
  get: (id: string) => api<Campus>(`/campuses/${id}`),
  create: (data: CampusInput) => api<Campus>("/campuses", { method: "POST", body: data }),
  update: (id: string, data: Partial<CampusInput>) =>
    api<Campus>(`/campuses/${id}`, { method: "PATCH", body: data }),
};

// --- Eventos ---

export type EventWhen = "upcoming" | "past" | "all";

export interface EventFilters {
  campus_id?: string;
  status?: EventStatus;
  when?: EventWhen;
  limit?: number;
}

export interface EventInput {
  campus_id: string;
  title: string;
  kind: EventKind;
  status: EventStatus;
  start_date: string;
  end_date: string | null;
  responsible_id: string | null;
  expected_participants: number | null;
  notes_md: string;
}

export const eventsApi = {
  list: (filters: EventFilters = {}) => api<AcademyEvent[]>("/events", { query: { ...filters } }),
  get: (id: string) => api<AcademyEvent>(`/events/${id}`),
  create: (data: EventInput) => api<AcademyEvent>("/events", { method: "POST", body: data }),
  update: (id: string, data: Partial<EventInput>) =>
    api<AcademyEvent>(`/events/${id}`, { method: "PATCH", body: data }),
  remove: (id: string) => api<void>(`/events/${id}`, { method: "DELETE" }),
};

// --- Material ---

export interface VariantInput {
  label: string;
  sku?: string | null;
  low_stock_threshold?: number | null;
  initial_stock?: number;
  is_active?: boolean;
}

export interface ProductInput {
  name: string;
  category: ProductCategory;
  description?: string | null;
  is_active?: boolean;
}

export const inventoryApi = {
  list: (filters: { include_inactive?: boolean; category?: ProductCategory; q?: string } = {}) =>
    api<Product[]>("/products", { query: { ...filters } }),
  create: (data: ProductInput & { variants: VariantInput[] }) =>
    api<Product>("/products", { method: "POST", body: data }),
  update: (id: string, data: Partial<ProductInput>) =>
    api<Product>(`/products/${id}`, { method: "PATCH", body: data }),
  remove: (id: string) => api<void>(`/products/${id}`, { method: "DELETE" }),
  addVariant: (productId: string, data: VariantInput) =>
    api<Product>(`/products/${productId}/variants`, { method: "POST", body: data }),
  updateVariant: (id: string, data: Partial<VariantInput>) =>
    api<Product>(`/variants/${id}`, { method: "PATCH", body: data }),
  movements: (filters: { variant_id?: string; product_id?: string; limit?: number } = {}) =>
    api<StockMovement[]>("/stock/movements", { query: { ...filters } }),
  addMovement: (data: {
    variant_id: string;
    kind: Exclude<MovementKind, "shipment">;
    quantity: number;
    note: string | null;
  }) => api<StockMovement>("/stock/movements", { method: "POST", body: data }),
};

// --- Envíos ---

export interface ItemInput {
  variant_id: string;
  quantity: number;
}

export interface ShipmentFilters {
  status?: ShipmentStatus;
  campus_id?: string;
  event_id?: string;
  assigned_to_me?: boolean;
  limit?: number;
}

export interface ShipmentDetailsInput {
  assignee_id?: string | null;
  needed_by?: string | null;
  carrier?: string | null;
  tracking_number?: string | null;
  tracking_url?: string | null;
  cost_amount?: string | null;
  cost_currency?: string;
  notes_md?: string;
}

export const shipmentsApi = {
  list: (filters: ShipmentFilters = {}) => api<Shipment[]>("/shipments", { query: { ...filters } }),
  get: (id: string) => api<Shipment>(`/shipments/${id}`),
  create: (
    data: ShipmentDetailsInput & {
      campus_id?: string | null;
      event_id?: string | null;
      items: ItemInput[];
    },
  ) => api<Shipment>("/shipments", { method: "POST", body: data }),
  update: (id: string, data: ShipmentDetailsInput) =>
    api<Shipment>(`/shipments/${id}`, { method: "PATCH", body: data }),
  replaceItems: (id: string, items: ItemInput[]) =>
    api<Shipment>(`/shipments/${id}/items`, { method: "PUT", body: { items } }),
  changeStatus: (
    id: string,
    data: { status: ShipmentStatus; carrier?: string | null; tracking_number?: string | null; tracking_url?: string | null },
  ) => api<Shipment>(`/shipments/${id}/status`, { method: "POST", body: data }),
  remove: (id: string) => api<void>(`/shipments/${id}`, { method: "DELETE" }),
  sentMaterial: (filters: { campus_id?: string; year?: number } = {}) =>
    api<SentMaterialRow[]>("/shipments/sent-material", { query: { ...filters } }),
};
