import { useQueryClient } from "@tanstack/react-query";
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";

import { refreshSession, setAccessToken, setSessionExpiredHandler } from "@/api/client";
import { authApi } from "@/api/endpoints";
import type { User } from "@/api/types";

type AuthState =
  | { status: "loading" }
  | { status: "anonymous" }
  | { status: "authenticated"; user: User };

interface AuthContextValue {
  state: AuthState;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  setUser: (user: User) => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient();
  const [state, setState] = useState<AuthState>({ status: "loading" });

  useEffect(() => {
    setSessionExpiredHandler(() => {
      queryClient.clear();
      setState({ status: "anonymous" });
    });
    // Al cargar la app intentamos recuperar la sesión con la cookie de refresh.
    void refreshSession().then((data) =>
      setState(data ? { status: "authenticated", user: data.user } : { status: "anonymous" }),
    );
    return () => setSessionExpiredHandler(null);
  }, [queryClient]);

  const login = useCallback(async (email: string, password: string) => {
    const data = await authApi.login(email, password);
    setAccessToken(data.access_token);
    setState({ status: "authenticated", user: data.user });
  }, []);

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } finally {
      setAccessToken(null);
      queryClient.clear();
      setState({ status: "anonymous" });
    }
  }, [queryClient]);

  const setUser = useCallback((user: User) => setState({ status: "authenticated", user }), []);

  const value = useMemo(() => ({ state, login, logout, setUser }), [state, login, logout, setUser]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth debe usarse dentro de <AuthProvider>");
  return ctx;
}

/** Usuario actual. Solo para componentes que se renderizan tras <RequireAuth>. */
export function useCurrentUser(): User {
  const { state } = useAuth();
  if (state.status !== "authenticated") throw new Error("No hay sesión iniciada");
  return state.user;
}
