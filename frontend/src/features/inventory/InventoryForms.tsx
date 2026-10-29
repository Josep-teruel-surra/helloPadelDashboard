import { useMutation } from "@tanstack/react-query";
import { Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import type { FormEvent } from "react";

import { inventoryApi } from "@/api/endpoints";
import type { VariantInput } from "@/api/endpoints";
import type { MovementKind, Product, ProductCategory, Variant } from "@/api/types";
import { useCurrentUser } from "@/auth/AuthContext";
import { Button, IconButton } from "@/components/ui/Button";
import { ErrorAlert } from "@/components/ui/Feedback";
import { Field, inputClass } from "@/components/ui/Field";
import { Segmented } from "@/components/ui/Layout";
import { CATEGORY_LABELS, options } from "@/lib/labels";
import { useInvalidate } from "@/lib/useInvalidate";

const CATEGORY_OPTIONS = options(CATEGORY_LABELS);

function FormButtons({ saving, label, onCancel }: { saving: boolean; label: string; onCancel: () => void }) {
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

const toNumberOrNull = (value: string) => (value === "" ? null : Number(value));

// --- Producto nuevo (con variantes) o edición de sus datos ---

interface VariantDraft {
  label: string;
  sku: string;
  threshold: string;
  stock: string;
}

const EMPTY_VARIANT: VariantDraft = { label: "", sku: "", threshold: "", stock: "0" };

export function ProductForm({ product, onDone }: { product?: Product; onDone: () => void }) {
  const invalidate = useInvalidate();
  const user = useCurrentUser();
  const [name, setName] = useState(product?.name ?? "");
  const [category, setCategory] = useState<ProductCategory>(product?.category ?? "clothing");
  const [description, setDescription] = useState(product?.description ?? "");
  const [isActive, setIsActive] = useState(product?.is_active ?? true);
  const [variants, setVariants] = useState<VariantDraft[]>([{ ...EMPTY_VARIANT }]);

  const save = useMutation({
    mutationFn: () => {
      const base = { name, category, description: description || null };
      if (product) return inventoryApi.update(product.id, { ...base, is_active: isActive });
      return inventoryApi.create({
        ...base,
        variants: variants.map(
          (v): VariantInput => ({
            label: v.label,
            sku: v.sku || null,
            low_stock_threshold: toNumberOrNull(v.threshold),
            initial_stock: Number(v.stock || 0),
          }),
        ),
      });
    },
    onSuccess: async () => {
      await invalidate(["products"]);
      onDone();
    },
  });

  const remove = useMutation({
    mutationFn: () => inventoryApi.remove(product!.id),
    onSuccess: async () => {
      await invalidate(["products"]);
      onDone();
    },
  });

  const updateVariant = (index: number, field: keyof VariantDraft, value: string) =>
    setVariants((prev) => prev.map((v, i) => (i === index ? { ...v, [field]: value } : v)));

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    save.mutate();
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <ErrorAlert error={save.error ?? remove.error} />
      <Field label="Nombre" htmlFor="product-name">
        <input
          id="product-name"
          required
          maxLength={160}
          value={name}
          onChange={(e) => setName(e.target.value)}
          className={inputClass}
          placeholder="Ej.: Camiseta Hello Padel 2026"
        />
      </Field>
      <Segmented label="Categoría" options={CATEGORY_OPTIONS} value={category} onChange={setCategory} />
      <Field label="Descripción" htmlFor="product-description" hint="Opcional">
        <textarea
          id="product-description"
          rows={2}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className={inputClass}
        />
      </Field>

      {!product && (
        <fieldset className="space-y-2">
          <legend className="mb-1 text-sm font-medium text-stone-700">
            Variantes <span className="font-normal text-stone-500">(tallas, idiomas…)</span>
          </legend>
          <div className="hidden grid-cols-[1fr_1fr_5rem_5rem_2rem] gap-2 text-xs text-stone-500 sm:grid">
            <span>Variante</span>
            <span>SKU</span>
            <span>Stock inicial</span>
            <span>Avisar con</span>
          </div>
          {variants.map((v, index) => (
            <div key={index} className="grid grid-cols-2 gap-2 sm:grid-cols-[1fr_1fr_5rem_5rem_2rem]">
              <input
                aria-label="Variante"
                required
                maxLength={60}
                placeholder={category === "book" ? "Español" : "M"}
                value={v.label}
                onChange={(e) => updateVariant(index, "label", e.target.value)}
                className={inputClass}
              />
              <input
                aria-label="SKU"
                maxLength={60}
                placeholder="Opcional"
                value={v.sku}
                onChange={(e) => updateVariant(index, "sku", e.target.value)}
                className={inputClass}
              />
              <input
                aria-label="Stock inicial"
                type="number"
                min={0}
                value={v.stock}
                onChange={(e) => updateVariant(index, "stock", e.target.value)}
                className={inputClass}
              />
              <input
                aria-label="Avisar cuando queden"
                type="number"
                min={0}
                placeholder="–"
                value={v.threshold}
                onChange={(e) => updateVariant(index, "threshold", e.target.value)}
                className={inputClass}
              />
              <IconButton
                label="Quitar variante"
                disabled={variants.length === 1}
                onClick={() => setVariants((prev) => prev.filter((_, i) => i !== index))}
              >
                <Trash2 className="size-4" />
              </IconButton>
            </div>
          ))}
          <Button size="sm" variant="ghost" onClick={() => setVariants((prev) => [...prev, { ...EMPTY_VARIANT }])}>
            <Plus className="size-4" aria-hidden />
            Añadir variante
          </Button>
          <p className="text-xs text-stone-500">
            "Avisar con": se marca como stock bajo cuando las unidades disponibles lleguen a ese número.
          </p>
        </fieldset>
      )}

      {product && (
        <label className="flex cursor-pointer items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={isActive}
            onChange={(e) => setIsActive(e.target.checked)}
            className="size-4 accent-amber-500"
          />
          Producto activo (los desactivados no se pueden añadir a envíos)
        </label>
      )}

      <div className="flex flex-wrap items-center justify-between gap-2">
        {product && user.role === "admin" ? (
          <Button
            variant="ghost"
            size="sm"
            loading={remove.isPending}
            onClick={() => window.confirm(`¿Borrar «${product.name}»?`) && remove.mutate()}
            className="text-red-700 hover:bg-red-50"
          >
            <Trash2 className="size-4" aria-hidden />
            Borrar producto
          </Button>
        ) : (
          <span />
        )}
        <FormButtons saving={save.isPending} label={product ? "Guardar" : "Crear producto"} onCancel={onDone} />
      </div>
    </form>
  );
}

// --- Añadir o editar una variante ---

export function VariantForm({
  product,
  variant,
  onDone,
}: {
  product: Product;
  variant?: Variant;
  onDone: () => void;
}) {
  const invalidate = useInvalidate();
  const [label, setLabel] = useState(variant?.label ?? "");
  const [sku, setSku] = useState(variant?.sku ?? "");
  const [threshold, setThreshold] = useState(variant?.low_stock_threshold?.toString() ?? "");
  const [stock, setStock] = useState("0");
  const [isActive, setIsActive] = useState(variant?.is_active ?? true);

  const save = useMutation({
    mutationFn: () => {
      const data = { label, sku: sku || null, low_stock_threshold: toNumberOrNull(threshold) };
      return variant
        ? inventoryApi.updateVariant(variant.id, { ...data, is_active: isActive })
        : inventoryApi.addVariant(product.id, { ...data, initial_stock: Number(stock || 0) });
    },
    onSuccess: async () => {
      await invalidate(["products"]);
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
        <Field label="Variante" htmlFor="variant-label">
          <input id="variant-label" required maxLength={60} value={label} onChange={(e) => setLabel(e.target.value)} className={inputClass} />
        </Field>
        <Field label="SKU" htmlFor="variant-sku" hint="Opcional">
          <input id="variant-sku" maxLength={60} value={sku} onChange={(e) => setSku(e.target.value)} className={inputClass} />
        </Field>
        <Field label="Avisar con" htmlFor="variant-threshold" hint="Unidades disponibles">
          <input id="variant-threshold" type="number" min={0} value={threshold} onChange={(e) => setThreshold(e.target.value)} className={inputClass} />
        </Field>
        {!variant && (
          <Field label="Stock inicial" htmlFor="variant-stock">
            <input id="variant-stock" type="number" min={0} value={stock} onChange={(e) => setStock(e.target.value)} className={inputClass} />
          </Field>
        )}
      </div>
      {variant && (
        <label className="flex cursor-pointer items-center gap-2 text-sm">
          <input type="checkbox" checked={isActive} onChange={(e) => setIsActive(e.target.checked)} className="size-4 accent-amber-500" />
          Variante activa
        </label>
      )}
      <FormButtons saving={save.isPending} label={variant ? "Guardar" : "Añadir variante"} onCancel={onDone} />
    </form>
  );
}

// --- Registrar entrada, devolución o ajuste ---

const MOVEMENT_OPTIONS: { value: Exclude<MovementKind, "shipment">; label: string }[] = [
  { value: "restock", label: "Entrada" },
  { value: "return", label: "Devolución" },
  { value: "adjustment", label: "Ajuste" },
];

export function MovementForm({ product, onDone }: { product: Product; onDone: () => void }) {
  const invalidate = useInvalidate();
  const user = useCurrentUser();
  const variants = product.variants.filter((v) => v.is_active);
  const [variantId, setVariantId] = useState(variants[0]?.id ?? "");
  const [kind, setKind] = useState<Exclude<MovementKind, "shipment">>("restock");
  const [quantity, setQuantity] = useState("");
  const [note, setNote] = useState("");

  const save = useMutation({
    mutationFn: () =>
      inventoryApi.addMovement({ variant_id: variantId, kind, quantity: Number(quantity), note: note || null }),
    onSuccess: async () => {
      await invalidate(["products"], ["shipments"]);
      onDone();
    },
  });

  const kinds = MOVEMENT_OPTIONS.filter((o) => o.value !== "adjustment" || user.role === "admin");
  const selected = product.variants.find((v) => v.id === variantId);

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        save.mutate();
      }}
      className="space-y-4"
    >
      <ErrorAlert error={save.error} />
      <Segmented label="Tipo de movimiento" options={kinds} value={kind} onChange={setKind} />
      <p className="text-xs text-stone-500">
        {kind === "restock" && "Material que entra en el almacén (compra, reposición)."}
        {kind === "return" && "Material que vuelve (sobrante de un campus, devolución)."}
        {kind === "adjustment" &&
          "Corrección tras un recuento o por roturas. Usa un número negativo para restar."}
      </p>
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Variante" htmlFor="movement-variant">
          <select id="movement-variant" value={variantId} onChange={(e) => setVariantId(e.target.value)} className={inputClass}>
            {variants.map((v) => (
              <option key={v.id} value={v.id}>
                {v.label} ({v.on_hand} en almacén)
              </option>
            ))}
          </select>
        </Field>
        <Field label="Cantidad" htmlFor="movement-quantity">
          <input
            id="movement-quantity"
            type="number"
            required
            min={kind === "adjustment" ? undefined : 1}
            value={quantity}
            onChange={(e) => setQuantity(e.target.value)}
            className={inputClass}
          />
        </Field>
      </div>
      <Field label="Nota" htmlFor="movement-note" hint="Opcional: proveedor, motivo del ajuste…">
        <input id="movement-note" maxLength={500} value={note} onChange={(e) => setNote(e.target.value)} className={inputClass} />
      </Field>
      {selected && quantity && (
        <p className="text-sm text-stone-600">
          Quedarán <strong>{selected.on_hand + Number(quantity)}</strong> en almacén.
        </p>
      )}
      <FormButtons saving={save.isPending} label="Registrar" onCancel={onDone} />
    </form>
  );
}
