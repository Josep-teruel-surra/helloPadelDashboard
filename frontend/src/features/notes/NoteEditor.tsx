import { useState } from "react";
import type { FormEvent } from "react";

import type { Scope } from "@/api/types";
import { Button } from "@/components/ui/Button";
import { ErrorAlert } from "@/components/ui/Feedback";
import { Field, inputClass } from "@/components/ui/Field";
import { Segmented } from "@/components/ui/Layout";
import { SCOPE_OPTIONS } from "@/lib/scope";
import { Markdown } from "./Markdown";

export interface NoteDraft {
  scope: Scope;
  title: string;
  content_md: string;
}

interface NoteEditorProps {
  initial: NoteDraft;
  /** El ámbito solo se elige al crear la nota. */
  allowScopeChange: boolean;
  saving: boolean;
  error: unknown;
  submitLabel: string;
  onSubmit: (draft: NoteDraft) => void;
  onCancel: () => void;
}

type EditorTab = "write" | "preview";

export function NoteEditor({
  initial,
  allowScopeChange,
  saving,
  error,
  submitLabel,
  onSubmit,
  onCancel,
}: NoteEditorProps) {
  const [draft, setDraft] = useState(initial);
  const [tab, setTab] = useState<EditorTab>("write");

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    onSubmit(draft);
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <ErrorAlert error={error} />

      {allowScopeChange && (
        <div className="space-y-1.5">
          <Segmented
            label="Ámbito"
            options={SCOPE_OPTIONS}
            value={draft.scope}
            onChange={(scope) => setDraft({ ...draft, scope })}
          />
          <p className="text-xs text-stone-500">
            {draft.scope === "personal"
              ? "Solo tú podrás verla."
              : "La verá todo el equipo. El ámbito no se puede cambiar después."}
          </p>
        </div>
      )}

      <Field label="Título" htmlFor="note-title">
        <input
          id="note-title"
          required
          maxLength={200}
          autoFocus
          value={draft.title}
          onChange={(e) => setDraft({ ...draft, title: e.target.value })}
          className={inputClass}
        />
      </Field>

      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <label htmlFor="note-content" className="text-sm font-medium text-stone-700">
            Contenido
          </label>
          <Segmented
            label="Modo del editor"
            options={[
              { value: "write", label: "Escribir" },
              { value: "preview", label: "Vista previa" },
            ]}
            value={tab}
            onChange={setTab}
          />
        </div>
        {tab === "write" ? (
          <textarea
            id="note-content"
            rows={16}
            value={draft.content_md}
            onChange={(e) => setDraft({ ...draft, content_md: e.target.value })}
            className={inputClass + " font-mono text-[13px] leading-relaxed"}
            placeholder={"# Título\n\n- Punto uno\n- **Importante**"}
          />
        ) : (
          <div className="min-h-64 rounded-lg border border-stone-200 bg-white px-4 py-3">
            {draft.content_md.trim() ? (
              <Markdown content={draft.content_md} />
            ) : (
              <p className="text-sm text-stone-400">Nada que previsualizar.</p>
            )}
          </div>
        )}
        <p className="text-xs text-stone-500">
          Admite markdown: **negrita**, _cursiva_, listas, enlaces, tablas y casillas `- [ ]`.
        </p>
      </div>

      <div className="flex justify-end gap-2">
        <Button variant="secondary" onClick={onCancel}>
          Cancelar
        </Button>
        <Button type="submit" loading={saving}>
          {submitLabel}
        </Button>
      </div>
    </form>
  );
}
