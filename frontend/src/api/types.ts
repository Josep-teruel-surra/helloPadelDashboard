// Tipos que reflejan los schemas del backend.

export type Role = "admin" | "worker";
export type Scope = "personal" | "company";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: Role;
  is_active: boolean;
  last_login_at: string | null;
  created_at: string;
}

export interface UserSummary {
  id: string;
  full_name: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: "bearer";
  expires_in: number;
  user: User;
}

export interface Todo {
  id: string;
  scope: Scope;
  title: string;
  description: string | null;
  is_done: boolean;
  completed_at: string | null;
  due_date: string | null;
  created_by: UserSummary;
  assignee: UserSummary | null;
  created_at: string;
  updated_at: string;
  can_edit: boolean;
}

export interface Note {
  id: string;
  scope: Scope;
  title: string;
  content_md: string;
  author: UserSummary;
  created_at: string;
  updated_at: string;
  can_edit: boolean;
}
