import { api } from "./client";
import type { Note, Role, Scope, Todo, TokenResponse, User } from "./types";

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
  limit?: number;
}

export interface TodoCreateInput {
  scope: Scope;
  title: string;
  description?: string | null;
  due_date?: string | null;
  assignee_id?: string | null;
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
  limit?: number;
}

export interface NoteCreateInput {
  scope: Scope;
  title: string;
  content_md: string;
}

export const notesApi = {
  list: (filters: NoteFilters = {}) => api<Note[]>("/notes", { query: { ...filters } }),
  get: (id: string) => api<Note>(`/notes/${id}`),
  create: (data: NoteCreateInput) => api<Note>("/notes", { method: "POST", body: data }),
  update: (id: string, data: Partial<Omit<NoteCreateInput, "scope">>) =>
    api<Note>(`/notes/${id}`, { method: "PATCH", body: data }),
  remove: (id: string) => api<void>(`/notes/${id}`, { method: "DELETE" }),
};
