import { Navigate, Outlet, useLocation } from "react-router";

import { FullPageSpinner } from "@/components/ui/Spinner";
import { useAuth } from "./AuthContext";

export function RequireAuth() {
  const { state } = useAuth();
  const location = useLocation();

  if (state.status === "loading") return <FullPageSpinner />;
  if (state.status === "anonymous") {
    return <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />;
  }
  return <Outlet />;
}

export function RequireAdmin() {
  const { state } = useAuth();
  if (state.status !== "authenticated" || state.user.role !== "admin") {
    return <Navigate to="/" replace />;
  }
  return <Outlet />;
}
