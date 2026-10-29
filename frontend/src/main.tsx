import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { ApiError } from "@/api/client";
import { AuthProvider } from "@/auth/AuthContext";
import { App } from "./App";
import "./index.css";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      refetchOnWindowFocus: true,
      // No reintentamos errores del cliente (permisos, 404, validación).
      retry: (failureCount, error) =>
        !(error instanceof ApiError && error.status < 500) && failureCount < 2,
    },
  },
});

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <App />
      </AuthProvider>
    </QueryClientProvider>
  </StrictMode>,
);
