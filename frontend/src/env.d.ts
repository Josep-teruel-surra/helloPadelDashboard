/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** URL del backend si no está en el mismo origen (p. ej. con el frontend en GitHub Pages). */
  readonly VITE_API_URL?: string;
}
