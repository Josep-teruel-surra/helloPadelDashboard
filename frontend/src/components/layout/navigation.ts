import { House, NotebookPen, SquareCheckBig, Users } from "lucide-react";
import type { LucideIcon } from "lucide-react";

export interface NavItem {
  to: string;
  label: string;
  icon: LucideIcon;
  adminOnly?: boolean;
}

// Añade aquí cada sección nueva (inventario, reuniones, calendario, redes…).
export const NAV_ITEMS: NavItem[] = [
  { to: "/", label: "Inicio", icon: House },
  { to: "/tareas", label: "Tareas", icon: SquareCheckBig },
  { to: "/notas", label: "Notas", icon: NotebookPen },
  { to: "/usuarios", label: "Usuarios", icon: Users, adminOnly: true },
];
