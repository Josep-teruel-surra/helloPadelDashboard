from datetime import timedelta

from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import local_today, utcnow
from app.modules.events import service as events_service
from app.modules.events.models import Event, EventStatus
from app.modules.home.schemas import HomeSummary, LogisticsSummary, LowStockItem, TodoSummary
from app.modules.inventory import service as inventory_service
from app.modules.inventory.models import Product, ProductVariant
from app.modules.notes import service as notes_service
from app.modules.shipments import service as shipments_service
from app.modules.shipments.models import Shipment, ShipmentStatus
from app.modules.todos import service as todos_service
from app.modules.todos.models import Todo
from app.modules.users.models import User
from app.shared.enums import Scope
from app.shared.permissions import visible_to

LIST_LIMIT = 5
NOTES_LIMIT = 4
EVENTS_HORIZON = timedelta(days=30)
# Un envío que lleva más de esto en camino merece confirmar si ha llegado.
DELIVERY_FOLLOW_UP = timedelta(days=10)
LOW_STOCK_LIMIT = 8


async def _count(session: AsyncSession, *conditions: ColumnElement[bool]) -> int:
    query = select(func.count()).select_from(Todo).where(*conditions)
    return await session.scalar(query) or 0


async def _low_stock(session: AsyncSession) -> list[LowStockItem]:
    variants = list(
        await session.scalars(
            select(ProductVariant)
            .join(Product)
            .where(ProductVariant.is_active.is_(True), Product.is_active.is_(True))
        )
    )
    levels = await inventory_service.stock_levels(session, (v.id for v in variants))
    items = [
        LowStockItem(
            product_id=v.product_id,
            product_name=v.product.name,
            variant_id=v.id,
            label=v.label,
            available=levels[v.id].available,
            low_stock_threshold=v.low_stock_threshold,
        )
        for v in variants
        if levels[v.id].available < 0
        or (v.low_stock_threshold is not None and levels[v.id].available <= v.low_stock_threshold)
    ]
    return sorted(items, key=lambda i: (i.available, i.product_name))[:LOW_STOCK_LIMIT]


async def _logistics(session: AsyncSession, user: User) -> LogisticsSummary:
    today = local_today()
    events = await session.scalars(
        select(Event)
        .where(
            Event.end_date >= today,
            Event.start_date <= today + EVENTS_HORIZON,
            Event.status != EventStatus.CANCELLED,
        )
        .order_by(Event.start_date)
        .limit(LIST_LIMIT)
    )
    to_prepare = await session.scalars(
        select(Shipment)
        .where(Shipment.status == ShipmentStatus.PREPARING, Shipment.assignee_id == user.id)
        .order_by(Shipment.needed_by.asc().nulls_last(), Shipment.number)
        .limit(LIST_LIMIT)
    )
    awaiting = await session.scalars(
        select(Shipment)
        .where(
            Shipment.status.in_((ShipmentStatus.SHIPPED, ShipmentStatus.INCIDENT)),
            Shipment.shipped_at < utcnow() - DELIVERY_FOLLOW_UP,
        )
        .order_by(Shipment.shipped_at)
        .limit(LIST_LIMIT)
    )
    return LogisticsSummary(
        upcoming_events=await events_service.to_reads(session, list(events), user),
        to_prepare=await shipments_service.to_reads(session, list(to_prepare), user),
        awaiting_delivery=await shipments_service.to_reads(session, list(awaiting), user),
        low_stock=await _low_stock(session),
    )


async def get_summary(session: AsyncSession, user: User) -> HomeSummary:
    pending = Todo.is_done.is_(False)
    personal = await todos_service.list_todos(
        session, user, scope=Scope.PERSONAL, is_done=False, limit=LIST_LIMIT
    )
    company = await todos_service.list_todos(
        session, user, scope=Scope.COMPANY, is_done=False, limit=LIST_LIMIT
    )
    notes = await notes_service.list_notes(session, user, limit=NOTES_LIMIT)

    return HomeSummary(
        todos=TodoSummary(
            personal=[todos_service.to_read(t, user) for t in personal],
            company=[todos_service.to_read(t, user) for t in company],
            personal_pending=await _count(
                session, pending, Todo.scope == Scope.PERSONAL, Todo.created_by_id == user.id
            ),
            company_pending=await _count(session, pending, Todo.scope == Scope.COMPANY),
            assigned_to_me=await _count(
                session, pending, Todo.scope == Scope.COMPANY, Todo.assignee_id == user.id
            ),
            overdue=await _count(
                session,
                pending,
                Todo.due_date < local_today(),
                visible_to(Todo.scope, Todo.created_by_id, user),
            ),
        ),
        logistics=await _logistics(session, user),
        notes=[notes_service.to_read(n, user) for n in notes],
    )
