import { useMutation } from "@tanstack/react-query";
import { ArrowLeft, ExternalLink, PackageCheck, Pencil, Trash2, TriangleAlert } from "lucide-react";
import { useState } from "react";
import type { ReactNode } from "react";
import { Link, useNavigate, useParams } from "react-router";

import { shipmentsApi } from "@/api/endpoints";
import { LOGISTICS_KEYS, useShipment } from "@/api/queries";
import type { Shipment, ShipmentStatus } from "@/api/types";
import { AddressBlock } from "@/components/ui/AddressBlock";
import { Button } from "@/components/ui/Button";
import { CountryFlag } from "@/components/ui/Country";
import { ErrorAlert } from "@/components/ui/Feedback";
import { Card } from "@/components/ui/Layout";
import { Modal } from "@/components/ui/Modal";
import { Spinner } from "@/components/ui/Spinner";
import { formatDate, formatDateTime, formatMoney } from "@/lib/format";
import { useInvalidate } from "@/lib/useInvalidate";
import { Markdown } from "@/features/notes/Markdown";
import { EditItemsForm, ShipmentDetailsForm, StatusForm } from "./ShipmentForms";
import { ShipmentStatusBadge } from "./ShipmentRow";

// Acciones disponibles en cada estado (el backend valida las mismas transiciones).
const ACTIONS: Record<ShipmentStatus, { to: ShipmentStatus; label: string; primary?: boolean }[]> = {
  preparing: [
    { to: "shipped", label: "Marcar como enviado", primary: true },
    { to: "cancelled", label: "Cancelar" },
  ],
  shipped: [
    { to: "delivered", label: "Marcar como entregado", primary: true },
    { to: "incident", label: "Incidencia" },
    { to: "cancelled", label: "Cancelar" },
  ],
  incident: [
    { to: "delivered", label: "Marcar como entregado", primary: true },
    { to: "shipped", label: "Reenviado" },
    { to: "cancelled", label: "Cancelar" },
  ],
  delivered: [{ to: "incident", label: "Incidencia" }],
  cancelled: [],
};

type Dialog = { kind: "status"; to: ShipmentStatus } | { kind: "items" } | { kind: "details" } | null;

function Detail({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <dt className="text-xs text-stone-500">{label}</dt>
      <dd className="text-sm font-medium">{children}</dd>
    </div>
  );
}

function Timeline({ shipment }: { shipment: Shipment }) {
  return (
    <dl className="grid grid-cols-2 gap-3">
      <Detail label="Creado">{formatDateTime(shipment.created_at)} · {shipment.created_by.full_name}</Detail>
      <Detail label="Lo prepara">{shipment.assignee?.full_name ?? "Sin asignar"}</Detail>
      <Detail label="Lo necesitan antes del">{shipment.needed_by ? formatDate(shipment.needed_by) : "–"}</Detail>
      <Detail label="Enviado">{shipment.shipped_at ? formatDateTime(shipment.shipped_at) : "–"}</Detail>
      <Detail label="Entregado">{shipment.delivered_at ? formatDateTime(shipment.delivered_at) : "–"}</Detail>
      <Detail label="Coste">
        {shipment.cost_amount ? formatMoney(shipment.cost_amount, shipment.cost_currency) : "–"}
      </Detail>
    </dl>
  );
}

