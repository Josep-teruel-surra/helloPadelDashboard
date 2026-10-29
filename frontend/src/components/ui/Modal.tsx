import { X } from "lucide-react";
import { useEffect, useRef } from "react";
import type { ReactNode } from "react";

import { IconButton } from "./Button";

interface ModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
}

/** Diálogo modal nativo: gestiona foco, Escape y el fondo sin dependencias. */
export function Modal({ open, onClose, title, children }: ModalProps) {
  const ref = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) {
      dialog.showModal();
      // showModal enfoca el primer elemento (el botón de cerrar); preferimos el primer campo.
      dialog.querySelector<HTMLElement>("input, textarea, select")?.focus();
    }
    if (!open && dialog.open) dialog.close();
  }, [open]);

  return (
    <dialog
      ref={ref}
      onClose={onClose}
      onClick={(event) => {
        // Clic fuera del contenido (en el backdrop) cierra el diálogo.
        if (event.target === ref.current) onClose();
      }}
      aria-labelledby="modal-title"
      className="m-auto w-[calc(100%-2rem)] max-w-lg rounded-2xl bg-white p-0 text-stone-900 shadow-xl"
    >
      {open && (
        <div className="p-5 sm:p-6">
          <div className="mb-4 flex items-start justify-between gap-4">
            <h2 id="modal-title" className="text-lg font-bold">
              {title}
            </h2>
            <IconButton label="Cerrar" onClick={onClose} className="-mt-1 -mr-2">
              <X className="size-5" />
            </IconButton>
          </div>
          {children}
        </div>
      )}
    </dialog>
  );
}
