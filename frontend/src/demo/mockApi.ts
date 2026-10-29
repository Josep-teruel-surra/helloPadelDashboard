/**
 * API simulada para la demo sin backend (VITE_DEMO=true, p. ej. en GitHub Pages).
 *
 * Responde a partir de una foto de la API real con los datos de ejemplo
 * (`snapshot.json`, generada con backend/scripts/demo_snapshot.py). Las fechas se desplazan
 * para que la foto parezca de hoy. Es de solo lectura: cualquier cambio devuelve un aviso.
 */
import { ApiError } from "@/api/client";
import type { TokenResponse, User } from "@/api/types";
import { todayISO } from "@/lib/format";
import raw from "./snapshot.json";

// Filas JSON de la foto: se filtran por campo, sin tipar cada recurso.
type Row = Record<string, any>;
type Query = Record<string, string | number | boolean | null | undefined>;

interface UserData {
  me: User;
  home: Row;
  weather: Row;
  [list: string]: Row | Row[];
}

const SESSION_KEY = "hellopadel-demo-user";
const READ_ONLY = "Esto es una demo con datos de ejemplo: los cambios no se guardan.";
export const DEMO_USERS = Object.keys(raw.users);

// --- Fechas: la foto se mueve al día de hoy ---

const DAY_MS = 86_400_000;
const DATE_RE = /^(\d{4})-(\d{2})-(\d{2})(T.*)?$/;

function daysBetween(from: string, to: string): number {
  const [a, b] = [from, to].map((d) => Date.UTC(+d.slice(0, 4), +d.slice(5, 7) - 1, +d.slice(8, 10)));
  return Math.round((b! - a!) / DAY_MS);
}

function shift(value: unknown, days: number): unknown {
  if (typeof value === "string") {
    const m = DATE_RE.exec(value);
    if (!m) return value;
    const date = new Date(Date.UTC(+m[1]!, +m[2]! - 1, +m[3]! + days));
    return date.toISOString().slice(0, 10) + (m[4] ?? "");
  }
  if (Array.isArray(value)) return value.map((v) => shift(v, days));
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.entries(value).map(([k, v]) => [k, shift(v, days)]));
  }
  return value;
}

let cache: Record<string, UserData> | null = null;

function snapshot(): Record<string, UserData> {
  cache ??= shift(raw.users, daysBetween(raw.generated_on, todayISO())) as Record<string, UserData>;
  return cache;
}

function currentUser(): UserData | null {
  try {
    const email = sessionStorage.getItem(SESSION_KEY);
    return email ? (snapshot()[email] ?? null) : null;
  } catch {
    return null;
  }
}

function tokenFor(data: UserData): TokenResponse {
  return { access_token: "demo", token_type: "bearer", expires_in: 900, user: data.me };
}

// --- Filtros (los mismos que aplica el backend) ---

const isTrue = (v: unknown) => v === true || v === "true";
const has = (q: Query, key: string) => q[key] !== undefined && q[key] !== null && q[key] !== "";
const contains = (text: unknown, q: string) =>
  typeof text === "string" && text.toLowerCase().includes(q.toLowerCase());

function limit<T>(rows: T[], q: Query): T[] {
  return has(q, "limit") ? rows.slice(0, Number(q.limit)) : rows;
}

function byId(rows: Row[], id: string): Row {
  const row = rows.find((r) => r.id === id);
  if (!row) throw new ApiError(404, "No encontrado");
  return row;
}

type Handler = (data: UserData, q: Query, id: string) => unknown;

