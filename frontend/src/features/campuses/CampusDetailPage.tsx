import { ArrowLeft, CalendarDays, Mail, Package, Pencil, Phone, Truck } from "lucide-react";
import { useState } from "react";
import { Link, useParams } from "react-router";

import { useCampus, useEvents, useShipments } from "@/api/queries";
import { AddressBlock } from "@/components/ui/AddressBlock";
import { Button } from "@/components/ui/Button";
import { CountryFlag } from "@/components/ui/Country";
import { Badge, ErrorAlert } from "@/components/ui/Feedback";
import { Card } from "@/components/ui/Layout";
import { Spinner } from "@/components/ui/Spinner";
import { countryName } from "@/lib/countries";
import { EventRow } from "@/features/events/EventRow";
import { Markdown } from "@/features/notes/Markdown";
import { SentMaterialTable } from "@/features/shipments/SentMaterialTable";
import { ShipmentRow } from "@/features/shipments/ShipmentRow";
import { CampusFormModal } from "./CampusFormModal";

export function CampusDetailPage() {
  const { campusId = "" } = useParams();
  const campus = useCampus(campusId);
  const upcoming = useEvents({ campus_id: campusId, when: "upcoming" });
  const past = useEvents({ campus_id: campusId, when: "past", limit: 5 });
  const shipments = useShipments({ campus_id: campusId, limit: 10 });
  const [editing, setEditing] = useState(false);

  const back = (
    <Link
      to="/campus"
      className="mb-4 inline-flex items-center gap-1.5 text-sm font-medium text-stone-500 hover:text-stone-900"
    >
      <ArrowLeft className="size-4" aria-hidden />
      Campus
    </Link>
  );

  if (campus.isPending) return <Spinner />;
  if (campus.isError) {
    return (
      <>
        {back}
        <ErrorAlert error={campus.error} />
      </>
    );
  }
  const data = campus.data;

  return (
    <>
      {back}
      <div className="mb-6 flex flex-wrap items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <CountryFlag code={data.country_code} className="text-4xl leading-none" />
          <div>
            <h1 className="flex flex-wrap items-center gap-2 text-2xl font-extrabold tracking-tight">
              {data.name}
              {!data.is_active && <Badge tone="red">Desactivado</Badge>}
            </h1>
            <p className="text-sm text-stone-500">
              {data.city} · {countryName(data.country_code)}
              {data.partner && ` · ${data.partner}`}
            </p>
          </div>
        </div>
        <Button variant="secondary" onClick={() => setEditing(true)}>
          <Pencil className="size-4" aria-hidden />
          Editar
        </Button>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="min-w-0 space-y-4 lg:col-span-2">
          <Card title="Eventos" icon={<CalendarDays className="size-4" aria-hidden />}>
            <ErrorAlert error={upcoming.error} />
            {upcoming.data?.length ? (
              <ul className="-mx-4 divide-y divide-stone-100 sm:-mx-5">
                {upcoming.data.map((event) => (
                  <EventRow key={event.id} event={event} showCampus={false} />
                ))}
              </ul>
            ) : (
              !upcoming.isPending && <p className="text-sm text-stone-400">No hay eventos próximos.</p>
            )}
            {past.data && past.data.length > 0 && (
              <>
                <p className="mt-4 mb-1 text-xs font-semibold text-stone-500 uppercase">Anteriores</p>
                <ul className="-mx-4 divide-y divide-stone-100 sm:-mx-5">
                  {past.data.map((event) => (
                    <EventRow key={event.id} event={event} showCampus={false} />
                  ))}
                </ul>
              </>
            )}
          </Card>

          <Card title="Material enviado" icon={<Package className="size-4" aria-hidden />}>
            <SentMaterialTable campusId={campusId} />
          </Card>

          <Card title="Últimos envíos" icon={<Truck className="size-4" aria-hidden />}>
            {shipments.data?.length ? (
              <ul className="-mx-4 divide-y divide-stone-100 sm:-mx-5">
                {shipments.data.map((shipment) => (
                  <ShipmentRow key={shipment.id} shipment={shipment} showCampus={false} />
                ))}
              </ul>
            ) : (
              !shipments.isPending && <p className="text-sm text-stone-400">Sin envíos todavía.</p>
            )}
          </Card>
        </div>

        <div className="min-w-0 space-y-4">
          <Card title="Coordinador">
            {data.coordinator_name || data.coordinator_email || data.coordinator_phone ? (
              <div className="space-y-1.5 text-sm">
                {data.coordinator_name && <p className="font-semibold">{data.coordinator_name}</p>}
                {data.coordinator_email && (
                  <a href={`mailto:${data.coordinator_email}`} className="flex items-center gap-2 text-amber-700 hover:underline">
                    <Mail className="size-4" aria-hidden />
                    {data.coordinator_email}
                  </a>
                )}
                {data.coordinator_phone && (
                  <a href={`tel:${data.coordinator_phone}`} className="flex items-center gap-2 text-amber-700 hover:underline">
                    <Phone className="size-4" aria-hidden />
                    {data.coordinator_phone}
                  </a>
                )}
              </div>
            ) : (
              <p className="text-sm text-stone-400">Sin datos de contacto.</p>
            )}
          </Card>
          <Card title="Dirección de envío">
            <AddressBlock address={data.shipping_address} />
          </Card>
          {data.notes_md.trim() && (
            <Card title="Notas">
              <Markdown content={data.notes_md} className="prose-sm" />
            </Card>
          )}
        </div>
      </div>

      <CampusFormModal open={editing} campus={data} onClose={() => setEditing(false)} />
    </>
  );
}
