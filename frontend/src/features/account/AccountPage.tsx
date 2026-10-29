import { useMutation } from "@tanstack/react-query";
import { CircleCheck } from "lucide-react";
import { useState } from "react";
import type { FormEvent } from "react";

import { usersApi } from "@/api/endpoints";
import { useCurrentUser } from "@/auth/AuthContext";
import { Button } from "@/components/ui/Button";
import { ErrorAlert } from "@/components/ui/Feedback";
import { Field, inputClass } from "@/components/ui/Field";
import { Card, PageHeader } from "@/components/ui/Layout";

export function AccountPage() {
  const user = useCurrentUser();
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [mismatch, setMismatch] = useState(false);

  const change = useMutation({
    mutationFn: () => usersApi.changeMyPassword(current, next),
    onSuccess: () => {
      setCurrent("");
      setNext("");
      setConfirm("");
    },
  });

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (next !== confirm) {
      setMismatch(true);
      return;
    }
    setMismatch(false);
    change.mutate();
  }

  return (
    <>
      <PageHeader title="Mi cuenta" />
      <div className="grid gap-4 lg:grid-cols-2">
        <Card title="Datos">
          <dl className="space-y-3 text-sm">
            <div>
              <dt className="text-stone-500">Nombre</dt>
              <dd className="font-medium">{user.full_name}</dd>
            </div>
            <div>
              <dt className="text-stone-500">Email</dt>
              <dd className="font-medium">{user.email}</dd>
            </div>
            <div>
              <dt className="text-stone-500">Rol</dt>
              <dd className="font-medium">{user.role === "admin" ? "Administrador" : "Equipo"}</dd>
            </div>
          </dl>
          <p className="mt-4 text-xs text-stone-500">
            Para cambiar tu nombre o email, pídeselo a un administrador.
          </p>
        </Card>

        <Card title="Cambiar contraseña">
          <form onSubmit={handleSubmit} className="space-y-4">
            <ErrorAlert error={mismatch && "Las contraseñas nuevas no coinciden."} />
            <ErrorAlert error={change.error} />
            {change.isSuccess && (
              <p className="flex items-center gap-2 rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-800">
                <CircleCheck className="size-4" aria-hidden />
                Contraseña actualizada.
              </p>
            )}
            <Field label="Contraseña actual" htmlFor="pw-current">
              <input
                id="pw-current"
                type="password"
                autoComplete="current-password"
                required
                value={current}
                onChange={(e) => setCurrent(e.target.value)}
                className={inputClass}
              />
            </Field>
            <Field label="Nueva contraseña" htmlFor="pw-new" hint="Mínimo 8 caracteres.">
              <input
                id="pw-new"
                type="password"
                autoComplete="new-password"
                required
                minLength={8}
                maxLength={128}
                value={next}
                onChange={(e) => setNext(e.target.value)}
                className={inputClass}
              />
            </Field>
            <Field label="Repite la nueva contraseña" htmlFor="pw-confirm">
              <input
                id="pw-confirm"
                type="password"
                autoComplete="new-password"
                required
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                className={inputClass}
              />
            </Field>
            <Button type="submit" loading={change.isPending}>
              Cambiar contraseña
            </Button>
          </form>
        </Card>
      </div>
    </>
  );
}
