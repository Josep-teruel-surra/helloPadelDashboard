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
  event: EventRef | null;
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
  event: EventRef | null;
  created_at: string;
  updated_at: string;
  can_edit: boolean;
}

export interface LowStockItem {
  product_id: string;
  product_name: string;
  variant_id: string;
  label: string;
  available: number;
  low_stock_threshold: number | null;
}

export interface HomeSummary {
  exams: {
    mine: ExamSubmission[];
    mine_count: number;
    unassigned_count: number;
    to_notify_count: number;
    links_at_risk: ExamSubmission[];
  };
  logistics: {
    upcoming_events: AcademyEvent[];
    to_prepare: Shipment[];
    awaiting_delivery: Shipment[];
    low_stock: LowStockItem[];
  };
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

// --- Campus ---

export interface Address {
  recipient: string | null;
  line1: string | null;
  line2: string | null;
  postal_code: string | null;
  city: string | null;
  region: string | null;
  country_code: string | null;
}

export interface CampusSummary {
  id: string;
  name: string;
  country_code: string;
  city: string;
}

export interface Campus extends CampusSummary {
  partner: string | null;
  coordinator_name: string | null;
  coordinator_email: string | null;
  coordinator_phone: string | null;
  shipping_address: Address | null;
  notes_md: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// --- Eventos ---

export type EventKind = "campus" | "coach_training" | "exam" | "other";
export type EventStatus = "planned" | "confirmed" | "done" | "cancelled";

export interface EventRef {
  id: string;
  title: string;
  start_date: string;
}

/** "Event" ya existe en el DOM: lo llamamos AcademyEvent. */
export interface AcademyEvent {
  id: string;
  campus: CampusSummary;
  title: string;
  kind: EventKind;
  status: EventStatus;
  start_date: string;
  end_date: string;
  responsible: UserSummary | null;
  expected_participants: number | null;
  notes_md: string;
  created_by: UserSummary;
  material_task: {
    id: string;
    is_done: boolean;
    due_date: string | null;
    assignee: UserSummary | null;
  } | null;
  created_at: string;
  updated_at: string;
  can_delete: boolean;
}

// --- Material ---

export type ProductCategory = "clothing" | "book" | "other";
export type MovementKind = "restock" | "shipment" | "adjustment" | "return";

export interface Variant {
  id: string;
  label: string;
  sku: string | null;
  low_stock_threshold: number | null;
  is_active: boolean;
  on_hand: number;
  reserved: number;
  available: number;
  low_stock: boolean;
}

export interface Product {
  id: string;
  name: string;
  category: ProductCategory;
  description: string | null;
  is_active: boolean;
  variants: Variant[];
  total_on_hand: number;
  total_available: number;
  created_at: string;
  updated_at: string;
}

export interface StockMovement {
  id: string;
  kind: MovementKind;
  quantity: number;
  note: string | null;
  variant: { id: string; label: string; product_id: string; product_name: string };
  shipment_id: string | null;
  shipment_number: number | null;
  created_by: UserSummary;
  created_at: string;
}

// --- Envíos ---

export type ShipmentStatus = "preparing" | "shipped" | "delivered" | "incident" | "cancelled";

export interface ShipmentItem {
  variant_id: string;
  product_id: string;
  product_name: string;
  label: string;
  quantity: number;
}

export interface Shipment {
  id: string;
  number: number;
  status: ShipmentStatus;
  campus: CampusSummary;
  event: EventRef | null;
  items: ShipmentItem[];
  total_units: number;
  shipping_address: Address | null;
  carrier: string | null;
  tracking_number: string | null;
  tracking_url: string | null;
  needed_by: string | null;
  shipped_at: string | null;
  delivered_at: string | null;
  assignee: UserSummary | null;
  created_by: UserSummary;
  cost_amount: string | null;
  cost_currency: string;
  notes_md: string;
  created_at: string;
  updated_at: string;
  can_delete: boolean;
  stock_warnings: string[];
}

export interface SentMaterialRow {
  campus: CampusSummary;
  product_id: string;
  product_name: string;
  variant_id: string;
  label: string;
  quantity: number;
}

// --- Correcciones de exámenes ---

export interface StudentSummary {
  id: string;
  full_name: string;
  email: string;
  country_code: string | null;
}

export interface Student extends StudentSummary {
  campus: CampusSummary | null;
  notes_md: string;
  created_at: string;
  updated_at: string;
}

export interface Certification {
  id: string;
  name: string;
  has_test: boolean;
  has_video: boolean;
  position: number;
  is_active: boolean;
}

export type ExamKind = "test" | "video";
export type ExamSource = "examportal" | "wetransfer" | "email" | "other";
export type ExamStatus = "received" | "in_review" | "on_hold" | "corrected" | "notified" | "cancelled";
export type ExamOutcome = "passed" | "failed" | "resubmit";
export type LinkStatus = "ok" | "expiring" | "expired" | "saved";

export interface ExamSubmission {
  id: string;
  student: StudentSummary;
  certification: { id: string; name: string };
  kind: ExamKind;
  source: ExamSource;
  link_url: string | null;
  link_expires_on: string | null;
  saved_url: string | null;
  saved_at: string | null;
  received_on: string;
  due_on: string;
  status: ExamStatus;
  assignee: UserSummary | null;
  outcome: ExamOutcome | null;
  score: string | null;
  feedback_md: string;
  corrected_by: UserSummary | null;
  corrected_at: string | null;
  notified_at: string | null;
  created_by: UserSummary;
  created_at: string;
  updated_at: string;
  attempt: number;
  days_left: number | null;
  link_status: LinkStatus | null;
  can_delete: boolean;
}
