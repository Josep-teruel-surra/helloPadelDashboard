import uuid

from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from app.core.security import utcnow
from app.modules.campuses.models import Campus
from app.modules.campuses.schemas import CampusSummary
from app.modules.events.models import Event
from app.modules.events.schemas import EventRef
from app.modules.inventory import service as inventory_service
from app.modules.inventory.models import Product, ProductVariant, StockMovement, StockMovementKind
from app.modules.shipments.models import (
    SENT_STATUSES,
    Shipment,
    ShipmentItem,
    ShipmentStatus,
)
from app.modules.shipments.schemas import (
    ItemIn,
    SentMaterialRow,
    ShipmentCreate,
    ShipmentItemRead,
    ShipmentRead,
    ShipmentUpdate,
    StatusChange,
)
from app.modules.todos import service as todos_service
from app.modules.todos.models import Todo
from app.modules.users.models import User
from app.modules.users.schemas import UserSummary
from app.shared.address import Address

STATUS_LABELS = {
    ShipmentStatus.PREPARING: "en preparación",
    ShipmentStatus.SHIPPED: "enviado",
    ShipmentStatus.DELIVERED: "entregado",
    ShipmentStatus.INCIDENT: "con incidencia",
    ShipmentStatus.CANCELLED: "cancelado",
}

TRANSITIONS: dict[ShipmentStatus, set[ShipmentStatus]] = {
    ShipmentStatus.PREPARING: {ShipmentStatus.SHIPPED, ShipmentStatus.CANCELLED},
    ShipmentStatus.SHIPPED: {
        ShipmentStatus.DELIVERED,
        ShipmentStatus.INCIDENT,
        ShipmentStatus.CANCELLED,
    },
    ShipmentStatus.INCIDENT: {
        ShipmentStatus.SHIPPED,
        ShipmentStatus.DELIVERED,
        ShipmentStatus.CANCELLED,
    },
    ShipmentStatus.DELIVERED: {ShipmentStatus.INCIDENT},
    ShipmentStatus.CANCELLED: set(),
}


def can_delete(user: User, shipment: Shipment) -> bool:
    return shipment.status == ShipmentStatus.PREPARING and (
        user.is_admin or shipment.created_by_id == user.id
    )


# --- Lectura ---


def _item_read(item: ShipmentItem) -> ShipmentItemRead:
    variant = item.variant
    return ShipmentItemRead(
        variant_id=variant.id,
        product_id=variant.product_id,
        product_name=variant.product.name,
        label=variant.label,
        quantity=item.quantity,
    )


def _sorted_items(shipment: Shipment) -> list[ShipmentItem]:
    return sorted(shipment.items, key=lambda i: (i.variant.product.name, i.variant.position))


async def _stock_warnings(
    session: AsyncSession, shipments: list[Shipment]
) -> dict[uuid.UUID, list[str]]:
    preparing = [s for s in shipments if s.status == ShipmentStatus.PREPARING]
    levels = await inventory_service.stock_levels(
        session, {i.variant_id for s in preparing for i in s.items}
    )
    warnings: dict[uuid.UUID, list[str]] = {}
    for shipment in preparing:
        for item in _sorted_items(shipment):
            level = levels[item.variant_id]
            if level.available < 0:
                warnings.setdefault(shipment.id, []).append(
                    f"{item.variant.product.name} · {item.variant.label}: faltan "
                    f"{-level.available} (en almacén {level.on_hand}, apartadas {level.reserved})"
                )
    return warnings


async def to_reads(
    session: AsyncSession, shipments: list[Shipment], user: User
) -> list[ShipmentRead]:
    warnings = await _stock_warnings(session, shipments)
    return [
        ShipmentRead(
            id=s.id,
            number=s.number,
            status=s.status,
            campus=CampusSummary.model_validate(s.campus),
            event=EventRef.model_validate(s.event) if s.event else None,
            items=[_item_read(i) for i in _sorted_items(s)],
            total_units=sum(i.quantity for i in s.items),
            shipping_address=Address.from_model(s),
            carrier=s.carrier,
            tracking_number=s.tracking_number,
            tracking_url=s.tracking_url,
            needed_by=s.needed_by,
            shipped_at=s.shipped_at,
            delivered_at=s.delivered_at,
            assignee=UserSummary.model_validate(s.assignee) if s.assignee else None,
            created_by=UserSummary.model_validate(s.created_by),
            cost_amount=s.cost_amount,
            cost_currency=s.cost_currency,
            notes_md=s.notes_md,
            created_at=s.created_at,
            updated_at=s.updated_at,
            can_delete=can_delete(user, s),
            stock_warnings=warnings.get(s.id, []),
        )
        for s in shipments
    ]


