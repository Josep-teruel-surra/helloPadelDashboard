import { useMutation } from "@tanstack/react-query";
import { ClipboardCheck, GraduationCap, Pencil, Plus, Search } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router";

import { certificationsApi } from "@/api/endpoints";
import { useCertifications, useExams, useStudents } from "@/api/queries";
import type { Certification, ExamKind, ExamSource, ExamStatus } from "@/api/types";
import { useCurrentUser } from "@/auth/AuthContext";
import { Button, IconButton } from "@/components/ui/Button";
import { CountryFlag } from "@/components/ui/Country";
import { Badge, EmptyState, ErrorAlert } from "@/components/ui/Feedback";
import { Field, inlineSelectClass, inputClass } from "@/components/ui/Field";
import { PageHeader, Segmented } from "@/components/ui/Layout";
import { Modal } from "@/components/ui/Modal";
import { Spinner } from "@/components/ui/Spinner";
import { cn } from "@/lib/cn";
import { EXAM_KIND_LABELS, EXAM_SOURCE_LABELS, EXAM_STATUS } from "@/lib/labels";
import { useDebouncedValue } from "@/lib/useDebouncedValue";
import { useInvalidate } from "@/lib/useInvalidate";
import { NewSubmissionForm } from "./ExamForms";
import { ExamRow } from "./ExamRow";

type View = "exams" | "students" | "certifications";

function Select<T extends string>({
  label,
  value,
  onChange,
  options,
  all,
}: {
  label: string;
  value: T | "";
  onChange: (v: T | "") => void;
  options: Record<T, string | { label: string }>;
  all: string;
}) {
  return (
    <select aria-label={label} value={value} onChange={(e) => onChange(e.target.value as T | "")} className={inlineSelectClass}>
      <option value="">{all}</option>
      {(Object.keys(options) as T[]).map((key) => {
        const entry = options[key];
        return (
          <option key={key} value={key}>
            {typeof entry === "string" ? entry : entry.label}
          </option>
        );
      })}
    </select>
  );
}

function ExamsList() {
  const [scope, setScope] = useState<"open" | "all">("open");
  const [mine, setMine] = useState(false);
  const [status, setStatus] = useState<ExamStatus | "">("");
  const [kind, setKind] = useState<ExamKind | "">("");
  const [source, setSource] = useState<ExamSource | "">("");
  const exams = useExams({
    open_only: scope === "open" ? true : undefined,
    assigned_to_me: mine || undefined,
    status: status || undefined,
    kind: kind || undefined,
    source: source || undefined,
  });

  return (
    <>
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <Segmented
          label="Entregas"
          options={[
            { value: "open", label: "Abiertas" },
            { value: "all", label: "Todas" },
          ]}
          value={scope}
          onChange={setScope}
        />
        <Select label="Estado" value={status} onChange={setStatus} options={EXAM_STATUS} all="Cualquier estado" />
        <Select label="Tipo" value={kind} onChange={setKind} options={EXAM_KIND_LABELS} all="Test y vídeo" />
        <Select label="Origen" value={source} onChange={setSource} options={EXAM_SOURCE_LABELS} all="Cualquier origen" />
        <label className="flex cursor-pointer items-center gap-2 text-sm font-medium text-stone-700">
          <input type="checkbox" checked={mine} onChange={(e) => setMine(e.target.checked)} className="size-4 accent-amber-500" />
          Solo las mías
        </label>
      </div>

      <ErrorAlert error={exams.error} className="mb-4" />
      {exams.isPending ? (
        <Spinner />
      ) : exams.data?.length ? (
        <ul className="divide-y divide-stone-100 overflow-hidden rounded-2xl border border-stone-200 bg-white">
          {exams.data.map((exam) => (
            <ExamRow key={exam.id} exam={exam} />
          ))}
        </ul>
      ) : (
        !exams.error && (
          <EmptyState
            icon={<ClipboardCheck className="size-8" />}
            title={scope === "open" ? "No hay correcciones pendientes" : "No hay entregas"}
          />
        )
      )}
    </>
  );
}

function StudentsList() {
  const [search, setSearch] = useState("");
  const q = useDebouncedValue(search.trim());
  const students = useStudents({ q: q || undefined, limit: 200 });

  return (
    <>
      <div className="relative mb-4 w-full sm:w-80">
        <Search className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-stone-400" aria-hidden />
        <input type="search" aria-label="Buscar alumnos" placeholder="Buscar por nombre o email…" value={search} onChange={(e) => setSearch(e.target.value)} className={cn(inputClass, "pl-9")} />
      </div>
      <ErrorAlert error={students.error} className="mb-4" />
      {students.isPending ? (
        <Spinner />
      ) : students.data?.length ? (
        <ul className="divide-y divide-stone-100 overflow-hidden rounded-2xl border border-stone-200 bg-white">
          {students.data.map((s) => (
            <li key={s.id}>
              <Link to={`/alumnos/${s.id}`} className="flex flex-wrap items-baseline gap-x-3 px-4 py-3 hover:bg-stone-50">
                <span className="font-semibold">
                  {s.country_code && <CountryFlag code={s.country_code} />} {s.full_name}
                </span>
                <span className="text-sm text-stone-500">{s.email}</span>
                {s.campus && <span className="text-xs text-stone-400">{s.campus.name}</span>}
              </Link>
            </li>
          ))}
        </ul>
      ) : (
        !students.error && <EmptyState icon={<GraduationCap className="size-8" />} title={q ? "Ningún alumno coincide" : "Todavía no hay alumnos"} />
      )}
    </>
  );
}

