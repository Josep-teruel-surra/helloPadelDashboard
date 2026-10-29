import type {
  EventKind,
  EventStatus,
  MovementKind,
  ProductCategory,
  ShipmentStatus,
} from "@/api/types";

export type Tone = "neutral" | "brand" | "red" | "amber" | "green" | "blue";

export const EVENT_KIND_LABELS: Record<EventKind, string> = {
  campus: "Campus",
  coach_training: "Formación de coaches",
  exam: "Examen presencial",
  other: "Otro",
};

export const EVENT_STATUS: Record<EventStatus, { label: string; tone: Tone }> = {
  planned: { label: "Planificado", tone: "neutral" },
  confirmed: { label: "Confirmado", tone: "blue" },
  done: { label: "Hecho", tone: "green" },
  cancelled: { label: "Cancelado", tone: "red" },
};

export const SHIPMENT_STATUS: Record<ShipmentStatus, { label: string; tone: Tone }> = {
  preparing: { label: "Preparando", tone: "amber" },
  shipped: { label: "Enviado", tone: "blue" },
  delivered: { label: "Entregado", tone: "green" },
  incident: { label: "Incidencia", tone: "red" },
  cancelled: { label: "Cancelado", tone: "neutral" },
};

export const CATEGORY_LABELS: Record<ProductCategory, string> = {
  clothing: "Ropa",
  book: "Libros",
  other: "Otros",
};

export const MOVEMENT_KIND_LABELS: Record<MovementKind, string> = {
  restock: "Entrada",
  shipment: "Envío",
  adjustment: "Ajuste",
  return: "Devolución",
};

export function options<T extends string>(labels: Record<T, string | { label: string }>) {
  return (Object.keys(labels) as T[]).map((value) => {
    const entry = labels[value];
    return { value, label: typeof entry === "string" ? entry : entry.label };
  });
}
