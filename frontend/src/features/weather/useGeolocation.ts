import { useEffect, useState } from "react";

import type { Coordinates } from "@/api/endpoints";

export type GeolocationState =
  | { status: "pending" }
  | { status: "granted"; coords: Coordinates }
  // Denegada, no disponible o caducada: se usa la ubicación por defecto (Barcelona).
  | { status: "fallback" };

const TIMEOUT_MS = 8000;

export function useGeolocation(): GeolocationState {
  const [state, setState] = useState<GeolocationState>(() =>
    "geolocation" in navigator ? { status: "pending" } : { status: "fallback" },
  );

  useEffect(() => {
    if (!("geolocation" in navigator)) return;
    let cancelled = false;
    navigator.geolocation.getCurrentPosition(
      ({ coords }) =>
        !cancelled &&
        setState({ status: "granted", coords: { lat: coords.latitude, lon: coords.longitude } }),
      () => !cancelled && setState({ status: "fallback" }),
      // Baja precisión basta para el tiempo y es más rápida; reutilizamos una posición de <30 min.
      { enableHighAccuracy: false, timeout: TIMEOUT_MS, maximumAge: 30 * 60_000 },
    );
    return () => {
      cancelled = true;
    };
  }, []);

  return state;
}