async def to_read(session: AsyncSession, shipment: Shipment, user: User) -> ShipmentRead:
    return (await to_reads(session, [shipment], user))[0]


async def list_shipments(
    session: AsyncSession,
    user: User,
    *,
    status: ShipmentStatus | None = None,
    campus_id: uuid.UUID | None = None,
    event_id: uuid.UUID | None = None,
    assigned_to_me: bool = False,
    limit: int = 200,
) -> list[Shipment]:
    query = select(Shipment).order_by(Shipment.number.desc()).limit(limit)
    if status:
        query = query.where(Shipment.status == status)
    if campus_id:
        query = query.where(Shipment.campus_id == campus_id)
    if event_id:
        query = query.where(Shipment.event_id == event_id)
    if assigned_to_me:
        query = query.where(Shipment.assignee_id == user.id)
    return list(await session.scalars(query))


async def get_shipment(session: AsyncSession, shipment_id: uuid.UUID) -> Shipment:
    shipment = await session.get(Shipment, shipment_id)
    if shipment is None:
        raise NotFoundError("Envío no encontrado")
    return shipment


async def _reload(session: AsyncSession, shipment: Shipment) -> Shipment:
    """Recarga tras commit para tener número, relaciones y artículos al día."""
    await session.refresh(shipment)
    return shipment


# --- Escritura ---


async def _validated_items(session: AsyncSession, items: list[ItemIn]) -> list[ShipmentItem]:
    ids = [item.variant_id for item in items]
    variants = {
        v.id: v
        for v in await session.scalars(select(ProductVariant).where(ProductVariant.id.in_(ids)))
    }
    for variant_id in ids:
        variant = variants.get(variant_id)
        if variant is None:
            raise BadRequestError("Alguna variante del envío no existe")
        if not variant.is_active or not variant.product.is_active:
            raise BadRequestError(f"«{variant.product.name} · {variant.label}» está desactivado")
    return [ShipmentItem(variant_id=i.variant_id, quantity=i.quantity) for i in items]


async def _complete_material_task(session: AsyncSession, event: Event) -> None:
    """Al apartar el material de un evento, su tarea automática queda hecha."""
    if not event.material_todo_id:
        return
    todo = await session.get(Todo, event.material_todo_id)
    if todo and not todo.is_done:
        todo.is_done = True
        todo.completed_at = utcnow()


async def create_shipment(session: AsyncSession, user: User, data: ShipmentCreate) -> Shipment:
    event = None
    if data.event_id:
        event = await session.get(Event, data.event_id)
        if event is None:
            raise BadRequestError("El evento no existe")
        if data.campus_id and data.campus_id != event.campus_id:
            raise BadRequestError("El campus no coincide con el del evento")

    campus_id = data.campus_id or (event.campus_id if event else None)
    campus = await session.get(Campus, campus_id) if campus_id else None
    if campus is None or not campus.is_active:
        raise BadRequestError("El campus no existe o está desactivado")

    assignee_id = data.assignee_id or (event.responsible_id if event else None)
    if assignee_id:
        await todos_service.check_assignee(session, assignee_id)

    shipment = Shipment(
        campus_id=campus.id,
        event_id=event.id if event else None,
        assignee_id=assignee_id,
        needed_by=data.needed_by or (event.start_date if event else None),
        carrier=data.carrier,
        tracking_number=data.tracking_number,
        tracking_url=data.tracking_url,
        cost_amount=data.cost_amount,
        cost_currency=data.cost_currency,
        notes_md=data.notes_md,
        created_by_id=user.id,
        items=await _validated_items(session, data.items),
    )
    Address.apply_to(shipment, data.shipping_address or Address.from_model(campus))
    session.add(shipment)

    if event:
        await _complete_material_task(session, event)

    await session.commit()
    return await _reload(session, shipment)


async def replace_items(session: AsyncSession, shipment: Shipment, items: list[ItemIn]) -> Shipment:
    if shipment.status != ShipmentStatus.PREPARING:
        raise ConflictError("Solo se puede cambiar el contenido de un envío en preparación")
    new_items = await _validated_items(session, items)
    shipment.items.clear()
    await session.flush()  # libera la restricción única (envío, variante) antes de reinsertar
    shipment.items.extend(new_items)
    await session.commit()
    return await _reload(session, shipment)


