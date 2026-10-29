import { CalendarDays, CircleCheck, Truck } from "lucide-react";
import type { ReactNode } from "react";
import { Link } from "react-router";

import type { AcademyEvent, HomeSummary, Shipment } from "@/api/types";
import { CountryFlag } from "@/components/ui/Country";
import { Card, SeeAll } from "@/components/ui/Layout";
import { Spinner } from "@/components/ui/Spinner";
import { cn } from "@/lib/cn";
import { daysUntil, formatDate } from "@/lib/format";
import { EventRow } from "@/features/events/EventRow";

export function UpcomingEventsCard({
  events,
  className,
}: {
  events: AcademyEvent[] | undefined;
  className?: string;
}) {
  return (
    <Card
      className={className}
      title="Próximos 30 días"
      icon={<CalendarDays className="size-4" aria-hidden />}
      actions={<SeeAll to="/eventos">Ver eventos</SeeAll>}
    >
      {!events ? (
        <Spinner />
      ) : events.length ? (
        <ul className="-mx-4 divide-y divide-stone-100 sm:-mx-5">
          {events.map((event) => (
            <EventRow key={event.id} event={event} />
          ))}
        </ul>
      ) : (
        <p className="py-6 text-center text-sm text-stone-400">No hay eventos en los próximos 30 días.</p>
      )}
    </Card>
  );
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div>
      <h3 className="mb-1 text-xs font-semibold text-stone-500">{title}</h3>
      <ul className="space-y-1">{children}</ul>
    </div>
  );
}

function ShipmentLine({ shipment, detail }: { shipment: Shipment; detail: string }) {
  return (
    <li>
      <Link
        to={`/envios/${shipment.id}`}
        className="-mx-2 flex items-baseline gap-2 rounded-lg px-2 py-1 text-sm hover:bg-stone-50"
      >
        <span className="font-semibold text-stone-400">#{shipment.number}</span>
        <span className="min-w-0 flex-1 truncate">
          <CountryFlag code={shipment.campus.country_code} /> {shipment.campus.name}
          <span className="text-stone-500"> · {shipment.total_units} uds</span>
        </span>
        <span className="shrink-0 text-xs text-stone-500">{detail}</span>
      </Link>
    </li>
  );
}

function daysAgo(iso: string): number {
  return Math.floor((Date.now() - new Date(iso).getTime()) / 86_400_000);
}

export function LogisticsCard({
  logistics,
  className,
}: {
  logistics: HomeSummary["logistics"] | undefined;
  className?: string;
}) {
  const allClear =
    logistics &&
    !logistics.to_prepare.length &&
    !logistics.awaiting_delivery.length &&
    !logistics.low_stock.length;

  return (
    <Card
      className={className}
      title="Envíos y material"
      icon={<Truck className="size-4" aria-hidden />}
      actions={<SeeAll to="/envios">Ver envíos</SeeAll>}
    >
      {!logistics ? (
        <Spinner />
      ) : allClear ? (
        <p className="flex items-center justify-center gap-2 py-6 text-sm text-stone-400">
          <CircleCheck className="size-4" aria-hidden />
          Nada pendiente.
        </p>
      ) : (
        <div className="space-y-4">
          {logistics.to_prepare.length > 0 && (
            <Section title="Te toca preparar">
              {logistics.to_prepare.map((s) => {
                const days = s.needed_by ? daysUntil(s.needed_by) : null;
                return (
                  <ShipmentLine
                    key={s.id}
                    shipment={s}
                    detail={
                      s.needed_by
                        ? days !== null && days < 0
                          ? `vencido el ${formatDate(s.needed_by)}`
                          : `para el ${formatDate(s.needed_by)}`
                        : "sin fecha"
                    }
                  />
                );
              })}
            </Section>
          )}

          {logistics.awaiting_delivery.length > 0 && (
            <Section title="¿Ha llegado? Enviados hace tiempo">
              {logistics.awaiting_delivery.map((s) => (
                <ShipmentLine
                  key={s.id}
                  shipment={s}
                  detail={`enviado hace ${daysAgo(s.shipped_at!)} días`}
                />
              ))}
            </Section>
          )}

          {logistics.low_stock.length > 0 && (
            <Section title="Stock bajo">
              {logistics.low_stock.map((item) => (
                <li key={item.variant_id}>
                  <Link
                    to="/material"
                    className="-mx-2 flex items-baseline gap-2 rounded-lg px-2 py-1 text-sm hover:bg-stone-50"
                  >
                    <span className="min-w-0 flex-1 truncate">
                      {item.product_name} <span className="text-stone-500">· {item.label}</span>
                    </span>
                    <span
                      className={cn(
                        "shrink-0 font-semibold tabular-nums",
                        item.available < 0 ? "text-red-700" : "text-amber-700",
                      )}
                    >
                      {item.available < 0 ? `faltan ${-item.available}` : `${item.available} disp.`}
                    </span>
                  </Link>
                </li>
              ))}
            </Section>
          )}
        </div>
      )}
    </Card>
  );
}
