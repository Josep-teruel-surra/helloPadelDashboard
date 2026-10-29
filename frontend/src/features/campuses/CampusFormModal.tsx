import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router";

import { campusesApi } from "@/api/endpoints";
import type { CampusInput } from "@/api/endpoints";
import type { Address, Campus } from "@/api/types";
import { Button } from "@/components/ui/Button";
import { CountrySelect } from "@/components/ui/Country";
import { ErrorAlert } from "@/components/ui/Feedback";
import { Field, inputClass } from "@/components/ui/Field";
import { Modal } from "@/components/ui/Modal";
import { useInvalidate } from "@/lib/useInvalidate";

const EMPTY_ADDRESS: Address = {
  recipient: null,
  line1: null,
  line2: null,
  postal_code: null,
  city: null,
  region: null,
  country_code: null,
};

export function CampusFormModal({
  open,
  onClose,
  campus,
}: {
  open: boolean;
  onClose: () => void;
  campus?: Campus | null;
}) {
  return (
    <Modal open={open} onClose={onClose} title={campus ? "Editar campus" : "Nuevo campus"}>
      <CampusForm key={campus?.id ?? "new"} campus={campus} onDone={onClose} />
    </Modal>
  );
}

function CampusForm({ campus, onDone }: { campus?: Campus | null; onDone: () => void }) {
  const invalidate = useInvalidate();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    name: campus?.name ?? "",
    country_code: campus?.country_code ?? "",
    city: campus?.city ?? "",
    partner: campus?.partner ?? "",
    coordinator_name: campus?.coordinator_name ?? "",
    coordinator_email: campus?.coordinator_email ?? "",
    coordinator_phone: campus?.coordinator_phone ?? "",
    notes_md: campus?.notes_md ?? "",
    is_active: campus?.is_active ?? true,
  });
  const [address, setAddress] = useState<Address>(campus?.shipping_address ?? EMPTY_ADDRESS);

  const set = (field: keyof typeof form) => (value: string | boolean) =>
    setForm((prev) => ({ ...prev, [field]: value }));
  const setAddr = (field: keyof Address) => (value: string) =>
    setAddress((prev) => ({ ...prev, [field]: value || null }));

  const save = useMutation({
    mutationFn: () => {
      const hasAddress = Object.values(address).some(Boolean);
      const data: CampusInput = {
        ...form,
        partner: form.partner || null,
        coordinator_name: form.coordinator_name || null,
        coordinator_email: form.coordinator_email || null,
        coordinator_phone: form.coordinator_phone || null,
        // Si no se indica país en la dirección, se usa el del campus.
        shipping_address: hasAddress
          ? { ...address, country_code: address.country_code || form.country_code }
          : null,
      };
      return campus ? campusesApi.update(campus.id, data) : campusesApi.create(data);
    },
    onSuccess: async (saved) => {
      await invalidate(["campuses"], ["events"], ["shipments"]);
      onDone();
      if (!campus) navigate(`/campus/${saved.id}`);
    },
  });

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    save.mutate();
  }

  const text = (
    id: string,
    label: string,
    value: string,
    onChange: (v: string) => void,
    props: { required?: boolean; type?: string; maxLength?: number } = {},
  ) => (
    <Field label={label} htmlFor={id}>
      <input
        id={id}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={inputClass}
        maxLength={props.maxLength ?? 120}
        {...props}
      />
    </Field>
  );

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <ErrorAlert error={save.error} />

      {text("campus-name", "Nombre", form.name, set("name"), { required: true })}
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="País" htmlFor="campus-country">
          <CountrySelect
            id="campus-country"
            required
            value={form.country_code}
            onChange={set("country_code")}
          />
        </Field>
        {text("campus-city", "Ciudad", form.city, set("city"), { required: true })}
      </div>
      {text("campus-partner", "Partner (federación, club…)", form.partner, set("partner"), {
        maxLength: 160,
      })}

      <fieldset className="space-y-3 rounded-xl border border-stone-200 p-3">
        <legend className="px-1 text-sm font-semibold text-stone-700">Coordinador</legend>
        {text("coord-name", "Nombre", form.coordinator_name, set("coordinator_name"))}
        <div className="grid gap-3 sm:grid-cols-2">
          {text("coord-email", "Email", form.coordinator_email, set("coordinator_email"), {
            type: "email",
            maxLength: 255,
          })}
          {text("coord-phone", "Teléfono", form.coordinator_phone, set("coordinator_phone"), {
            type: "tel",
            maxLength: 40,
          })}
        </div>
      </fieldset>

      <fieldset className="space-y-3 rounded-xl border border-stone-200 p-3">
        <legend className="px-1 text-sm font-semibold text-stone-700">Dirección de envío</legend>
        {text("addr-recipient", "Destinatario", address.recipient ?? "", setAddr("recipient"), {
          maxLength: 160,
        })}
        {text("addr-line1", "Dirección", address.line1 ?? "", setAddr("line1"), { maxLength: 200 })}
        {text("addr-line2", "Dirección (línea 2)", address.line2 ?? "", setAddr("line2"), {
          maxLength: 200,
        })}
        <div className="grid gap-3 sm:grid-cols-3">
          {text("addr-postal", "Código postal", address.postal_code ?? "", setAddr("postal_code"))}
          {text("addr-city", "Ciudad", address.city ?? "", setAddr("city"))}
          {text("addr-region", "Región", address.region ?? "", setAddr("region"))}
        </div>
        <p className="text-xs text-stone-500">
          Se copia en cada envío al crearlo. Si la dejas vacía, la indicarás en cada envío.
        </p>
      </fieldset>

      <Field label="Notas" htmlFor="campus-notes" hint="Admite markdown.">
        <textarea
          id="campus-notes"
          rows={3}
          value={form.notes_md}
          onChange={(e) => set("notes_md")(e.target.value)}
          className={inputClass}
        />
      </Field>

      {campus && (
        <label className="flex cursor-pointer items-start gap-2 text-sm">
          <input
            type="checkbox"
            checked={form.is_active}
            onChange={(e) => set("is_active")(e.target.checked)}
            className="mt-0.5 size-4 accent-amber-500"
          />
          <span>
            <span className="font-medium">Campus activo</span>
            <span className="block text-xs text-stone-500">
              Los desactivados no aparecen al crear eventos o envíos, pero conservan su historial.
            </span>
          </span>
        </label>
      )}

      <div className="flex justify-end gap-2 pt-2">
        <Button variant="secondary" onClick={onDone}>
          Cancelar
        </Button>
        <Button type="submit" loading={save.isPending}>
          {campus ? "Guardar" : "Crear campus"}
        </Button>
      </div>
    </form>
  );
}
