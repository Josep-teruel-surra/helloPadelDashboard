import uuid
from collections.abc import Iterable

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.errors import ConflictError, ForbiddenError, NotFoundError
from app.modules.inventory.models import (
    Product,
    ProductCategory,
    ProductVariant,
    StockMovement,
    StockMovementKind,
)
from app.modules.inventory.schemas import (
    MovementCreate,
    MovementRead,
    ProductCreate,
    ProductRead,
    ProductUpdate,
    VariantCreate,
    VariantRead,
    VariantRef,
    VariantUpdate,
)
from app.modules.users.models import User
from app.modules.users.schemas import UserSummary

# --- Stock ---


async def on_hand(session: AsyncSession, variant_ids: Iterable[uuid.UUID]) -> dict[uuid.UUID, int]:
    """Unidades en almacén por variante (las que no tienen movimientos, 0)."""
    ids = list(variant_ids)
    if not ids:
        return {}
    rows = await session.execute(
        select(StockMovement.variant_id, func.sum(StockMovement.quantity))
        .where(StockMovement.variant_id.in_(ids))
        .group_by(StockMovement.variant_id)
    )
    totals = {variant_id: int(total) for variant_id, total in rows}
    return {variant_id: totals.get(variant_id, 0) for variant_id in ids}


def _variant_read(variant: ProductVariant, stock: int) -> VariantRead:
    threshold = variant.low_stock_threshold
    return VariantRead.model_validate(variant).model_copy(
        update={"on_hand": stock, "low_stock": threshold is not None and stock <= threshold}
    )


async def to_reads(session: AsyncSession, products: list[Product]) -> list[ProductRead]:
    stock = await on_hand(session, (v.id for p in products for v in p.variants))
    reads = []
    for product in products:
        variants = [_variant_read(v, stock[v.id]) for v in product.variants]
        reads.append(
            ProductRead.model_validate(product).model_copy(
                update={"variants": variants, "total_on_hand": sum(v.on_hand for v in variants)}
            )
        )
    return reads


async def to_read(session: AsyncSession, product: Product) -> ProductRead:
    return (await to_reads(session, [product]))[0]


# --- Productos ---


async def list_products(
    session: AsyncSession,
    *,
    include_inactive: bool = False,
    category: ProductCategory | None = None,
    q: str | None = None,
) -> list[Product]:
    query = select(Product).order_by(Product.category, Product.name)
    if not include_inactive:
        query = query.where(Product.is_active.is_(True))
    if category:
        query = query.where(Product.category == category)
    if q:
        query = query.where(
            or_(
                Product.name.icontains(q, autoescape=True),
                Product.variants.any(ProductVariant.sku.icontains(q, autoescape=True)),
            )
        )
    return list(await session.scalars(query))


async def get_product(session: AsyncSession, product_id: uuid.UUID) -> Product:
    product = await session.get(Product, product_id)
    if product is None:
        raise NotFoundError("Producto no encontrado")
    return product


async def _check_name_free(
    session: AsyncSession, name: str, exclude: uuid.UUID | None = None
) -> None:
    query = select(Product.id).where(func.lower(Product.name) == name.lower())
    if exclude:
        query = query.where(Product.id != exclude)
    if await session.scalar(query):
        raise ConflictError("Ya existe un producto con ese nombre")


async def _check_sku_free(
    session: AsyncSession, sku: str | None, exclude: uuid.UUID | None = None
) -> None:
    if not sku:
        return
    query = select(ProductVariant.id).where(ProductVariant.sku == sku)
    if exclude:
        query = query.where(ProductVariant.id != exclude)
    if await session.scalar(query):
        raise ConflictError(f"El SKU {sku} ya está en uso")


def _new_variant(data: VariantCreate, position: int) -> ProductVariant:
    return ProductVariant(
        label=data.label,
        sku=data.sku,
        low_stock_threshold=data.low_stock_threshold,
        position=position,
    )


def _initial_stock(variant: ProductVariant, quantity: int, user: User) -> StockMovement:
    return StockMovement(
        variant=variant,
        kind=StockMovementKind.RESTOCK,
        quantity=quantity,
        note="Stock inicial",
        created_by_id=user.id,
    )


async def create_product(session: AsyncSession, user: User, data: ProductCreate) -> Product:
    await _check_name_free(session, data.name)
    for variant_data in data.variants:
        await _check_sku_free(session, variant_data.sku)

    product = Product(name=data.name, category=data.category, description=data.description)
    for position, variant_data in enumerate(data.variants):
        variant = _new_variant(variant_data, position)
        product.variants.append(variant)
        if variant_data.initial_stock:
            session.add(_initial_stock(variant, variant_data.initial_stock, user))
    session.add(product)
    await session.commit()
    return product


