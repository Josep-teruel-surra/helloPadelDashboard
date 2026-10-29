import { useState } from "react";
import type { FormEvent } from "react";
import { Navigate, useLocation, useNavigate } from "react-router";

import { useAuth } from "@/auth/AuthContext";
import { Logo } from "@/components/layout/Logo";
import { Button } from "@/components/ui/Button";
import { ErrorAlert } from "@/components/ui/Feedback";
import { Field, inputClass } from "@/components/ui/Field";
import { FullPageSpinner } from "@/components/ui/Spinner";

export function LoginPage() {
  const { state, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: string } | null)?.from ?? "/";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<unknown>(null);
  const [submitting, setSubmitting] = useState(false);

  if (state.status === "loading") return <FullPageSpinner />;
  if (state.status === "authenticated") return <Navigate to={from} replace />;

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await login(email, password);
      navigate(from, { replace: true });
    } catch (err) {
      setError(err);
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-dvh items-center justify-center bg-carbon px-4 py-10">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center text-2xl text-white">
          <Logo />
          <p className="mt-2 text-sm font-medium text-stone-400">Dashboard del equipo</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 rounded-2xl bg-white p-6 shadow-xl">
          <h1 className="text-xl font-bold">Inicia sesión</h1>
          <ErrorAlert error={error} />
          <Field label="Email" htmlFor="email">
            <input
              id="email"
              type="email"
              autoComplete="email"
              required
              autoFocus
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className={inputClass}
            />
          </Field>
          <Field label="Contraseña" htmlFor="password">
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className={inputClass}
            />
          </Field>
          <Button type="submit" loading={submitting} className="w-full">
            Entrar
          </Button>
          <p className="text-center text-xs text-stone-500">
            ¿No tienes cuenta? Pídesela a un administrador.
          </p>
        </form>
      </div>
    </div>
  );
}
