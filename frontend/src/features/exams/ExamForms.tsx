import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import type { FormEvent } from "react";
import { useNavigate } from "react-router";

import { examsApi, studentsApi } from "@/api/endpoints";
import type { StudentInput } from "@/api/endpoints";
import { useCampuses, useCertifications, useStudents, useUsers } from "@/api/queries";
import type { ExamKind, ExamOutcome, ExamSource, ExamSubmission, Student } from "@/api/types";
import { Button } from "@/components/ui/Button";
import { CountrySelect } from "@/components/ui/Country";
import { ErrorAlert } from "@/components/ui/Feedback";
import { Field, inputClass } from "@/components/ui/Field";
import { Segmented } from "@/components/ui/Layout";
import { todayISO } from "@/lib/format";
import { EXAM_KIND_LABELS, EXAM_OUTCOME, EXAM_SOURCE_LABELS, options } from "@/lib/labels";
import { useInvalidate } from "@/lib/useInvalidate";

const EXAM_KEYS = [["exams"], ["students"], ["home"]] as const;

function Actions({ saving, label, onCancel }: { saving: boolean; label: string; onCancel: () => void }) {
  return (
    <div className="flex justify-end gap-2 pt-2">
      <Button variant="secondary" onClick={onCancel}>
        Cancelar
      </Button>
      <Button type="submit" loading={saving}>
        {label}
      </Button>
    </div>
  );
}

export function UserSelect({ id, value, onChange }: { id: string; value: string; onChange: (v: string) => void }) {
  const users = useUsers();
  return (
    <select id={id} value={value} onChange={(e) => onChange(e.target.value)} className={inputClass}>
      <option value="">Sin asignar</option>
      {users.data?.map((u) => (
        <option key={u.id} value={u.id}>
          {u.full_name}
        </option>
      ))}
    </select>
  );
}

const isWeTransfer = (url: string) => /^https?:\/\/([^/]+\.)?(we\.tl|wetransfer\.com)(\/|$)/i.test(url.trim());

// --- Datos de un alumno (alta y edición) ---

export function StudentFields({
  value,
  onChange,
  idPrefix,
}: {
  value: StudentInput;
  onChange: (value: StudentInput) => void;
  idPrefix: string;
}) {
  const campuses = useCampuses();
  const set = (patch: Partial<StudentInput>) => onChange({ ...value, ...patch });
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      <Field label="Nombre completo" htmlFor={`${idPrefix}-name`}>
        <input id={`${idPrefix}-name`} required maxLength={160} value={value.full_name} onChange={(e) => set({ full_name: e.target.value })} className={inputClass} />
      </Field>
      <Field label="Email" htmlFor={`${idPrefix}-email`}>
        <input id={`${idPrefix}-email`} type="email" required value={value.email} onChange={(e) => set({ email: e.target.value })} className={inputClass} />
      </Field>
      <Field label="País" htmlFor={`${idPrefix}-country`}>
        <CountrySelect id={`${idPrefix}-country`} value={value.country_code ?? ""} onChange={(code) => set({ country_code: code || null })} emptyLabel="Sin indicar" />
      </Field>
      <Field label="Sede" htmlFor={`${idPrefix}-campus`} hint="Opcional">
        <select id={`${idPrefix}-campus`} value={value.campus_id ?? ""} onChange={(e) => set({ campus_id: e.target.value || null })} className={inputClass}>
          <option value="">Ninguna</option>
          {campuses.data?.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
      </Field>
    </div>
  );
}

export function StudentForm({ student, onDone }: { student: Student; onDone: () => void }) {
  const invalidate = useInvalidate();
  const [value, setValue] = useState<StudentInput>({
    full_name: student.full_name,
    email: student.email,
    country_code: student.country_code,
    campus_id: student.campus?.id ?? null,
  });
  const [notes, setNotes] = useState(student.notes_md);
  const save = useMutation({
    mutationFn: () => studentsApi.update(student.id, { ...value, notes_md: notes }),
    onSuccess: async () => {
      await invalidate(...EXAM_KEYS);
      onDone();
    },
  });
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        save.mutate();
      }}
      className="space-y-4"
    >
      <ErrorAlert error={save.error} />
      <StudentFields value={value} onChange={setValue} idPrefix="edit-student" />
      <Field label="Notas" htmlFor="student-notes">
        <textarea id="student-notes" rows={3} value={notes} onChange={(e) => setNotes(e.target.value)} className={inputClass} />
      </Field>
      <Actions saving={save.isPending} label="Guardar" onCancel={onDone} />
    </form>
  );
}

// --- Nueva entrega ---

const NEW_STUDENT = "__new__";
const EMPTY_STUDENT: StudentInput = { full_name: "", email: "", country_code: null, campus_id: null };

