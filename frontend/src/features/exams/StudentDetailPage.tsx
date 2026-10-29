import { ArrowLeft, Mail, Pencil, Plus } from "lucide-react";
import { useState } from "react";
import { Link, useParams } from "react-router";

import { useExams, useStudent } from "@/api/queries";
import { Button } from "@/components/ui/Button";
import { CountryFlag } from "@/components/ui/Country";
import { ErrorAlert } from "@/components/ui/Feedback";
import { Card } from "@/components/ui/Layout";
import { Modal } from "@/components/ui/Modal";
import { Spinner } from "@/components/ui/Spinner";
import { countryName } from "@/lib/countries";
import { Markdown } from "@/features/notes/Markdown";
import { NewSubmissionForm, StudentForm } from "./ExamForms";
import { ExamRow } from "./ExamRow";

export function StudentDetailPage() {
  const { studentId = "" } = useParams();
  const student = useStudent(studentId);
  const exams = useExams({ student_id: studentId });
  const [dialog, setDialog] = useState<"edit" | "exam" | null>(null);

  const back = (
    <Link to="/correcciones" className="mb-4 inline-flex items-center gap-1.5 text-sm font-medium text-stone-500 hover:text-stone-900">
      <ArrowLeft className="size-4" aria-hidden />
      Correcciones
    </Link>
  );

  if (student.isPending) return <Spinner />;
  if (student.isError) {
    return (
      <>
        {back}
        <ErrorAlert error={student.error} />
      </>
    );
  }
  const data = student.data;

  return (
    <>
      {back}
      <div className="mb-6 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-extrabold tracking-tight">
            {data.country_code && <CountryFlag code={data.country_code} />} {data.full_name}
          </h1>
          <p className="mt-1 flex flex-wrap items-center gap-x-2 text-sm text-stone-500">
            <a href={`mailto:${data.email}`} className="inline-flex items-center gap-1 text-amber-700 hover:underline">
              <Mail className="size-4" aria-hidden />
              {data.email}
            </a>
            {data.country_code && <span>· {countryName(data.country_code)}</span>}
            {data.campus && (
              <span>
                · <Link to={`/campus/${data.campus.id}`} className="hover:underline">{data.campus.name}</Link>
              </span>
            )}
          </p>
        </div>
        <div className="flex gap-2">
          <Button onClick={() => setDialog("exam")}>
            <Plus className="size-4" aria-hidden />
            Nueva entrega
          </Button>
          <Button variant="secondary" onClick={() => setDialog("edit")}>
            <Pencil className="size-4" aria-hidden />
            Editar
          </Button>
        </div>
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card title="Entregas" className="lg:col-span-2">
          {exams.isPending ? (
            <Spinner />
          ) : exams.data?.length ? (
            <ul className="-mx-4 divide-y divide-stone-100 sm:-mx-5">
              {exams.data.map((exam) => (
                <ExamRow key={exam.id} exam={exam} showStudent={false} />
              ))}
            </ul>
          ) : (
            <p className="text-sm text-stone-400">Sin entregas.</p>
          )}
        </Card>
        <Card title="Notas">
          {data.notes_md.trim() ? <Markdown content={data.notes_md} className="prose-sm" /> : <p className="text-sm text-stone-400">Sin notas.</p>}
        </Card>
      </div>

      <Modal open={dialog !== null} onClose={() => setDialog(null)} title={dialog === "edit" ? "Editar alumno" : "Nueva entrega"}>
        {dialog === "edit" && <StudentForm student={data} onDone={() => setDialog(null)} />}
        {dialog === "exam" && <NewSubmissionForm studentId={data.id} onDone={() => setDialog(null)} />}
      </Modal>
    </>
  );
}
