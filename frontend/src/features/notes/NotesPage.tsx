import { NotebookPen, Plus, Search } from "lucide-react";
import { useState } from "react";
import { Link, useSearchParams } from "react-router";

import { useNotes } from "@/api/queries";
import type { Note, Scope } from "@/api/types";
import { buttonClass } from "@/components/ui/Button";
import { EmptyState, ErrorAlert } from "@/components/ui/Feedback";
import { inputClass } from "@/components/ui/Field";
import { PageHeader, Segmented } from "@/components/ui/Layout";
import { Spinner } from "@/components/ui/Spinner";
import { cn } from "@/lib/cn";
import { markdownExcerpt, relativeTime } from "@/lib/format";
import { useDebouncedValue } from "@/lib/useDebouncedValue";

const SCOPE_TABS: { value: Scope; label: string }[] = [
  { value: "personal", label: "Mis notas" },
  { value: "company", label: "Empresa" },
];

export function NoteCard({ note }: { note: Note }) {
  const excerpt = markdownExcerpt(note.content_md);
  return (
    <Link
      to={`/notas/${note.id}`}
      className="flex flex-col rounded-2xl border border-stone-200 bg-white p-4 transition hover:border-stone-300 hover:shadow-sm"
    >
      <h3 className="line-clamp-2 font-bold break-words">{note.title}</h3>
      {excerpt && <p className="mt-1 line-clamp-3 text-sm text-stone-500">{excerpt}</p>}
      <p className="mt-auto pt-3 text-xs text-stone-400">
        {note.scope === "company" && `${note.author.full_name} · `}
        Editada {relativeTime(note.updated_at)}
      </p>
    </Link>
  );
}

export function NotesPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const scope: Scope = searchParams.get("ambito") === "empresa" ? "company" : "personal";
  const [search, setSearch] = useState("");
  const q = useDebouncedValue(search.trim());

  const notes = useNotes({ scope, q: q || undefined });

  return (
    <>
      <PageHeader
        title="Notas"
        description="Apuntes personales y documentación compartida del equipo."
        actions={
          <Link
            to={`/notas/nueva${scope === "company" ? "?ambito=empresa" : ""}`}
            className={buttonClass()}
          >
            <Plus className="size-4" aria-hidden />
            Nueva nota
          </Link>
        }
      />

      <div className="mb-4 flex flex-wrap items-center gap-3">
        <Segmented
          label="Ámbito"
          options={SCOPE_TABS}
          value={scope}
          onChange={(value) =>
            setSearchParams(value === "company" ? { ambito: "empresa" } : {}, { replace: true })
          }
        />
        <div className="relative w-full sm:w-72">
          <Search
            className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-stone-400"
            aria-hidden
          />
          <input
            type="search"
            aria-label="Buscar notas"
            placeholder="Buscar…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className={cn(inputClass, "pl-9")}
          />
        </div>
      </div>

      <ErrorAlert error={notes.error} className="mb-4" />

      {notes.isPending ? (
        <Spinner />
      ) : notes.data && notes.data.length > 0 ? (
        <div
          className={cn(
            "grid gap-3 sm:grid-cols-2 lg:grid-cols-3",
            notes.isFetching && "opacity-70",
          )}
        >
          {notes.data.map((note) => (
            <NoteCard key={note.id} note={note} />
          ))}
        </div>
      ) : (
        !notes.error && (
          <EmptyState
            icon={<NotebookPen className="size-8" />}
            title={q ? "Ninguna nota coincide con la búsqueda" : "Todavía no hay notas"}
            description={
              scope === "personal"
                ? "Tus notas personales solo las ves tú."
                : "Las notas de empresa las lee todo el equipo."
            }
          />
        )
      )}
    </>
  );
}