const ROUTES: [RegExp, Handler][] = [
  [/^\/users\/me$/, (d) => d.me],
  [
    /^\/users$/,
    (d, q) => (d.users as Row[]).filter((u) => (isTrue(q.include_inactive) && d.me.role === "admin") || u.is_active),
  ],
  [/^\/users\/([\w-]+)$/, (d, _q, id) => byId(d.users as Row[], id)],
  [/^\/home$/, (d) => d.home],
  [
    /^\/weather$/,
    (d, q) =>
      has(q, "lat")
        ? { ...d.weather, location: { ...d.weather.location, name: null, is_default: false } }
        : d.weather,
  ],
  [
    /^\/todos$/,
    (d, q) =>
      limit(
        (d.todos as Row[]).filter(
          (t) =>
            (!has(q, "scope") || t.scope === q.scope) &&
            (!has(q, "is_done") || t.is_done === isTrue(q.is_done)) &&
            (!isTrue(q.assigned_to_me) || t.assignee?.id === d.me.id) &&
            (!has(q, "event_id") || t.event?.id === q.event_id),
        ),
        q,
      ),
  ],
  [/^\/todos\/([\w-]+)$/, (d, _q, id) => byId(d.todos as Row[], id)],
  [
    /^\/notes$/,
    (d, q) =>
      limit(
        (d.notes as Row[]).filter(
          (n) =>
            (!has(q, "scope") || n.scope === q.scope) &&
            (!has(q, "event_id") || n.event?.id === q.event_id) &&
            (!has(q, "q") || contains(n.title, String(q.q)) || contains(n.content_md, String(q.q))),
        ),
        q,
      ),
  ],
  [/^\/notes\/([\w-]+)$/, (d, _q, id) => byId(d.notes as Row[], id)],
  [
    /^\/campuses$/,
    (d, q) =>
      (d.campuses as Row[]).filter(
        (c) =>
          (isTrue(q.include_inactive) || c.is_active) &&
          (!has(q, "q") || [c.name, c.city, c.partner].some((f) => contains(f, String(q.q)))),
      ),
  ],
  [/^\/campuses\/([\w-]+)$/, (d, _q, id) => byId(d.campuses as Row[], id)],
  [
    /^\/events$/,
    (d, q) => {
      const today = todayISO();
      const when = (q.when as string) ?? "upcoming";
      let rows = (d.events as Row[]).filter(
        (e) =>
          (!has(q, "campus_id") || e.campus.id === q.campus_id) &&
          (!has(q, "status") || e.status === q.status) &&
          (when === "all" || (when === "upcoming" ? e.end_date >= today : e.end_date < today)),
      );
      if (when === "upcoming") rows = [...rows].sort((a, b) => a.start_date.localeCompare(b.start_date));
      return limit(rows, q);
    },
  ],
  [/^\/events\/([\w-]+)$/, (d, _q, id) => byId(d.events as Row[], id)],
  [
    /^\/products$/,
    (d, q) =>
      (d.products as Row[]).filter(
        (p) =>
          (isTrue(q.include_inactive) || p.is_active) &&
          (!has(q, "category") || p.category === q.category) &&
          (!has(q, "q") ||
            contains(p.name, String(q.q)) ||
            p.variants.some((v: Row) => contains(v.sku, String(q.q)))),
      ),
  ],
  [
    /^\/stock\/movements$/,
    (d, q) =>
      limit(
        (d.movements as Row[]).filter(
          (m) =>
            (!has(q, "variant_id") || m.variant.id === q.variant_id) &&
            (!has(q, "product_id") || m.variant.product_id === q.product_id),
        ),
        q,
      ),
  ],
  [
    /^\/shipments\/sent-material$/,
    (d, q) =>
      has(q, "year") && Number(q.year) !== new Date().getFullYear()
        ? []
        : (d.sent_material as Row[]).filter((r) => !has(q, "campus_id") || r.campus.id === q.campus_id),
  ],
  [
    /^\/shipments$/,
    (d, q) =>
      limit(
        (d.shipments as Row[]).filter(
          (s) =>
            (!has(q, "status") || s.status === q.status) &&
            (!has(q, "campus_id") || s.campus.id === q.campus_id) &&
            (!has(q, "event_id") || s.event?.id === q.event_id) &&
            (!isTrue(q.assigned_to_me) || s.assignee?.id === d.me.id),
        ),
        q,
      ),
  ],
  [/^\/shipments\/([\w-]+)$/, (d, _q, id) => byId(d.shipments as Row[], id)],
  [
    /^\/students$/,
    (d, q) =>
      limit(
        (d.students as Row[]).filter(
          (s) =>
            (!has(q, "campus_id") || s.campus?.id === q.campus_id) &&
            (!has(q, "q") || contains(s.full_name, String(q.q)) || contains(s.email, String(q.q))),
        ),
        q,
      ),
  ],
  [/^\/students\/([\w-]+)$/, (d, _q, id) => byId(d.students as Row[], id)],
  [
    /^\/certifications$/,
    (d, q) => (d.certifications as Row[]).filter((c) => isTrue(q.include_inactive) || c.is_active),
  ],
  [
    /^\/exams$/,
    (d, q) =>
      limit(
        (d.exams as Row[]).filter(
          (e) =>
            (!has(q, "status") || e.status === q.status) &&
            (!isTrue(q.open_only) || !["notified", "cancelled"].includes(e.status)) &&
            (!has(q, "kind") || e.kind === q.kind) &&
            (!has(q, "source") || e.source === q.source) &&
            (!isTrue(q.assigned_to_me) || e.assignee?.id === d.me.id) &&
            (!has(q, "student_id") || e.student.id === q.student_id) &&
            (!has(q, "certification_id") || e.certification.id === q.certification_id),
        ),
        q,
      ),
  ],
  [/^\/exams\/([\w-]+)$/, (d, _q, id) => byId(d.exams as Row[], id)],
];

// --- Entrada desde el cliente ---

export function demoRefresh(): TokenResponse | null {
  const data = currentUser();
  return data ? tokenFor(data) : null;
}

export async function demoRequest(
  path: string,
  options: { method?: string; body?: unknown; query?: Query },
): Promise<unknown> {
  await new Promise((resolve) => setTimeout(resolve, 120)); // que se note que «carga»
  const method = options.method ?? "GET";

  if (path === "/auth/login") {
    const email = String((options.body as { email?: string })?.email ?? "").toLowerCase();
    const data = snapshot()[email];
    if (!data) {
      throw new ApiError(401, `En la demo, entra con ${DEMO_USERS.join(", ")} (cualquier contraseña).`);
    }
    try {
      sessionStorage.setItem(SESSION_KEY, email);
    } catch {
      // Sin sessionStorage la sesión dura hasta recargar.
    }
    return tokenFor(data);
  }
  if (path === "/auth/logout") {
    try {
      sessionStorage.removeItem(SESSION_KEY);
    } catch {
      // nada que borrar
    }
    return undefined;
  }

  const data = currentUser();
  if (!data) throw new ApiError(401, "Tu sesión ha caducado. Vuelve a iniciar sesión.");
  if (method !== "GET") throw new ApiError(400, READ_ONLY);

  for (const [pattern, handler] of ROUTES) {
    const match = pattern.exec(path);
    if (match) return structuredClone(handler(data, options.query ?? {}, match[1] ?? ""));
  }
  throw new ApiError(404, "No disponible en la demo");
}
