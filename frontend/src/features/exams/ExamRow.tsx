import { CircleCheck, Link2Off, TriangleAlert } from "lucide-react";
import { Link } from "react-router";

import type { ExamSubmission } from "@/api/types";
import { CountryFlag } from "@/components/ui/Country";
import { Badge } from "@/components/ui/Feedback";
import { formatDate } from "@/lib/format";
import { EXAM_KIND_LABELS, EXAM_OUTCOME, EXAM_STATUS } from "@/lib/labels";

export function ExamStatusBadge({ exam }: { exam: ExamSubmission }) {
  const status = EXAM_STATUS[exam.status];
  return <Badge tone={status.tone}>{status.label}</Badge>;
}

export function OutcomeBadge({ exam }: { exam: ExamSubmission }) {
  if (!exam.outcome) return null;
  const outcome = EXAM_OUTCOME[exam.outcome];
  return (
    <Badge tone={outcome.tone}>
      {outcome.label}
      {exam.score && ` · ${Number(exam.score)}`}
    </Badge>
  );
}

/** Plazo de corrección: rojo si se ha pasado, ámbar si vence hoy o mañana. */
export function DeadlineBadge({ exam }: { exam: ExamSubmission }) {
  const days = exam.days_left;
  if (days === null) return null;
  if (days < 0) return <Badge tone="red">Plazo vencido · {formatDate(exam.due_on)}</Badge>;
  if (days === 0) return <Badge tone="amber">Vence hoy</Badge>;
  if (days === 1) return <Badge tone="amber">Vence mañana</Badge>;
  return <Badge>Quedan {days} días</Badge>;
}

/** Riesgo del enlace (sobre todo WeTransfer, que caduca). */
export function LinkBadge({ exam }: { exam: ExamSubmission }) {
  switch (exam.link_status) {
    case "expired":
      return (
        <Badge tone="red">
          <Link2Off className="size-3" aria-hidden />
          Enlace caducado
        </Badge>
      );
    case "expiring":
      return (
        <Badge tone="red">
          <TriangleAlert className="size-3" aria-hidden />
          Descargar antes del {formatDate(exam.link_expires_on!)}
        </Badge>
      );
    case "saved":
      return (
        <Badge tone="green">
          <CircleCheck className="size-3" aria-hidden />
          Guardado
        </Badge>
      );
    default:
      return null;
  }
}

export function examTitle(exam: ExamSubmission): string {
  const attempt = exam.attempt > 1 ? ` · ${exam.attempt}.º intento` : "";
  return `${exam.certification.name} · ${EXAM_KIND_LABELS[exam.kind]}${attempt}`;
}

export function ExamRow({ exam, showStudent = true }: { exam: ExamSubmission; showStudent?: boolean }) {
  return (
    <li>
      <Link to={`/correcciones/${exam.id}`} className="flex gap-3 px-4 py-3 transition-colors hover:bg-stone-50">
        <div className="min-w-0 flex-1">
          <p className="flex flex-wrap items-center gap-x-2 font-semibold">
            {showStudent && (
              <span>
                {exam.student.country_code && <CountryFlag code={exam.student.country_code} />}{" "}
                {exam.student.full_name}
              </span>
            )}
            <span className={showStudent ? "font-normal text-stone-500" : undefined}>{examTitle(exam)}</span>
          </p>
          <div className="mt-1.5 flex flex-wrap items-center gap-1.5 text-xs text-stone-500">
            <ExamStatusBadge exam={exam} />
            <OutcomeBadge exam={exam} />
            <DeadlineBadge exam={exam} />
            <LinkBadge exam={exam} />
            <span>
              Recibido {formatDate(exam.received_on)}
              {exam.assignee ? ` · ${exam.assignee.full_name}` : " · sin asignar"}
            </span>
          </div>
        </div>
      </Link>
    </li>
  );
}