async def update_product(session: AsyncSession, product: Product, data: ProductUpdate) -> Product:
    changes = data.model_dump(exclude_unset=True)
    if "name" in changes:
        await _check_name_free(session, changes["name"], exclude=product.id)
    for field, value in changes.items():
        setattr(product, field, value)
    await session.commit()
    return product


async def _has_movements(session: AsyncSession, variant_ids: list[uuid.UUID]) -> bool:
    if not variant_ids:
        return False
    query = select(StockMovement.id).where(StockMovement.variant_id.in_(variant_ids)).limit(1)
    return await session.scalar(query) is not None


async def delete_product(session: AsyncSession, user: User, product: Product) -> None:
    if not user.is_admin:
        raise ForbiddenError("Solo un admin puede borrar productos")
    if await _has_movements(session, [v.id for v in product.variants]):
        raise ConflictError(
            "El producto tiene movimientos de stock: desactívalo en lugar de borrarlo"
        )
    await session.delete(product)
    await session.commit()


# --- Variantes ---


async def get_variant(session: AsyncSession, variant_id: uuid.UUID) -> ProductVariant:
    # Con el producto y todas sus variantes: hacen falta para validar etiquetas y responder.
    variant = await session.scalar(
        select(ProductVariant)
        .where(ProductVariant.id == variant_id)
        .options(joinedload(ProductVariant.product).selectinload(Product.variants))
    )
    if variant is None:
        raise NotFoundError("Variante no encontrada")
    return variant


def _check_label_free(product: Product, label: str, exclude: uuid.UUID | None = None) -> None:
    if any(v.label.lower() == label.lower() and v.id != exclude for v in product.variants):
        raise ConflictError(f"El producto ya tiene la variante «{label}»")


async def add_variant(
    session: AsyncSession, user: User, product: Product, data: VariantCreate
) -> Product:
    _check_label_free(product, data.label)
    await _check_sku_free(session, data.sku)
    position = max((v.position for v in product.variants), default=-1) + 1
    variant = _new_variant(data, position)
    product.variants.append(variant)
    if data.initial_stock:
        session.add(_initial_stock(variant, data.initial_stock, user))
    await session.commit()
    return product


async def update_variant(
    session: AsyncSession, variant: ProductVariant, data: VariantUpdate
) -> ProductVariant:
    changes = data.model_dump(exclude_unset=True)
    if "label" in changes:
        _check_label_free(variant.product, changes["label"], exclude=variant.id)
    if "sku" in changes:
        await _check_sku_free(session, changes["sku"], exclude=variant.id)
    for field, value in changes.items():
        setattr(variant, field, value)
    await session.commit()
    return variant


async def delete_variant(session: AsyncSession, user: User, variant: ProductVariant) -> None:
    if not user.is_admin:
        raise ForbiddenError("Solo un admin puede borrar variantes")
    if await _has_movements(session, [variant.id]):
        raise ConflictError("La variante tiene movimientos de stock: desactívala en su lugar")
    if len(variant.product.variants) == 1:
        raise ConflictError("Un producto necesita al menos una variante")
    await session.delete(variant)
    await session.commit()


# --- Movimientos ---


def movement_read(movement: StockMovement) -> MovementRead:
    variant = movement.variant
    return MovementRead(
        id=movement.id,
        kind=movement.kind,
        quantity=movement.quantity,
        note=movement.note,
        variant=VariantRef(
            id=variant.id,
            label=variant.label,
            product_id=variant.product_id,
            product_name=variant.product.name,
        ),
        created_by=UserSummary.model_validate(movement.created_by),
        created_at=movement.created_at,
    )


async def list_movements(
    session: AsyncSession,
    *,
    variant_id: uuid.UUID | None = None,
    product_id: uuid.UUID | None = None,
    limit: int = 100,
) -> list[StockMovement]:
    query = select(StockMovement).order_by(StockMovement.created_at.desc()).limit(limit)
    if variant_id:
        query = query.where(StockMovement.variant_id == variant_id)
    if product_id:
        query = query.join(ProductVariant).where(ProductVariant.product_id == product_id)
    return list(await session.scalars(query))


async def create_movement(session: AsyncSession, user: User, data: MovementCreate) -> StockMovement:
    if data.kind == StockMovementKind.ADJUSTMENT and not user.is_admin:
        raise ForbiddenError("Solo un admin puede hacer ajustes manuales de stock")
    await get_variant(session, data.variant_id)
    movement = StockMovement(**data.model_dump(), created_by_id=user.id)
    session.add(movement)
    await session.commit()
    await session.refresh(movement, ["variant", "created_by"])
    return movement
