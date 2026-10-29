import { CircleCheck, ClipboardCheck } from "lucide-react";
import type { ReactNode } from "react";
import { Link } from "react-router";

import type { ExamSubmission, HomeSummary } from "@/api/types";
import { Badge } from "@/components/ui/Feedback";
import { Card, SeeAll } from "@/components/ui/Layout";
import { Spinner } from "@/components/ui/Spinner";
import { DeadlineBadge, LinkBadge, examTitle } from "@/features/exams/ExamRow";

function ExamLine({ exam, badge }: { exam: ExamSubmission; badge: ReactNode }) {
  return (
    <li>
      <Link
        to={`/correcciones/${exam.id}`}
        className="-mx-2 flex flex-wrap items-center gap-x-2 gap-y-1 rounded-lg px-2 py-1.5 text-sm hover:bg-stone-50"
      >
        <span className="min-w-0 flex-1 truncate">
          <span className="font-medium">{exam.student.full_name}</span>
          <span className="text-stone-500"> · {examTitle(exam)}</span>
        </span>
        {badge}
      </Link>
    </li>
  );
}

export function ExamsCard({
  exams,
  className,
}: {
  exams: HomeSummary["exams"] | undefined;
  className?: string;
}) {
  return (
    <Card
      className={className}
      title="Correcciones"
      icon={<ClipboardCheck className="size-4" aria-hidden />}
      actions={<SeeAll to="/correcciones">{exams ? `Mías (${exams.mine_count})` : "Ver"}</SeeAll>}
    >
      {!exams ? (
        <Spinner />
      ) : (
        <div className="space-y-4">
          {(exams.unassigned_count > 0 || exams.to_notify_count > 0) && (
            <p className="flex flex-wrap gap-1.5">
              {exams.unassigned_count > 0 && (
                <Badge tone="amber">{exams.unassigned_count} sin asignar</Badge>
              )}
              {exams.to_notify_count > 0 && (
                <Badge tone="blue">{exams.to_notify_count} por comunicar al alumno</Badge>
              )}
            </p>
          )}

          {exams.links_at_risk.length > 0 && (
            <div>
              <h3 className="mb-1 text-xs font-semibold text-red-700">Enlaces a punto de perderse</h3>
              <ul>
                {exams.links_at_risk.map((exam) => (
                  <ExamLine key={exam.id} exam={exam} badge={<LinkBadge exam={exam} />} />
                ))}
              </ul>
            </div>
          )}

          <div>
            <h3 className="mb-1 text-xs font-semibold text-stone-500">Te toca corregir</h3>
            {exams.mine.length ? (
              <ul>
                {exams.mine.map((exam) => (
                  <ExamLine key={exam.id} exam={exam} badge={<DeadlineBadge exam={exam} />} />
                ))}
              </ul>
            ) : (
              <p className="flex items-center gap-2 py-2 text-sm text-stone-400">
                <CircleCheck className="size-4" aria-hidden />
                Nada pendiente.
              </p>
            )}
          </div>
        </div>
      )}
    </Card>
  );
}
