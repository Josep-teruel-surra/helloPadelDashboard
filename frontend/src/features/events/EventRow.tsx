import { CircleCheck, PackageOpen } from "lucide-react";
import { Link } from "react-router";

import type { AcademyEvent } from "@/api/types";
import { CountryFlag } from "@/components/ui/Country";
import { Badge } from "@/components/ui/Feedback";
import { cn } from "@/lib/cn";
import { formatDate, formatDateRange, parseLocalDate } from "@/lib/format";
import { EVENT_KIND_LABELS, EVENT_STATUS } from "@/lib/labels";

export function MaterialBadge({ event }: { event: AcademyEvent }) {
  const task = event.material_task;
  if (!task || event.status === "cancelled") return null;
  if (task.is_done) {
    return (
      <Badge tone="green">
        <CircleCheck className="size-3" aria-hidden />
        Material apartado
      </Badge>
    );
  }
  return (
    <Badge tone="amber">
      <PackageOpen className="size-3" aria-hidden />
      Material sin apartar{task.due_date && ` · antes del ${formatDate(task.due_date)}`}
    </Badge>
  );
}

function DateBlock({ date }: { date: string }) {
  const d = parseLocalDate(date);
  return (
    <div className="flex w-12 shrink-0 flex-col items-center rounded-lg bg-stone-100 py-1.5 leading-none">
      <span className="text-[11px] font-semibold text-stone-500 uppercase">
        {d.toLocaleDateString("es-ES", { month: "short" }).replace(".", "")}
      </span>
      <span className="text-lg font-extrabold">{d.getDate()}</span>
    </div>
  );
}

export function EventRow({ event, showCampus = true }: { event: AcademyEvent; showCampus?: boolean }) {
  const status = EVENT_STATUS[event.status];
  return (
    <li>
      <Link
        to={`/eventos/${event.id}`}
        className={cn(
          "flex gap-3 px-4 py-3 transition-colors hover:bg-stone-50",
          event.status === "cancelled" && "opacity-60",
        )}
      >
        <DateBlock date={event.start_date} />
        <div className="min-w-0 flex-1">
          <p className="font-semibold break-words">{event.title}</p>
          <p className="mt-0.5 flex flex-wrap items-center gap-x-2 text-sm text-stone-500">
            {showCampus && (
              <span>
                <CountryFlag code={event.campus.country_code} /> {event.campus.name}
              </span>
            )}
            <span>{formatDateRange(event.start_date, event.end_date)}</span>
            {event.responsible && <span>· {event.responsible.full_name}</span>}
          </p>
          <div className="mt-1.5 flex flex-wrap gap-1.5">
            <Badge>{EVENT_KIND_LABELS[event.kind]}</Badge>
            <Badge tone={status.tone}>{status.label}</Badge>
            <MaterialBadge event={event} />
          </div>
        </div>
      </Link>
    </li>
  );
}
