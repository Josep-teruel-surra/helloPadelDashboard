import { ArrowDownToLine, History, Package, Pencil, Plus, TriangleAlert } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router";

import { useMovements, useProducts } from "@/api/queries";
import type { Product, ProductCategory, Variant } from "@/api/types";
import { Button, IconButton } from "@/components/ui/Button";
import { Badge, EmptyState, ErrorAlert } from "@/components/ui/Feedback";
import { PageHeader, Segmented } from "@/components/ui/Layout";
import { Modal } from "@/components/ui/Modal";
import { Spinner } from "@/components/ui/Spinner";
import { cn } from "@/lib/cn";
import { formatDateTime } from "@/lib/format";
import { CATEGORY_LABELS, MOVEMENT_KIND_LABELS } from "@/lib/labels";
import { MovementForm, ProductForm, VariantForm } from "./InventoryForms";

type CategoryFilter = ProductCategory | "all";
const CATEGORY_FILTERS: { value: CategoryFilter; label: string }[] = [
  { value: "all", label: "Todo" },
  { value: "clothing", label: "Ropa" },
  { value: "book", label: "Libros" },
  { value: "other", label: "Otros" },
];

type Dialog =
  | { kind: "new-product" }
  | { kind: "edit-product"; product: Product }
  | { kind: "new-variant"; product: Product }
  | { kind: "edit-variant"; product: Product; variant: Variant }
  | { kind: "movement"; product: Product }
  | null;

const DIALOG_TITLES = {
  "new-product": "Nuevo producto",
  "edit-product": "Editar producto",
  "new-variant": "Añadir variante",
  "edit-variant": "Editar variante",
  movement: "Registrar movimiento",
} as const;

function MovementsList({ productId }: { productId: string }) {
  const movements = useMovements({ product_id: productId, limit: 15 });
  if (movements.isPending) return <Spinner />;
  if (!movements.data?.length) return <p className="py-3 text-sm text-stone-400">Sin movimientos.</p>;
  return (
    <ul className="divide-y divide-stone-100 text-sm">
      {movements.data.map((m) => (
        <li key={m.id} className="flex flex-wrap items-baseline gap-x-3 gap-y-0.5 py-2">
          <span className={cn("w-12 font-semibold tabular-nums", m.quantity > 0 ? "text-emerald-700" : "text-red-700")}>
            {m.quantity > 0 ? `+${m.quantity}` : m.quantity}
          </span>
          <span className="font-medium">{m.variant.label}</span>
          <span className="text-stone-500">
            {MOVEMENT_KIND_LABELS[m.kind]}
            {m.shipment_id && (
              <>
                {" "}
                <Link to={`/envios/${m.shipment_id}`} className="text-amber-700 hover:underline">
                  #{m.shipment_number}
                </Link>
              </>
            )}
            {m.note && !m.shipment_id && ` · ${m.note}`}
          </span>
          <span className="ml-auto text-xs text-stone-400">
            {m.created_by.full_name} · {formatDateTime(m.created_at)}
          </span>
        </li>
      ))}
    </ul>
  );
}

