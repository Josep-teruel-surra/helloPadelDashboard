import { Plus, Truck } from "lucide-react";
import { useState } from "react";

import { useCampuses, useShipments } from "@/api/queries";
import type { ShipmentStatus } from "@/api/types";
import { Button } from "@/components/ui/Button";
import { EmptyState, ErrorAlert } from "@/components/ui/Feedback";
import { inlineSelectClass } from "@/components/ui/Field";
import { Card, PageHeader, Segmented } from "@/components/ui/Layout";
import { Modal } from "@/components/ui/Modal";
import { Spinner } from "@/components/ui/Spinner";
import { SHIPMENT_STATUS } from "@/lib/labels";
import { SentMaterialTable } from "./SentMaterialTable";
import { NewShipmentForm } from "./ShipmentForms";
import { ShipmentRow } from "./ShipmentRow";

type View = "shipments" | "sent";

export function ShipmentsPage() {
  const [view, setView] = useState<View>("shipments");
  const [status, setStatus] = useState<ShipmentStatus | "">("");
  const [campusId, setCampusId] = useState("");
  const [creating, setCreating] = useState(false);
  const campuses = useCampuses({ include_inactive: true });
  const shipments = useShipments({ status: status || undefined, campus_id: campusId || undefined });

  return (
    <>
      <PageHeader
        title="Envíos"
        description="Material apartado y enviado a los campus. Crear un envío es apartar su material."
        actions={
          <Button onClick={() => setCreating(true)}>
            <Plus className="size-4" aria-hidden />
            Nuevo envío
          </Button>
        }
      />

      <div className="mb-4 flex flex-wrap items-center gap-3">
        <Segmented
          label="Vista"
          options={[
            { value: "shipments", label: "Envíos" },
            { value: "sent", label: "Material por campus" },
          ]}
          value={view}
          onChange={setView}
        />
        {view === "shipments" && (
          <>
            <select
              aria-label="Estado"
              value={status}
              onChange={(e) => setStatus(e.target.value as ShipmentStatus | "")}
              className={inlineSelectClass}
            >
              <option value="">Todos los estados</option>
              {Object.entries(SHIPMENT_STATUS).map(([value, { label }]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
            <select
              aria-label="Campus"
              value={campusId}
              onChange={(e) => setCampusId(e.target.value)}
              className={inlineSelectClass}
            >
              <option value="">Todos los campus</option>
              {campuses.data?.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </>
        )}
      </div>

      {view === "sent" ? (
        <Card>
          <SentMaterialTable />
        </Card>
      ) : (
        <>
          <ErrorAlert error={shipments.error} className="mb-4" />
          {shipments.isPending ? (
            <Spinner />
          ) : shipments.data?.length ? (
            <ul className="divide-y divide-stone-100 overflow-hidden rounded-2xl border border-stone-200 bg-white">
              {shipments.data.map((shipment) => (
                <ShipmentRow key={shipment.id} shipment={shipment} />
              ))}
            </ul>
          ) : (
            !shipments.error && (
              <EmptyState
                icon={<Truck className="size-8" />}
                title="No hay envíos"
                description="Aparta material para un campus o un evento y aparecerá aquí."
              />
            )
          )}
        </>
      )}

      <Modal open={creating} onClose={() => setCreating(false)} title="Nuevo envío">
        <NewShipmentForm onDone={() => setCreating(false)} />
      </Modal>
    </>
  );
}