export function NewSubmissionForm({ studentId, onDone }: { studentId?: string; onDone: () => void }) {
  const invalidate = useInvalidate();
  const navigate = useNavigate();
  const students = useStudents({ limit: 500 });
  const certifications = useCertifications();

  const [selectedStudent, setSelectedStudent] = useState(studentId ?? "");
  const [newStudent, setNewStudent] = useState<StudentInput>(EMPTY_STUDENT);
  const [certificationId, setCertificationId] = useState("");
  const [kind, setKind] = useState<ExamKind>("video");
  const [linkUrl, setLinkUrl] = useState("");
  const [source, setSource] = useState<ExamSource | "">("");
  const [receivedOn, setReceivedOn] = useState(todayISO());
  const [dueOn, setDueOn] = useState("");
  const [linkExpiresOn, setLinkExpiresOn] = useState("");
  const [assigneeId, setAssigneeId] = useState("");

  const certification = certifications.data?.find((c) => c.id === certificationId);
  const kinds = options(EXAM_KIND_LABELS).filter(
    (o) => !certification || (o.value === "test" ? certification.has_test : certification.has_video),
  );
  const detectedSource: ExamSource = linkUrl && isWeTransfer(linkUrl) ? "wetransfer" : "examportal";
  const effectiveSource = source || detectedSource;

  const save = useMutation({
    mutationFn: async () => {
      let student = selectedStudent;
      if (student === NEW_STUDENT) {
        student = (await studentsApi.create(newStudent)).id;
        // Si la entrega falla después, al reintentar no se vuelve a crear el alumno.
        setSelectedStudent(student);
        await invalidate(["students"]);
      }
      return examsApi.create({
        student_id: student,
        certification_id: certificationId,
        kind: kinds.some((k) => k.value === kind) ? kind : kinds[0]!.value,
        source: source || null,
        link_url: linkUrl.trim() || null,
        link_expires_on: linkExpiresOn || null,
        received_on: receivedOn || null,
        due_on: dueOn || null,
        assignee_id: assigneeId || null,
      });
    },
    onSuccess: async (exam) => {
      await invalidate(...EXAM_KEYS);
      onDone();
      navigate(`/correcciones/${exam.id}`);
    },
  });

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    save.mutate();
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <ErrorAlert error={save.error} />

      <Field label="Alumno" htmlFor="exam-student">
        <select id="exam-student" required value={selectedStudent} onChange={(e) => setSelectedStudent(e.target.value)} className={inputClass} disabled={!!studentId}>
          <option value="">Elige alumno…</option>
          <option value={NEW_STUDENT}>+ Alumno nuevo</option>
          {students.data?.map((s) => (
            <option key={s.id} value={s.id}>
              {s.full_name} · {s.email}
            </option>
          ))}
        </select>
      </Field>
      {selectedStudent === NEW_STUDENT && (
        <div className="rounded-xl border border-stone-200 p-3">
          <StudentFields value={newStudent} onChange={setNewStudent} idPrefix="new-student" />
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Certificación" htmlFor="exam-cert">
          <select id="exam-cert" required value={certificationId} onChange={(e) => setCertificationId(e.target.value)} className={inputClass}>
            <option value="">Elige…</option>
            {certifications.data?.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </Field>
        <div className="space-y-1.5">
          <span className="block text-sm font-medium text-stone-700">Tipo</span>
          <Segmented label="Tipo de examen" options={kinds} value={kinds.some((k) => k.value === kind) ? kind : (kinds[0]?.value ?? kind)} onChange={setKind} />
        </div>
      </div>

      <Field
        label="Enlace"
        htmlFor="exam-link"
        hint={
          effectiveSource === "wetransfer"
            ? "WeTransfer: se avisará antes de que caduque el enlace."
            : "Del examportal, WeTransfer u otro sitio. Opcional."
        }
      >
        <input id="exam-link" type="url" maxLength={1000} placeholder="https://…" value={linkUrl} onChange={(e) => setLinkUrl(e.target.value)} className={inputClass} />
      </Field>

      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Origen" htmlFor="exam-source">
          <select id="exam-source" value={source} onChange={(e) => setSource(e.target.value as ExamSource | "")} className={inputClass}>
            <option value="">Automático ({EXAM_SOURCE_LABELS[detectedSource]})</option>
            {options(EXAM_SOURCE_LABELS).map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Lo corrige" htmlFor="exam-assignee">
          <UserSelect id="exam-assignee" value={assigneeId} onChange={setAssigneeId} />
        </Field>
        <Field label="Recibido el" htmlFor="exam-received">
          <input id="exam-received" type="date" required value={receivedOn} onChange={(e) => setReceivedOn(e.target.value)} className={inputClass} />
        </Field>
        <Field label="Corregir antes del" htmlFor="exam-due" hint="Vacío: 7 días después de recibirlo">
          <input id="exam-due" type="date" min={receivedOn} value={dueOn} onChange={(e) => setDueOn(e.target.value)} className={inputClass} />
        </Field>
        {effectiveSource === "wetransfer" && (
          <Field label="El enlace caduca el" htmlFor="exam-expires" hint="Vacío: 7 días después de recibirlo">
            <input id="exam-expires" type="date" value={linkExpiresOn} onChange={(e) => setLinkExpiresOn(e.target.value)} className={inputClass} />
          </Field>
        )}
      </div>

      <Actions saving={save.isPending} label="Registrar entrega" onCancel={onDone} />
    </form>
  );
}

// --- Corregir ---

export function CorrectionForm({ exam, onDone }: { exam: ExamSubmission; onDone: () => void }) {
  const invalidate = useInvalidate();
  const [outcome, setOutcome] = useState<ExamOutcome>(exam.outcome ?? "passed");
  const [score, setScore] = useState(exam.score ? String(Number(exam.score)) : "");
  const [feedback, setFeedback] = useState(exam.feedback_md);

  const save = useMutation({
    mutationFn: () => examsApi.correct(exam.id, { outcome, score: score || null, feedback_md: feedback }),
    onSuccess: async () => {
      await invalidate(...EXAM_KEYS);
      onDone();
    },
  });

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        save.mutate();
      }}
      className="space-y-4"
    >
      <ErrorAlert error={save.error} />
      <div className="grid gap-4 sm:grid-cols-[1fr_8rem]">
        <div className="space-y-1.5">
          <span className="block text-sm font-medium text-stone-700">Resultado</span>
          <Segmented label="Resultado" options={options(EXAM_OUTCOME)} value={outcome} onChange={setOutcome} />
        </div>
        <Field label="Nota" htmlFor="exam-score" hint="0 a 10, opcional">
          <input id="exam-score" type="number" min={0} max={10} step="0.25" value={score} onChange={(e) => setScore(e.target.value)} className={inputClass} />
        </Field>
      </div>
      <Field label="Comentarios para el alumno" htmlFor="exam-feedback" hint="Admite markdown.">
        <textarea id="exam-feedback" rows={6} value={feedback} onChange={(e) => setFeedback(e.target.value)} className={inputClass} />
      </Field>
      <Actions saving={save.isPending} label="Guardar corrección" onCancel={onDone} />
    </form>
  );
}

