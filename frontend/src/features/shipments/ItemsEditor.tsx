import { Plus, Trash2 } from "lucide-react";

import type { ItemInput } from "@/api/endpoints";
import { useProducts } from "@/api/queries";
import { Button, IconButton } from "@/components/ui/Button";
import { inputClass } from "@/components/ui/Field";
import { Spinner } from "@/components/ui/Spinner";
import { cn } from "@/lib/cn";

export interface ItemDraft {
  variant_id: string;
  quantity: string;
}

export const toItemInputs = (items: ItemDraft[]): ItemInput[] =>
  items
    .filter((i) => i.variant_id && Number(i.quantity) > 0)
    .map((i) => ({ variant_id: i.variant_id, quantity: Number(i.quantity) }));

interface ItemsEditorProps {
  items: ItemDraft[];
  onChange: (items: ItemDraft[]) => void;
  /** Al editar un envío en preparación, lo que ya tenía apartado vuelve a contar como disponible. */
  alreadyReserved?: Record<string, number>;
}

/** Líneas de material (variante + cantidad) mostrando lo disponible de cada variante. */
export function ItemsEditor({ items, onChange, alreadyReserved = {} }: ItemsEditorProps) {
  const products = useProducts();
  if (products.isPending) return <Spinner label="Cargando material…" />;

  const variants = new Map(
    (products.data ?? []).flatMap((p) =>
      p.variants
        .filter((v) => v.is_active)
        .map((v) => [v.id, { ...v, product: p.name, available: v.available + (alreadyReserved[v.id] ?? 0) }]),
    ),
  );
  const chosen = new Set(items.map((i) => i.variant_id));
  const update = (index: number, patch: Partial<ItemDraft>) =>
    onChange(items.map((item, i) => (i === index ? { ...item, ...patch } : item)));

  return (
    <div className="space-y-2">
      {items.map((item, index) => {
        const variant = variants.get(item.variant_id);
        const short = variant && Number(item.quantity) > variant.available;
        return (
          <div key={index}>
            <div className="flex gap-2">
              <div className="min-w-0 flex-1">
              <select
                aria-label="Material"
                required
                value={item.variant_id}
                onChange={(e) => update(index, { variant_id: e.target.value })}
                className={cn(inputClass, "min-w-0")}
              >
                <option value="">Elige material…</option>
                {(products.data ?? [])
                  .filter((p) => p.is_active)
                  .map((p) => (
                    <optgroup key={p.id} label={p.name}>
                      {p.variants
                        .filter((v) => v.is_active)
                        .map((v) => {
                          const available = variants.get(v.id)?.available ?? 0;
                          return (
                            <option
                              key={v.id}
                              value={v.id}
                              disabled={chosen.has(v.id) && v.id !== item.variant_id}
                            >
                              {p.name} · {v.label} ({available} disp.)
                            </option>
                          );
                        })}
                    </optgroup>
                  ))}
              </select>
              </div>
              {/* inputClass lleva w-full: el ancho fijo va en el contenedor. */}
              <div className="w-20 shrink-0">
                <input
                  aria-label="Cantidad"
                  type="number"
                  required
                  min={1}
                  value={item.quantity}
                  onChange={(e) => update(index, { quantity: e.target.value })}
                  className={cn(inputClass, short && "border-amber-500")}
                />
              </div>
              <IconButton
                label="Quitar línea"
                disabled={items.length === 1}
                onClick={() => onChange(items.filter((_, i) => i !== index))}
                className="mt-1 shrink-0"
              >
                <Trash2 className="size-4" />
              </IconButton>
            </div>
            {short && (
              <p className="mt-1 text-xs text-amber-700">
                Solo hay {variant.available} disponibles: se puede apartar igualmente, pero faltará stock.
              </p>
            )}
          </div>
        );
      })}
      <Button size="sm" variant="ghost" onClick={() => onChange([...items, { variant_id: "", quantity: "1" }])}>
        <Plus className="size-4" aria-hidden />
        Añadir línea
      </Button>
    </div>
  );
}
