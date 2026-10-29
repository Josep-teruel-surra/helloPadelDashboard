import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate, useSearchParams } from "react-router";

import { notesApi } from "@/api/endpoints";
import { PageHeader } from "@/components/ui/Layout";
import { NoteEditor } from "./NoteEditor";
import type { NoteDraft } from "./NoteEditor";

export function NoteNewPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [searchParams] = useSearchParams();
  const scope = searchParams.get("ambito") === "empresa" ? "company" : "personal";
  const eventId = searchParams.get("evento");

  const create = useMutation({
    mutationFn: (draft: NoteDraft) => notesApi.create({ ...draft, event_id: eventId }),
    onSuccess: async (note) => {
      await queryClient.invalidateQueries({ queryKey: ["notes"] });
      await queryClient.invalidateQueries({ queryKey: ["home"] });
      navigate(`/notas/${note.id}`, { replace: true });
    },
  });

  return (
    <>
      <PageHeader
        title="Nueva nota"
        description={eventId ? "Quedará vinculada al evento desde el que la creas." : undefined}
      />
      <NoteEditor
        initial={{ scope, title: "", content_md: "" }}
        allowScopeChange
        saving={create.isPending}
        error={create.error}
        submitLabel="Crear nota"
        onSubmit={(draft) => create.mutate(draft)}
        onCancel={() => navigate(-1)}
      />
    </>
  );
}
