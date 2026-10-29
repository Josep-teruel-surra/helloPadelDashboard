import { TriangleAlert } from "lucide-react";
import { Link } from "react-router";

import type { Shipment } from "@/api/types";
import { CountryFlag } from "@/components/ui/Country";
import { Badge } from "@/components/ui/Feedback";
import { formatDate, formatDateTime } from "@/lib/format";
import { SHIPMENT_STATUS } from "@/lib/labels";

export function ShipmentStatusBadge({ shipment }: { shipment: Shipment }) {
  const status = SHIPMENT_STATUS[shipment.status];
  return <Badge tone={status.tone}>{status.label}</Badge>;
}

function dateLine(shipment: Shipment): string | null {
  if (shipment.delivered_at) return `Entregado ${formatDateTime(shipment.delivered_at)}`;
  if (shipment.shipped_at) return `Enviado ${formatDateTime(shipment.shipped_at)}`;
  if (shipment.needed_by) return `Para el ${formatDate(shipment.needed_by)}`;
  return null;
}

export function itemsSummary(shipment: Shipment, max = 3): string {
  const parts = shipment.items.map((i) => `${i.product_name} ${i.label} ×${i.quantity}`);
  return parts.length > max ? `${parts.slice(0, max).join(", ")} y ${parts.length - max} más` : parts.join(", ");
}

export function ShipmentRow({
  shipment,
  showCampus = true,
  showEvent = true,
}: {
  shipment: Shipment;
  showCampus?: boolean;
  showEvent?: boolean;
}) {
  const when = dateLine(shipment);
  return (
    <li>
      <Link to={`/envios/${shipment.id}`} className="flex gap-3 px-4 py-3 transition-colors hover:bg-stone-50">
        <span className="w-12 shrink-0 pt-0.5 text-sm font-bold text-stone-400">#{shipment.number}</span>
        <div className="min-w-0 flex-1">
          {(showCampus || (showEvent && shipment.event)) && (
          <p className="flex flex-wrap items-center gap-x-2 font-semibold">
            {showCampus && (
              <span>
                <CountryFlag code={shipment.campus.country_code} /> {shipment.campus.name}
              </span>
            )}
            {showEvent && shipment.event && (
              <span className="font-normal text-stone-500">· {shipment.event.title}</span>
            )}
          </p>
          )}
          <p className="mt-0.5 truncate text-sm text-stone-500">
            {shipment.total_units} uds · {itemsSummary(shipment)}
          </p>
          <div className="mt-1.5 flex flex-wrap items-center gap-1.5 text-xs text-stone-500">
            <ShipmentStatusBadge shipment={shipment} />
            {shipment.stock_warnings.length > 0 && (
              <Badge tone="red">
                <TriangleAlert className="size-3" aria-hidden />
                Falta stock
              </Badge>
            )}
            {when && <span>{when}</span>}
            {shipment.assignee && <span>· {shipment.assignee.full_name}</span>}
          </div>
        </div>
      </Link>
    </li>
  );
}