// --- Datos de la entrega ---

export function SubmissionDetailsForm({ exam, onDone }: { exam: ExamSubmission; onDone: () => void }) {
  const invalidate = useInvalidate();
  const [form, setForm] = useState({
    assignee_id: exam.assignee?.id ?? "",
    received_on: exam.received_on,
    due_on: exam.due_on,
    source: exam.source,
    link_url: exam.link_url ?? "",
    link_expires_on: exam.link_expires_on ?? "",
  });
  const set = (field: keyof typeof form) => (value: string) => setForm((f) => ({ ...f, [field]: value }));

  const save = useMutation({
    mutationFn: () =>
      examsApi.update(exam.id, {
        ...form,
        assignee_id: form.assignee_id || null,
        link_url: form.link_url.trim() || null,
        link_expires_on: form.link_expires_on || null,
      }),
    onSuccess: async () => {
      await invalidate(...EXAM_KEYS);
      onDone();
    },
  });

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        save.mutate();
      }}
      className="space-y-4"
    >
      <ErrorAlert error={save.error} />
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Lo corrige" htmlFor="ed-assignee">
          <UserSelect id="ed-assignee" value={form.assignee_id} onChange={set("assignee_id")} />
        </Field>
        <Field label="Origen" htmlFor="ed-source">
          <select id="ed-source" value={form.source} onChange={(e) => set("source")(e.target.value)} className={inputClass}>
            {options(EXAM_SOURCE_LABELS).map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Recibido el" htmlFor="ed-received">
          <input id="ed-received" type="date" required value={form.received_on} onChange={(e) => set("received_on")(e.target.value)} className={inputClass} />
        </Field>
        <Field label="Corregir antes del" htmlFor="ed-due">
          <input id="ed-due" type="date" required min={form.received_on} value={form.due_on} onChange={(e) => set("due_on")(e.target.value)} className={inputClass} />
        </Field>
      </div>
      <Field label="Enlace" htmlFor="ed-link">
        <input id="ed-link" type="url" maxLength={1000} value={form.link_url} onChange={(e) => set("link_url")(e.target.value)} className={inputClass} />
      </Field>
      <Field label="El enlace caduca el" htmlFor="ed-expires" hint="Vacío si no caduca">
        <input id="ed-expires" type="date" value={form.link_expires_on} onChange={(e) => set("link_expires_on")(e.target.value)} className={inputClass} />
      </Field>
      <Actions saving={save.isPending} label="Guardar" onCancel={onDone} />
    </form>
  );
}
