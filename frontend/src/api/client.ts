import type { TokenResponse } from "./types";

// El access token vive solo en memoria; el refresh token va en una cookie httpOnly.
let accessToken: string | null = null;
let refreshInFlight: Promise<TokenResponse | null> | null = null;
let onSessionExpired: (() => void) | null = null;

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
  }
}

export function setAccessToken(token: string | null): void {
  accessToken = token;
}

export function setSessionExpiredHandler(handler: (() => void) | null): void {
  onSessionExpired = handler;
}

type QueryValue = string | number | boolean | null | undefined;

interface RequestOptions {
  method?: "GET" | "POST" | "PATCH" | "DELETE";
  body?: unknown;
  query?: Record<string, QueryValue>;
  signal?: AbortSignal;
}

function buildUrl(path: string, query?: Record<string, QueryValue>): string {
  const params = new URLSearchParams();
  for (const [key, value] of Object.entries(query ?? {})) {
    if (value !== undefined && value !== null && value !== "") params.set(key, String(value));
  }
  const qs = params.toString();
  return `/api${path}${qs ? `?${qs}` : ""}`;
}

interface ValidationIssue {
  msg: string;
}

async function toApiError(resp: Response): Promise<ApiError> {
  let message: string | null = null;
  try {
    const body = (await resp.json()) as { detail?: string | ValidationIssue[] };
    if (typeof body.detail === "string") {
      message = body.detail;
    } else if (Array.isArray(body.detail)) {
      message = body.detail.map((issue) => issue.msg.replace(/^Value error, /, "")).join(". ");
    }
  } catch {
    // Respuesta sin JSON: usamos el mensaje genérico.
  }
  return new ApiError(resp.status, message ?? "Ha ocurrido un error inesperado. Inténtalo de nuevo.");
}

/** Pide un access token nuevo con la cookie de refresh. Las llamadas simultáneas comparten petición. */
export function refreshSession(): Promise<TokenResponse | null> {
  refreshInFlight ??= (async () => {
    try {
      const resp = await fetch("/api/auth/refresh", { method: "POST", credentials: "same-origin" });
      if (!resp.ok) {
        accessToken = null;
        return null;
      }
      const data = (await resp.json()) as TokenResponse;
      accessToken = data.access_token;
      return data;
    } catch {
      return null;
    } finally {
      refreshInFlight = null;
    }
  })();
  return refreshInFlight;
}

export async function api<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const url = buildUrl(path, options.query);
  const send = () =>
    fetch(url, {
      method: options.method ?? "GET",
      headers: {
        ...(options.body !== undefined && { "Content-Type": "application/json" }),
        ...(accessToken && { Authorization: `Bearer ${accessToken}` }),
      },
      body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
      credentials: "same-origin",
      signal: options.signal,
    });

  let resp = await send();

  // Access token caducado: renovamos una vez y repetimos la petición.
  if (resp.status === 401 && !path.startsWith("/auth/")) {
    if (await refreshSession()) {
      resp = await send();
    } else {
      onSessionExpired?.();
      throw new ApiError(401, "Tu sesión ha caducado. Vuelve a iniciar sesión.");
    }
  }

  if (!resp.ok) throw await toApiError(resp);
  if (resp.status === 204) return undefined as T;
  return (await resp.json()) as T;
}

export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  return "No se ha podido conectar con el servidor.";
}
