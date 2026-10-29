import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Pencil, Plus, Users } from "lucide-react";
import { useState } from "react";
import type { FormEvent } from "react";

import { usersApi } from "@/api/endpoints";
import type { UserUpdateInput } from "@/api/endpoints";
import { useUsers } from "@/api/queries";
import type { Role, User } from "@/api/types";
import { useAuth, useCurrentUser } from "@/auth/AuthContext";
import { Button, IconButton } from "@/components/ui/Button";
import { Badge, EmptyState, ErrorAlert } from "@/components/ui/Feedback";
import { Field, inputClass } from "@/components/ui/Field";
import { PageHeader } from "@/components/ui/Layout";
import { Modal } from "@/components/ui/Modal";
import { Spinner } from "@/components/ui/Spinner";
import { cn } from "@/lib/cn";
import { relativeTime } from "@/lib/format";

const ROLE_LABELS: Record<Role, string> = { admin: "Administrador", worker: "Equipo" };

export function UsersPage() {
  const users = useUsers(true);
  const [editing, setEditing] = useState<User | null>(null);
  const [creating, setCreating] = useState(false);

  return (
    <>
      <PageHeader
        title="Usuarios"
        description="Cuentas del equipo. Solo los administradores pueden gestionarlas."
        actions={
          <Button onClick={() => setCreating(true)}>
            <Plus className="size-4" aria-hidden />
            Nuevo usuario
          </Button>
        }
      />

      <ErrorAlert error={users.error} className="mb-4" />

      {users.isPending ? (
        <Spinner />
      ) : users.data && users.data.length > 0 ? (
        <ul className="divide-y divide-stone-100 overflow-hidden rounded-2xl border border-stone-200 bg-white">
          {users.data.map((user) => (
            <li
              key={user.id}
              className={cn("flex items-center gap-3 px-4 py-3", !user.is_active && "opacity-60")}
            >
              <div className="min-w-0 flex-1">
                <p className="flex flex-wrap items-center gap-2 font-semibold">
                  {user.full_name}
                  <Badge tone={user.role === "admin" ? "brand" : "neutral"}>
                    {ROLE_LABELS[user.role]}
                  </Badge>
                  {!user.is_active && <Badge tone="red">Desactivado</Badge>}
                </p>
                <p className="truncate text-sm text-stone-500">{user.email}</p>
              </div>
              <p className="hidden text-right text-xs text-stone-500 sm:block">
                {user.last_login_at ? `Último acceso ${relativeTime(user.last_login_at)}` : "Nunca ha entrado"}
              </p>
              <IconButton label={`Editar a ${user.full_name}`} onClick={() => setEditing(user)}>
                <Pencil className="size-4" />
              </IconButton>
            </li>
          ))}
        </ul>
      ) : (
        !users.error && <EmptyState icon={<Users className="size-8" />} title="No hay usuarios" />
      )}

      <Modal
        open={creating || editing !== null}
        onClose={() => {
          setCreating(false);
          setEditing(null);
        }}
        title={editing ? `Editar a ${editing.full_name}` : "Nuevo usuario"}
      >
        <UserForm
          key={editing?.id ?? "new"}
          user={editing}
          onDone={() => {
            setCreating(false);
            setEditing(null);
          }}
        />
      </Modal>
    </>
  );
}

function UserForm({ user, onDone }: { user: User | null; onDone: () => void }) {
  const queryClient = useQueryClient();
  const me = useCurrentUser();
  const { setUser } = useAuth();
  const isSelf = user?.id === me.id;

  const [fullName, setFullName] = useState(user?.full_name ?? "");
  const [email, setEmail] = useState(user?.email ?? "");
  const [role, setRole] = useState<Role>(user?.role ?? "worker");
  const [isActive, setIsActive] = useState(user?.is_active ?? true);
  const [password, setPassword] = useState("");

  const save = useMutation({
    mutationFn: () => {
      if (!user) return usersApi.create({ full_name: fullName, email, role, password });
      const changes: UserUpdateInput = {};
      if (fullName !== user.full_name) changes.full_name = fullName;
      if (email !== user.email) changes.email = email;
      if (role !== user.role) changes.role = role;
      if (isActive !== user.is_active) changes.is_active = isActive;
      if (password) changes.password = password;
      return usersApi.update(user.id, changes);
    },
    onSuccess: async (saved) => {
      if (saved.id === me.id) setUser(saved);
      await queryClient.invalidateQueries({ queryKey: ["users"] });
      onDone();
    },
  });

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    save.mutate();
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <ErrorAlert error={save.error} />

      <Field label="Nombre completo" htmlFor="user-name">
        <input
          id="user-name"
          required
          maxLength={120}
          autoFocus
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          className={inputClass}
        />
      </Field>

      <Field label="Email" htmlFor="user-email">
        <input
          id="user-email"
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className={inputClass}
        />
      </Field>

      <Field
        label={user ? "Nueva contraseña" : "Contraseña"}
        htmlFor="user-password"
        hint={
          user
            ? "Déjala vacía para no cambiarla. Si la cambias, se cerrarán sus sesiones."
            : "Mínimo 8 caracteres. Compártela con la persona por un canal seguro."
        }
      >
        <input
          id="user-password"
          type="password"
          autoComplete="new-password"
          required={!user}
          minLength={8}
          maxLength={128}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className={inputClass}
        />
      </Field>

      <Field
        label="Rol"
        htmlFor="user-role"
        hint={isSelf ? "No puedes quitarte el rol de administrador." : undefined}
      >
        <select
          id="user-role"
          value={role}
          disabled={isSelf}
          onChange={(e) => setRole(e.target.value as Role)}
          className={inputClass}
        >
          <option value="worker">{ROLE_LABELS.worker}</option>
          <option value="admin">{ROLE_LABELS.admin}</option>
        </select>
      </Field>

      {user && !isSelf && (
        <label className="flex cursor-pointer items-start gap-2 text-sm">
          <input
            type="checkbox"
            checked={isActive}
            onChange={(e) => setIsActive(e.target.checked)}
            className="mt-0.5 size-4 accent-amber-500"
          />
          <span>
            <span className="font-medium">Cuenta activa</span>
            <span className="block text-xs text-stone-500">
              Al desactivarla no podrá entrar y se cerrarán sus sesiones.
            </span>
          </span>
        </label>
      )}

      <div className="flex justify-end gap-2 pt-2">
        <Button variant="secondary" onClick={onDone}>
          Cancelar
        </Button>
        <Button type="submit" loading={save.isPending}>
          {user ? "Guardar" : "Crear usuario"}
        </Button>
      </div>
    </form>
  );
}
