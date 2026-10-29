import { useMutation } from "@tanstack/react-query";
import { ArrowLeft, ExternalLink, FilePen, HardDriveDownload, Pencil, Trash2 } from "lucide-react";
import { useState } from "react";
import type { ReactNode } from "react";
import { Link, useNavigate, useParams } from "react-router";

import { examsApi } from "@/api/endpoints";
import { useExam, useExams } from "@/api/queries";
import type { ExamStatus, ExamSubmission } from "@/api/types";
import { Button } from "@/components/ui/Button";
import { CountryFlag } from "@/components/ui/Country";
import { ErrorAlert } from "@/components/ui/Feedback";
import { inputClass } from "@/components/ui/Field";
import { Card } from "@/components/ui/Layout";
import { Modal } from "@/components/ui/Modal";
import { Spinner } from "@/components/ui/Spinner";
import { formatDate, formatDateTime } from "@/lib/format";
import { EXAM_SOURCE_LABELS } from "@/lib/labels";
import { useInvalidate } from "@/lib/useInvalidate";
import { Markdown } from "@/features/notes/Markdown";
import { CorrectionForm, SubmissionDetailsForm } from "./ExamForms";
import { DeadlineBadge, ExamRow, ExamStatusBadge, LinkBadge, OutcomeBadge, examTitle } from "./ExamRow";

type Action = { to: Exclude<ExamStatus, "corrected">; label: string } | { to: "correct"; label: string };

// Acciones según el estado (el backend valida las mismas transiciones).
const ACTIONS: Record<ExamStatus, Action[]> = {
  received: [
    { to: "in_review", label: "Empezar a corregir" },
    { to: "correct", label: "Corregir" },
    { to: "on_hold", label: "En espera" },
    { to: "cancelled", label: "Cancelar" },
  ],
  in_review: [
    { to: "correct", label: "Corregir" },
    { to: "on_hold", label: "En espera" },
    { to: "received", label: "Devolver a pendiente" },
    { to: "cancelled", label: "Cancelar" },
  ],
  on_hold: [
    { to: "in_review", label: "Retomar" },
    { to: "correct", label: "Corregir" },
    { to: "cancelled", label: "Cancelar" },
  ],
  corrected: [
    { to: "notified", label: "Marcar como comunicada" },
    { to: "correct", label: "Editar corrección" },
    { to: "in_review", label: "Reabrir" },
  ],
  notified: [{ to: "in_review", label: "Reabrir" }],
  cancelled: [{ to: "received", label: "Reactivar" }],
};

function Detail({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <dt className="text-xs text-stone-500">{label}</dt>
      <dd className="text-sm font-medium">{children}</dd>
    </div>
  );
}

function SavedLinkForm({ exam, onDone }: { exam: ExamSubmission; onDone: () => void }) {
  const invalidate = useInvalidate();
  const [url, setUrl] = useState(exam.saved_url ?? "");
  const save = useMutation({
    mutationFn: (savedUrl: string | null) => examsApi.update(exam.id, { saved_url: savedUrl }),
    onSuccess: async () => {
      await invalidate(["exams"], ["home"]);
      onDone();
    },
  });
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        save.mutate(url.trim() || null);
      }}
      className="mt-3 flex flex-wrap gap-2"
    >
      <ErrorAlert error={save.error} className="w-full" />
      <input
        type="url"
        required
        aria-label="Dónde lo has guardado"
        placeholder="https://drive.google.com/…"
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        className={inputClass + " min-w-0 flex-1"}
      />
      <Button type="submit" size="sm" loading={save.isPending} className="h-10">
        Guardar
      </Button>
      {exam.saved_url && (
        <Button size="sm" variant="ghost" className="h-10" onClick={() => save.mutate(null)}>
          Quitar
        </Button>
      )}
    </form>
  );
}