function ProductCard({ product, onDialog }: { product: Product; onDialog: (d: Dialog) => void }) {
  const [showHistory, setShowHistory] = useState(false);
  const lowStock = product.variants.filter((v) => v.is_active && v.low_stock).length;

  return (
    <section className={cn("rounded-2xl border border-stone-200 bg-white", !product.is_active && "opacity-60")}>
      <div className="flex flex-wrap items-start justify-between gap-3 p-4 sm:p-5">
        <div className="min-w-0">
          <h2 className="flex flex-wrap items-center gap-2 font-bold">
            {product.name}
            <Badge>{CATEGORY_LABELS[product.category]}</Badge>
            {!product.is_active && <Badge tone="red">Desactivado</Badge>}
            {lowStock > 0 && (
              <Badge tone="amber">
                <TriangleAlert className="size-3" aria-hidden />
                {lowStock} con stock bajo
              </Badge>
            )}
          </h2>
          <p className="mt-0.5 text-sm text-stone-500">
            {product.total_on_hand} en almacén · {product.total_available} disponibles
          </p>
        </div>
        <div className="flex flex-wrap gap-1.5">
          <Button size="sm" onClick={() => onDialog({ kind: "movement", product })} disabled={!product.is_active}>
            <ArrowDownToLine className="size-4" aria-hidden />
            Movimiento
          </Button>
          <Button size="sm" variant="secondary" onClick={() => onDialog({ kind: "new-variant", product })}>
            <Plus className="size-4" aria-hidden />
            Variante
          </Button>
          <IconButton label="Editar producto" onClick={() => onDialog({ kind: "edit-product", product })}>
            <Pencil className="size-4" />
          </IconButton>
          <IconButton
            label={showHistory ? "Ocultar historial" : "Ver historial"}
            aria-pressed={showHistory}
            onClick={() => setShowHistory((v) => !v)}
            className={showHistory ? "bg-stone-200 text-stone-900" : undefined}
          >
            <History className="size-4" />
          </IconButton>
        </div>
      </div>

      <div className="overflow-x-auto border-t border-stone-100">
        <table className="w-full text-sm">
          <thead className="text-left text-xs text-stone-500">
            <tr>
              <th className="px-4 py-2 font-medium sm:px-5">Variante</th>
              <th className="px-2 py-2 text-right font-medium">Almacén</th>
              <th className="px-2 py-2 text-right font-medium">Apartado</th>
              <th className="px-2 py-2 text-right font-medium">Disponible</th>
              <th className="w-10" />
            </tr>
          </thead>
          <tbody className="divide-y divide-stone-100">
            {product.variants.map((v) => (
              <tr key={v.id} className={cn(!v.is_active && "text-stone-400")}>
                <td className="px-4 py-2 sm:px-5">
                  <span className="font-medium">{v.label}</span>
                  {v.sku && <span className="ml-2 text-xs text-stone-400">{v.sku}</span>}
                  {!v.is_active && <span className="ml-2 text-xs">(desactivada)</span>}
                </td>
                <td className="px-2 py-2 text-right tabular-nums">{v.on_hand}</td>
                <td className="px-2 py-2 text-right text-stone-500 tabular-nums">{v.reserved || "–"}</td>
                <td className="px-2 py-2 text-right tabular-nums">
                  <span
                    className={cn(
                      "font-semibold",
                      v.available < 0 && "text-red-700",
                      v.available >= 0 && v.low_stock && "text-amber-700",
                    )}
                    title={v.low_stock_threshold != null ? `Aviso con ${v.low_stock_threshold}` : undefined}
                  >
                    {v.available}
                  </span>
                </td>
                <td className="pr-2">
                  <IconButton
                    label={`Editar variante ${v.label}`}
                    onClick={() => onDialog({ kind: "edit-variant", product, variant: v })}
                  >
                    <Pencil className="size-3.5" />
                  </IconButton>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showHistory && (
        <div className="border-t border-stone-100 px-4 pb-2 sm:px-5">
          <MovementsList productId={product.id} />
        </div>
      )}
    </section>
  );
}

export function InventoryPage() {
  const [category, setCategory] = useState<CategoryFilter>("all");
  const [includeInactive, setIncludeInactive] = useState(false);
  const [dialog, setDialog] = useState<Dialog>(null);
  const products = useProducts({
    include_inactive: includeInactive,
    category: category === "all" ? undefined : category,
  });
  const close = () => setDialog(null);

  return (
    <>
      <PageHeader
        title="Material"
        description="Stock de camisetas, libros y demás material. «Apartado» es lo reservado en envíos en preparación."
        actions={
          <Button onClick={() => setDialog({ kind: "new-product" })}>
            <Plus className="size-4" aria-hidden />
            Nuevo producto
          </Button>
        }
      />

      <div className="mb-4 flex flex-wrap items-center gap-3">
        <Segmented label="Categoría" options={CATEGORY_FILTERS} value={category} onChange={setCategory} />
        <label className="flex cursor-pointer items-center gap-2 text-sm font-medium text-stone-700">
          <input
            type="checkbox"
            checked={includeInactive}
            onChange={(e) => setIncludeInactive(e.target.checked)}
            className="size-4 accent-amber-500"
          />
          Mostrar desactivados
        </label>
      </div>

      <ErrorAlert error={products.error} className="mb-4" />

      {products.isPending ? (
        <Spinner />
      ) : products.data?.length ? (
        <div className="space-y-4">
          {products.data.map((product) => (
            <ProductCard key={product.id} product={product} onDialog={setDialog} />
          ))}
        </div>
      ) : (
        !products.error && <EmptyState icon={<Package className="size-8" />} title="No hay material registrado" />
      )}

      <Modal open={dialog !== null} onClose={close} title={dialog ? DIALOG_TITLES[dialog.kind] : ""}>
        {dialog?.kind === "new-product" && <ProductForm onDone={close} />}
        {dialog?.kind === "edit-product" && <ProductForm product={dialog.product} onDone={close} />}
        {dialog?.kind === "new-variant" && <VariantForm product={dialog.product} onDone={close} />}
        {dialog?.kind === "edit-variant" && (
          <VariantForm product={dialog.product} variant={dialog.variant} onDone={close} />
        )}
        {dialog?.kind === "movement" && <MovementForm product={dialog.product} onDone={close} />}
      </Modal>
    </>
  );
}
