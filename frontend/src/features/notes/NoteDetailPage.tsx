import { useMutation, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Pencil, Trash2 } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router";

import { notesApi } from "@/api/endpoints";
import { queryKeys, useNote } from "@/api/queries";
import { Button } from "@/components/ui/Button";
import { Badge, ErrorAlert } from "@/components/ui/Feedback";
import { Spinner } from "@/components/ui/Spinner";
import { formatDateTime } from "@/lib/format";
import { Markdown } from "./Markdown";
import { NoteEditor } from "./NoteEditor";
import type { NoteDraft } from "./NoteEditor";

export function NoteDetailPage() {
  const { noteId = "" } = useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const note = useNote(noteId);
  const [editing, setEditing] = useState(false);

  const update = useMutation({
    mutationFn: ({ title, content_md }: NoteDraft) => notesApi.update(noteId, { title, content_md }),
    onSuccess: (updated) => {
      queryClient.setQueryData(queryKeys.note(noteId), updated);
      void queryClient.invalidateQueries({ queryKey: ["notes"] });
      setEditing(false);
    },
  });

  const remove = useMutation({
    mutationFn: () => notesApi.remove(noteId),
    onSuccess: () => {
      queryClient.removeQueries({ queryKey: queryKeys.note(noteId) });
      void queryClient.invalidateQueries({ queryKey: ["notes"] });
      navigate("/notas", { replace: true });
    },
  });

  const backLink = (
    <Link
      to={note.data?.scope === "company" ? "/notas?ambito=empresa" : "/notas"}
      className="mb-4 inline-flex items-center gap-1.5 text-sm font-medium text-stone-500 hover:text-stone-900"
    >
      <ArrowLeft className="size-4" aria-hidden />
      Notas
    </Link>
  );

  if (note.isPending) return <Spinner />;
  if (note.isError) {
    return (
      <>
        {backLink}
        <ErrorAlert error={note.error} />
      </>
    );
  }

  const data = note.data;

  if (editing) {
    return (
      <>
        <h1 className="mb-6 text-2xl font-extrabold tracking-tight">Editar nota</h1>
        <NoteEditor
          initial={{ scope: data.scope, title: data.title, content_md: data.content_md }}
          allowScopeChange={false}
          saving={update.isPending}
          error={update.error}
          submitLabel="Guardar"
          onSubmit={(draft) => update.mutate(draft)}
          onCancel={() => {
            update.reset();
            setEditing(false);
          }}
        />
      </>
    );
  }

  return (
    <article>
      {backLink}
      <div className="mb-6 flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <h1 className="text-2xl font-extrabold tracking-tight break-words">{data.title}</h1>
          <p className="mt-1 flex flex-wrap items-center gap-2 text-sm text-stone-500">
            <Badge tone={data.scope === "company" ? "brand" : "neutral"}>
              {data.scope === "company" ? "Empresa" : "Personal"}
            </Badge>
            {data.author.full_name} · Editada {formatDateTime(data.updated_at)}
          </p>
        </div>
        {data.can_edit && (
          <div className="flex gap-2">
            <Button variant="secondary" onClick={() => setEditing(true)}>
              <Pencil className="size-4" aria-hidden />
              Editar
            </Button>
            <Button
              variant="ghost"
              loading={remove.isPending}
              onClick={() => window.confirm("¿Borrar esta nota? No se puede deshacer.") && remove.mutate()}
              className="hover:bg-red-50 hover:text-red-700"
            >
              <Trash2 className="size-4" aria-hidden />
              Borrar
            </Button>
          </div>
        )}
      </div>

      <ErrorAlert error={remove.error} className="mb-4" />

      <div className="rounded-2xl border border-stone-200 bg-white p-5 sm:p-8">
        {data.content_md.trim() ? (
          <Markdown content={data.content_md} />
        ) : (
          <p className="text-stone-400">Esta nota está vacía.</p>
        )}
      </div>
    </article>
  );
}