export function ExamDetailPage() {
  const { examId = "" } = useParams();
  const navigate = useNavigate();
  const invalidate = useInvalidate();
  const exam = useExam(examId);
  const history = useExams({ student_id: exam.data?.student.id }, !!exam.data);
  const [dialog, setDialog] = useState<"correct" | "details" | null>(null);
  const [editingSaved, setEditingSaved] = useState(false);

  const status = useMutation({
    mutationFn: (to: Exclude<ExamStatus, "corrected">) => examsApi.changeStatus(examId, to),
    onSuccess: () => invalidate(["exams"], ["home"]),
  });
  const remove = useMutation({
    mutationFn: () => examsApi.remove(examId),
    onSuccess: async () => {
      await invalidate(["exams"], ["home"]);
      navigate("/correcciones", { replace: true });
    },
  });

  const back = (
    <Link to="/correcciones" className="mb-4 inline-flex items-center gap-1.5 text-sm font-medium text-stone-500 hover:text-stone-900">
      <ArrowLeft className="size-4" aria-hidden />
      Correcciones
    </Link>
  );

  if (exam.isPending) return <Spinner />;
  if (exam.isError) {
    return (
      <>
        {back}
        <ErrorAlert error={exam.error} />
      </>
    );
  }
  const data = exam.data;
  const others = history.data?.filter((e) => e.id !== data.id) ?? [];

  return (
    <>
      {back}
      <div className="mb-6 flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <h1 className="text-2xl font-extrabold tracking-tight">
            <Link to={`/alumnos/${data.student.id}`} className="hover:underline">
              {data.student.country_code && <CountryFlag code={data.student.country_code} />} {data.student.full_name}
            </Link>
          </h1>
          <p className="mt-1 text-sm text-stone-500">{examTitle(data)}</p>
          <div className="mt-2 flex flex-wrap gap-1.5">
            <ExamStatusBadge exam={data} />
            <OutcomeBadge exam={data} />
            <DeadlineBadge exam={data} />
            <LinkBadge exam={data} />
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          {ACTIONS[data.status].map((action, index) => (
            <Button
              key={action.to}
              variant={index === 0 ? "primary" : "secondary"}
              loading={status.isPending && status.variables === action.to}
              onClick={() => (action.to === "correct" ? setDialog("correct") : status.mutate(action.to))}
            >
              {action.to === "correct" && <FilePen className="size-4" aria-hidden />}
              {action.label}
            </Button>
          ))}
          {data.can_delete && (
            <Button
              variant="ghost"
              loading={remove.isPending}
              onClick={() => window.confirm("¿Borrar esta entrega?") && remove.mutate()}
              className="hover:bg-red-50 hover:text-red-700"
            >
              <Trash2 className="size-4" aria-hidden />
            </Button>
          )}
        </div>
      </div>

      <ErrorAlert error={status.error ?? remove.error} className="mb-4" />

      <div className="grid gap-4 lg:grid-cols-3">
        <div className="min-w-0 space-y-4 lg:col-span-2">
          <Card title="Material del examen" icon={<HardDriveDownload className="size-4" aria-hidden />}>
            <dl className="grid gap-3 sm:grid-cols-2">
              <Detail label="Origen">{EXAM_SOURCE_LABELS[data.source]}</Detail>
              <Detail label="El enlace caduca">
                {data.link_expires_on ? formatDate(data.link_expires_on) : "No caduca"}
              </Detail>
            </dl>
            {data.link_url && (
              <a href={data.link_url} target="_blank" rel="noopener noreferrer" className="mt-3 inline-flex max-w-full items-center gap-1.5 text-sm font-medium text-amber-700 hover:underline">
                <ExternalLink className="size-4 shrink-0" aria-hidden />
                <span className="truncate">{data.link_url}</span>
              </a>
            )}
            <div className="mt-4 border-t border-stone-100 pt-3">
              {data.saved_url && !editingSaved ? (
                <p className="flex flex-wrap items-center gap-2 text-sm">
                  <span className="text-stone-500">Guardado {data.saved_at && formatDateTime(data.saved_at)}:</span>
                  <a href={data.saved_url} target="_blank" rel="noopener noreferrer" className="font-medium text-amber-700 hover:underline">
                    abrir copia guardada
                  </a>
                  <Button size="sm" variant="ghost" onClick={() => setEditingSaved(true)}>
                    Cambiar
                  </Button>
                </p>
              ) : (
                <>
                  <p className="text-sm text-stone-600">
                    {data.source === "wetransfer"
                      ? "Descarga el vídeo y guárdalo (p. ej. en Drive) antes de que caduque el enlace."
                      : "¿Lo has guardado en otro sitio? Indica dónde."}
                  </p>
                  <SavedLinkForm exam={data} onDone={() => setEditingSaved(false)} />
                </>
              )}
            </div>
          </Card>

          <Card
            title="Corrección"
            icon={<FilePen className="size-4" aria-hidden />}
            actions={
              ["received", "in_review", "on_hold", "corrected"].includes(data.status) && (
                <Button size="sm" variant="secondary" onClick={() => setDialog("correct")}>
                  {data.outcome ? "Editar" : "Corregir"}
                </Button>
              )
            }
          >
            {data.outcome ? (
              <>
                <p className="flex flex-wrap items-center gap-2 text-sm">
                  <OutcomeBadge exam={data} />
                  {data.corrected_by && (
                    <span className="text-stone-500">
                      {data.corrected_by.full_name} · {data.corrected_at && formatDateTime(data.corrected_at)}
                    </span>
                  )}
                </p>
                {data.feedback_md.trim() ? (
                  <Markdown content={data.feedback_md} className="prose-sm mt-3" />
                ) : (
                  <p className="mt-3 text-sm text-stone-400">Sin comentarios.</p>
                )}
                {data.notified_at && (
                  <p className="mt-3 text-xs text-stone-500">Comunicado al alumno el {formatDateTime(data.notified_at)}.</p>
                )}
              </>
            ) : (
              <p className="text-sm text-stone-400">Todavía no se ha corregido.</p>
            )}
          </Card>

          {others.length > 0 && (
            <Card title="Otras entregas del alumno">
              <ul className="-mx-4 divide-y divide-stone-100 sm:-mx-5">
                {others.map((e) => (
                  <ExamRow key={e.id} exam={e} showStudent={false} />
                ))}
              </ul>
            </Card>
          )}
        </div>

        <Card
          title="Datos"
          actions={
            <Button size="sm" variant="secondary" onClick={() => setDialog("details")}>
              <Pencil className="size-4" aria-hidden />
              Editar
            </Button>
          }
        >
          <dl className="space-y-3">
            <Detail label="Lo corrige">{data.assignee?.full_name ?? "Sin asignar"}</Detail>
            <Detail label="Recibido">{formatDate(data.received_on)}</Detail>
            <Detail label="Corregir antes del">{formatDate(data.due_on)}</Detail>
            <Detail label="Alumno">
              <Link to={`/alumnos/${data.student.id}`} className="text-amber-700 hover:underline">
                {data.student.email}
              </Link>
            </Detail>
            <Detail label="Registrado por">{data.created_by.full_name}</Detail>
          </dl>
        </Card>
      </div>

      <Modal open={dialog !== null} onClose={() => setDialog(null)} title={dialog === "correct" ? "Corrección" : "Datos de la entrega"}>
        {dialog === "correct" && <CorrectionForm exam={data} onDone={() => setDialog(null)} />}
        {dialog === "details" && <SubmissionDetailsForm exam={data} onDone={() => setDialog(null)} />}
      </Modal>
    </>
  );
}
