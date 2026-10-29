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

export interface HomeSummary {
  todos: {
    personal: Todo[];
    company: Todo[];
    personal_pending: number;
    company_pending: number;
    assigned_to_me: number;
    overdue: number;
  };
  notes: Note[];
}

export type WeatherIcon =
  | "clear"
  | "partly-cloudy"
  | "cloudy"
  | "fog"
  | "drizzle"
  | "rain"
  | "snow"
  | "storm";

interface WeatherCondition {
  weather_code: number;
  description: string;
  icon: WeatherIcon;
}

export interface Weather {
  location: {
    latitude: number;
    longitude: number;
    name: string | null;
    is_default: boolean;
    timezone: string;
  };
  current: WeatherCondition & {
    time: string;
    is_day: boolean;
    temperature: number;
    apparent_temperature: number | null;
    humidity: number | null;
    precipitation: number | null;
    wind_speed: number | null;
    wind_gusts: number | null;
  };
  hourly: (WeatherCondition & {
    time: string;
    temperature: number | null;
    precipitation_probability: number | null;
  })[];
  daily: (WeatherCondition & {
    date: string;
    temperature_max: number | null;
    temperature_min: number | null;
    precipitation_probability_max: number | null;
    sunrise: string | null;
    sunset: string | null;
  })[];
  fetched_at: string;
  stale: boolean;
}