function CertificationForm({ certification, onDone }: { certification?: Certification; onDone: () => void }) {
  const invalidate = useInvalidate();
  const [name, setName] = useState(certification?.name ?? "");
  const [hasTest, setHasTest] = useState(certification?.has_test ?? true);
  const [hasVideo, setHasVideo] = useState(certification?.has_video ?? true);
  const [isActive, setIsActive] = useState(certification?.is_active ?? true);

  const save = useMutation({
    mutationFn: () => {
      const data = { name, has_test: hasTest, has_video: hasVideo };
      return certification
        ? certificationsApi.update(certification.id, { ...data, is_active: isActive })
        : certificationsApi.create(data);
    },
    onSuccess: async () => {
      await invalidate(["certifications"]);
      onDone();
    },
  });

  const checkbox = (label: string, checked: boolean, onChange: (v: boolean) => void) => (
    <label className="flex cursor-pointer items-center gap-2 text-sm">
      <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} className="size-4 accent-amber-500" />
      {label}
    </label>
  );

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        save.mutate();
      }}
      className="space-y-4"
    >
      <ErrorAlert error={save.error} />
      <Field label="Nombre" htmlFor="cert-name">
        <input id="cert-name" required maxLength={80} value={name} onChange={(e) => setName(e.target.value)} className={inputClass} placeholder="Ej.: Bronze 2" />
      </Field>
      <div className="flex flex-wrap gap-4">
        {checkbox("Tiene test", hasTest, setHasTest)}
        {checkbox("Tiene vídeo", hasVideo, setHasVideo)}
        {certification && checkbox("Activa", isActive, setIsActive)}
      </div>
      <div className="flex justify-end gap-2 pt-2">
        <Button variant="secondary" onClick={onDone}>
          Cancelar
        </Button>
        <Button type="submit" loading={save.isPending} disabled={!hasTest && !hasVideo}>
          {certification ? "Guardar" : "Crear"}
        </Button>
      </div>
    </form>
  );
}

function CertificationsAdmin() {
  const certifications = useCertifications(true);
  const [editing, setEditing] = useState<Certification | "new" | null>(null);

  return (
    <>
      <div className="mb-4">
        <Button onClick={() => setEditing("new")}>
          <Plus className="size-4" aria-hidden />
          Nueva certificación
        </Button>
      </div>
      <ErrorAlert error={certifications.error} className="mb-4" />
      {certifications.isPending ? (
        <Spinner />
      ) : (
        <ul className="divide-y divide-stone-100 overflow-hidden rounded-2xl border border-stone-200 bg-white">
          {certifications.data?.map((c) => (
            <li key={c.id} className={cn("flex items-center gap-3 px-4 py-3", !c.is_active && "opacity-60")}>
              <span className="flex-1 font-semibold">{c.name}</span>
              {c.has_test && <Badge>Test</Badge>}
              {c.has_video && <Badge>Vídeo</Badge>}
              {!c.is_active && <Badge tone="red">Desactivada</Badge>}
              <IconButton label={`Editar ${c.name}`} onClick={() => setEditing(c)}>
                <Pencil className="size-4" />
              </IconButton>
            </li>
          ))}
        </ul>
      )}
      <Modal open={editing !== null} onClose={() => setEditing(null)} title={editing === "new" ? "Nueva certificación" : "Editar certificación"}>
        <CertificationForm certification={editing === "new" || !editing ? undefined : editing} onDone={() => setEditing(null)} />
      </Modal>
    </>
  );
}

export function ExamsPage() {
  const user = useCurrentUser();
  const [view, setView] = useState<View>("exams");
  const [creating, setCreating] = useState(false);
  const views: { value: View; label: string }[] = [
    { value: "exams", label: "Entregas" },
    { value: "students", label: "Alumnos" },
    ...(user.role === "admin" ? [{ value: "certifications" as View, label: "Certificaciones" }] : []),
  ];

  return (
    <>
      <PageHeader
        title="Correcciones"
        description="Exámenes tipo test y vídeos recibidos por el examportal, WeTransfer u otros canales."
        actions={
          <Button onClick={() => setCreating(true)}>
            <Plus className="size-4" aria-hidden />
            Nueva entrega
          </Button>
        }
      />
      <div className="mb-4">
        <Segmented label="Vista" options={views} value={view} onChange={setView} />
      </div>

      {view === "exams" && <ExamsList />}
      {view === "students" && <StudentsList />}
      {view === "certifications" && <CertificationsAdmin />}

      <Modal open={creating} onClose={() => setCreating(false)} title="Nueva entrega">
        <NewSubmissionForm onDone={() => setCreating(false)} />
      </Modal>
    </>
  );
}