async def update_shipment(
    session: AsyncSession, shipment: Shipment, data: ShipmentUpdate
) -> Shipment:
    changes = data.model_dump(exclude_unset=True, exclude={"shipping_address"})
    if changes.get("assignee_id"):
        await todos_service.check_assignee(session, changes["assignee_id"])
    for field, value in changes.items():
        setattr(shipment, field, value)
    if "shipping_address" in data.model_fields_set:
        Address.apply_to(shipment, data.shipping_address)
    await session.commit()
    return await _reload(session, shipment)


def _movements(
    shipment: Shipment, kind: StockMovementKind, sign: int, note: str, user: User
) -> list[StockMovement]:
    return [
        StockMovement(
            variant_id=item.variant_id,
            kind=kind,
            quantity=sign * item.quantity,
            shipment_id=shipment.id,
            note=note,
            created_by_id=user.id,
        )
        for item in shipment.items
    ]


async def change_status(
    session: AsyncSession, user: User, shipment: Shipment, data: StatusChange
) -> Shipment:
    old, new = shipment.status, data.status
    if new not in TRANSITIONS[old]:
        raise BadRequestError(
            f"Un envío {STATUS_LABELS[old]} no puede pasar a {STATUS_LABELS[new]}"
        )

    for field in ("carrier", "tracking_number", "tracking_url"):
        if field in data.model_fields_set:
            setattr(shipment, field, getattr(data, field))

    now = utcnow()
    if old == ShipmentStatus.PREPARING and new == ShipmentStatus.SHIPPED:
        # Sale del almacén: deja de estar apartado y se descuenta.
        shipment.shipped_at = now
        session.add_all(
            _movements(
                shipment,
                StockMovementKind.SHIPMENT,
                -1,
                f"Envío #{shipment.number} a {shipment.campus.name}",
                user,
            )
        )
    elif new == ShipmentStatus.CANCELLED and old in SENT_STATUSES:
        session.add_all(
            _movements(
                shipment, StockMovementKind.RETURN, 1, f"Envío #{shipment.number} cancelado", user
            )
        )
    if new == ShipmentStatus.DELIVERED:
        shipment.delivered_at = now

    shipment.status = new
    await session.commit()
    return await _reload(session, shipment)


async def delete_shipment(session: AsyncSession, user: User, shipment: Shipment) -> None:
    if shipment.status != ShipmentStatus.PREPARING:
        raise ConflictError("Solo se pueden borrar envíos en preparación: cancélalo")
    if not can_delete(user, shipment):
        raise ForbiddenError("Solo quien creó el envío o un admin pueden borrarlo")
    await session.delete(shipment)
    await session.commit()


# --- Material enviado ---


async def sent_material(
    session: AsyncSession, *, campus_id: uuid.UUID | None = None, year: int | None = None
) -> list[SentMaterialRow]:
    """Unidades enviadas (envíos enviados, entregados o con incidencia) por campus y variante."""
    query = (
        select(Shipment.campus_id, ShipmentItem.variant_id, func.sum(ShipmentItem.quantity))
        .join(ShipmentItem)
        .where(Shipment.status.in_(SENT_STATUSES))
        .group_by(Shipment.campus_id, ShipmentItem.variant_id)
    )
    if campus_id:
        query = query.where(Shipment.campus_id == campus_id)
    if year:
        query = query.where(extract("year", Shipment.shipped_at) == year)
    rows = (await session.execute(query)).all()
    if not rows:
        return []

    campuses = {
        c.id: c
        for c in await session.scalars(select(Campus).where(Campus.id.in_({r[0] for r in rows})))
    }
    variants = {
        v.id: v
        for v in await session.scalars(
            select(ProductVariant).join(Product).where(ProductVariant.id.in_({r[1] for r in rows}))
        )
    }
    result = [
        SentMaterialRow(
            campus=CampusSummary.model_validate(campuses[cid]),
            product_id=variants[vid].product_id,
            product_name=variants[vid].product.name,
            variant_id=vid,
            label=variants[vid].label,
            quantity=int(quantity),
        )
        for cid, vid, quantity in rows
    ]
    return sorted(
        result,
        key=lambda r: (r.campus.name, r.product_name, variants[r.variant_id].position),
    )