export function ShipmentDetailPage() {
  const { shipmentId = "" } = useParams();
  const navigate = useNavigate();
  const invalidate = useInvalidate();
  const shipment = useShipment(shipmentId);
  const [dialog, setDialog] = useState<Dialog>(null);

  const remove = useMutation({
    mutationFn: () => shipmentsApi.remove(shipmentId),
    onSuccess: async () => {
      await invalidate(...LOGISTICS_KEYS);
      navigate("/envios", { replace: true });
    },
  });

  const back = (
    <Link to="/envios" className="mb-4 inline-flex items-center gap-1.5 text-sm font-medium text-stone-500 hover:text-stone-900">
      <ArrowLeft className="size-4" aria-hidden />
      Envíos
    </Link>
  );

  if (shipment.isPending) return <Spinner />;
  if (shipment.isError) {
    return (
      <>
        {back}
        <ErrorAlert error={shipment.error} />
      </>
    );
  }
  const data = shipment.data;
  const close = () => setDialog(null);
  const dialogTitle =
    dialog?.kind === "status"
      ? `${ACTIONS[data.status].find((a) => a.to === dialog.to)?.label ?? ""} · envío #${data.number}`
      : dialog?.kind === "items"
        ? "Contenido del envío"
        : "Datos del envío";

  return (
    <>
      {back}
      <div className="mb-6 flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <h1 className="flex flex-wrap items-center gap-2 text-2xl font-extrabold tracking-tight">
            Envío #{data.number}
            <ShipmentStatusBadge shipment={data} />
          </h1>
          <p className="mt-1 text-sm text-stone-500">
            <Link to={`/campus/${data.campus.id}`} className="hover:underline">
              <CountryFlag code={data.campus.country_code} /> {data.campus.name}
            </Link>
            {data.event && (
              <>
                {" · "}
                <Link to={`/eventos/${data.event.id}`} className="text-amber-700 hover:underline">
                  {data.event.title}
                </Link>
              </>
            )}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {ACTIONS[data.status].map((action) => (
            <Button
              key={action.to}
              variant={action.primary ? "primary" : "secondary"}
              onClick={() => setDialog({ kind: "status", to: action.to })}
            >
              {action.primary && <PackageCheck className="size-4" aria-hidden />}
              {action.label}
            </Button>
          ))}
          {data.can_delete && (
            <Button
              variant="ghost"
              loading={remove.isPending}
              onClick={() => window.confirm(`¿Borrar el envío #${data.number}? Se libera el material apartado.`) && remove.mutate()}
              className="hover:bg-red-50 hover:text-red-700"
            >
              <Trash2 className="size-4" aria-hidden />
              Borrar
            </Button>
          )}
        </div>
      </div>

      <ErrorAlert error={remove.error} className="mb-4" />
      {data.stock_warnings.length > 0 && (
        <div role="alert" className="mb-4 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
          <p className="flex items-center gap-2 font-semibold">
            <TriangleAlert className="size-4" aria-hidden />
            No hay stock suficiente para todo lo apartado
          </p>
          <ul className="mt-1 list-disc pl-6">
            {data.stock_warnings.map((w) => (
              <li key={w}>{w}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-3">
        <Card
          className="lg:col-span-2"
          title={`Contenido · ${data.total_units} uds`}
          actions={
            data.status === "preparing" && (
              <Button size="sm" variant="secondary" onClick={() => setDialog({ kind: "items" })}>
                <Pencil className="size-4" aria-hidden />
                Cambiar
              </Button>
            )
          }
        >
          <table className="w-full text-sm">
            <tbody className="divide-y divide-stone-100">
              {data.items.map((item) => (
                <tr key={item.variant_id}>
                  <td className="py-2">{item.product_name}</td>
                  <td className="py-2 text-stone-500">{item.label}</td>
                  <td className="py-2 text-right font-semibold tabular-nums">{item.quantity}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>

        <Card title="Destino">
          <AddressBlock address={data.shipping_address} />
          {(data.carrier || data.tracking_number) && (
            <p className="mt-3 text-sm">
              <span className="text-stone-500">{data.carrier ?? "Seguimiento"}:</span>{" "}
              {data.tracking_url ? (
                <a href={data.tracking_url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 font-medium text-amber-700 hover:underline">
                  {data.tracking_number ?? "Ver seguimiento"}
                  <ExternalLink className="size-3.5" aria-hidden />
                </a>
              ) : (
                <span className="font-medium">{data.tracking_number}</span>
              )}
            </p>
          )}
        </Card>

        <Card
          className="lg:col-span-3"
          title="Detalles"
          actions={
            <Button size="sm" variant="secondary" onClick={() => setDialog({ kind: "details" })}>
              <Pencil className="size-4" aria-hidden />
              Editar
            </Button>
          }
        >
          <Timeline shipment={data} />
          {data.notes_md.trim() && (
            <div className="mt-4 border-t border-stone-100 pt-3">
              <Markdown content={data.notes_md} className="prose-sm" />
            </div>
          )}
        </Card>
      </div>

      <Modal open={dialog !== null} onClose={close} title={dialogTitle}>
        {dialog?.kind === "status" && <StatusForm shipment={data} status={dialog.to} onDone={close} />}
        {dialog?.kind === "items" && <EditItemsForm shipment={data} onDone={close} />}
        {dialog?.kind === "details" && <ShipmentDetailsForm shipment={data} onDone={close} />}
      </Modal>
    </>
  );
}
