import { LogOut, Menu, UserRound, X } from "lucide-react";
import { useEffect, useState } from "react";
import { Link, NavLink, Outlet, useLocation } from "react-router";

import { useAuth, useCurrentUser } from "@/auth/AuthContext";
import { cn } from "@/lib/cn";
import { Logo } from "./Logo";
import { NAV_ITEMS } from "./navigation";

function Sidebar({ onNavigate }: { onNavigate?: () => void }) {
  const user = useCurrentUser();
  const { logout } = useAuth();
  const items = NAV_ITEMS.filter((item) => !item.adminOnly || user.role === "admin");

  return (
    <div className="flex h-full flex-col bg-carbon text-stone-300">
      <div className="flex h-16 items-center px-5">
        <Link to="/" onClick={onNavigate} className="text-lg text-white">
          <Logo />
        </Link>
      </div>

      <nav aria-label="Principal" className="flex-1 space-y-1 px-3 py-2">
        {items.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            onClick={onNavigate}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-semibold transition-colors",
                isActive ? "bg-brand text-carbon" : "hover:bg-carbon-2 hover:text-white",
              )
            }
          >
            <Icon className="size-5" aria-hidden />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="border-t border-carbon-line p-3">
        <NavLink
          to="/cuenta"
          onClick={onNavigate}
          className={({ isActive }) =>
            cn(
              "flex items-center gap-3 rounded-lg px-3 py-2 transition-colors",
              isActive ? "bg-carbon-2 text-white" : "hover:bg-carbon-2 hover:text-white",
            )
          }
        >
          <span className="flex size-8 items-center justify-center rounded-full bg-carbon-line text-brand">
            <UserRound className="size-4" aria-hidden />
          </span>
          <span className="min-w-0">
            <span className="block truncate text-sm font-semibold text-white">{user.full_name}</span>
            <span className="block text-xs text-stone-400">
              {user.role === "admin" ? "Administrador" : "Equipo"} · Mi cuenta
            </span>
          </span>
        </NavLink>
        <button
          type="button"
          onClick={() => void logout()}
          className="mt-1 flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium hover:bg-carbon-2 hover:text-white"
        >
          <LogOut className="size-4" aria-hidden />
          Cerrar sesión
        </button>
      </div>
    </div>
  );
}

export function AppLayout() {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const location = useLocation();

  useEffect(() => setDrawerOpen(false), [location.pathname]);

  useEffect(() => {
    if (!drawerOpen) return;
    const onKey = (event: KeyboardEvent) => event.key === "Escape" && setDrawerOpen(false);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [drawerOpen]);

  return (
    <div className="min-h-dvh lg:pl-64">
      {/* Escritorio: barra lateral fija */}
      <aside className="fixed inset-y-0 left-0 hidden w-64 lg:block">
        <Sidebar />
      </aside>

      {/* Móvil: barra superior + cajón */}
      <header className="sticky top-0 z-20 flex h-14 items-center gap-3 bg-carbon px-4 text-white lg:hidden">
        <button
          type="button"
          onClick={() => setDrawerOpen(true)}
          aria-label="Abrir menú"
          aria-expanded={drawerOpen}
          className="-ml-1 rounded-lg p-1.5 hover:bg-carbon-2"
        >
          <Menu className="size-6" />
        </button>
        <Link to="/">
          <Logo />
        </Link>
      </header>

      {drawerOpen && (
        <div className="fixed inset-0 z-30 lg:hidden" role="dialog" aria-modal="true" aria-label="Menú">
          <div className="absolute inset-0 bg-black/50" onClick={() => setDrawerOpen(false)} />
          <div className="absolute inset-y-0 left-0 w-72 max-w-[85vw] shadow-xl">
            <button
              type="button"
              onClick={() => setDrawerOpen(false)}
              aria-label="Cerrar menú"
              className="absolute top-4 right-3 z-10 rounded-lg p-1 text-stone-400 hover:text-white"
            >
              <X className="size-5" />
            </button>
            <Sidebar onNavigate={() => setDrawerOpen(false)} />
          </div>
        </div>
      )}

      <main className="mx-auto max-w-6xl px-4 py-6 sm:px-6 lg:px-8 lg:py-8">
        <Outlet />
      </main>
    </div>
  );
}
