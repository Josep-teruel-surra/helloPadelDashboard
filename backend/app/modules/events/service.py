import uuid
from datetime import date, timedelta
from typing import Literal

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BadRequestError, ForbiddenError, NotFoundError
from app.core.security import local_today
from app.modules.campuses.models import Campus
from app.modules.events.models import Event, EventStatus
from app.modules.events.schemas import EventCreate, EventRead, EventUpdate, MaterialTask
from app.modules.todos import service as todos_service
from app.modules.todos.models import Todo
from app.modules.users.models import User
from app.shared.enums import Scope

When = Literal["upcoming", "past", "all"]

# La tarea automática de material vence este tiempo antes de que empiece el evento.
MATERIAL_LEAD_TIME = timedelta(weeks=3)


def material_task_title(event_title: str) -> str:
    return f"Apartar material para «{event_title}»"


def material_task_due(start_date: date) -> date:
    return max(local_today(), start_date - MATERIAL_LEAD_TIME)


def can_delete(user: User, event: Event) -> bool:
    return user.is_admin or event.created_by_id == user.id


async def to_reads(session: AsyncSession, events: list[Event], user: User) -> list[EventRead]:
    todo_ids = [e.material_todo_id for e in events if e.material_todo_id]
    todos = {}
    if todo_ids:
        todos = {t.id: t for t in await session.scalars(select(Todo).where(Todo.id.in_(todo_ids)))}
    reads = []
    for event in events:
        todo = todos.get(event.material_todo_id) if event.material_todo_id else None
        reads.append(
            EventRead.model_validate(event).model_copy(
                update={
                    "material_task": MaterialTask.model_validate(todo) if todo else None,
                    "can_delete": can_delete(user, event),
                }
            )
        )
    return reads


async def to_read(session: AsyncSession, event: Event, user: User) -> EventRead:
    return (await to_reads(session, [event], user))[0]


async def list_events(
    session: AsyncSession,
    *,
    campus_id: uuid.UUID | None = None,
    status: EventStatus | None = None,
    when: When = "upcoming",
    limit: int = 200,
) -> list[Event]:
    query = select(Event)
    if campus_id:
        query = query.where(Event.campus_id == campus_id)
    if status:
        query = query.where(Event.status == status)
    today = local_today()
    if when == "upcoming":
        query = query.where(Event.end_date >= today).order_by(Event.start_date.asc())
    elif when == "past":
        query = query.where(Event.end_date < today).order_by(Event.start_date.desc())
    else:
        query = query.order_by(Event.start_date.desc())
    return list(await session.scalars(query.limit(limit)))


async def get_event(session: AsyncSession, event_id: uuid.UUID) -> Event:
    event = await session.get(Event, event_id)
    if event is None:
        raise NotFoundError("Evento no encontrado")
    return event


async def _check_campus(session: AsyncSession, campus_id: uuid.UUID) -> None:
    campus = await session.get(Campus, campus_id)
    if campus is None or not campus.is_active:
        raise BadRequestError("El campus no existe o está desactivado")


async def _check_responsible(session: AsyncSession, user_id: uuid.UUID) -> None:
    await todos_service.check_assignee(
        session, user_id, message="El responsable no existe o está inactivo"
    )


async def create_event(session: AsyncSession, user: User, data: EventCreate) -> Event:
    await _check_campus(session, data.campus_id)
    if data.responsible_id:
        await _check_responsible(session, data.responsible_id)

    event = Event(**data.model_dump(), created_by_id=user.id)
    session.add(event)
    await session.flush()

    # Cada evento nace con su tarea de empresa para apartar el material.
    todo = Todo(
        scope=Scope.COMPANY,
        title=material_task_title(event.title),
        description="Tarea creada automáticamente con el evento.",
        due_date=material_task_due(event.start_date),
        assignee_id=event.responsible_id,
        created_by_id=user.id,
        event_id=event.id,
    )
    session.add(todo)
    await session.flush()
    event.material_todo_id = todo.id

    await session.commit()
    return event


async def update_event(session: AsyncSession, event: Event, data: EventUpdate) -> Event:
    changes = data.model_dump(exclude_unset=True)

    if "campus_id" in changes and changes["campus_id"] != event.campus_id:
        await _check_campus(session, changes["campus_id"])
    if changes.get("responsible_id"):
        await _check_responsible(session, changes["responsible_id"])

    start = changes.get("start_date", event.start_date)
    end = changes.get("end_date", event.end_date)
    if end < start:
        raise BadRequestError("La fecha de fin no puede ser anterior a la de inicio")

    old_title = event.title
    for field, value in changes.items():
        setattr(event, field, value)

    # Mantiene la tarea de material al día mientras siga pendiente.
    todo = await session.get(Todo, event.material_todo_id) if event.material_todo_id else None
    if todo and not todo.is_done:
        if "start_date" in changes:
            todo.due_date = material_task_due(event.start_date)
        if "responsible_id" in changes:
            todo.assignee_id = event.responsible_id
        if "title" in changes and todo.title == material_task_title(old_title):
            todo.title = material_task_title(event.title)

    await session.commit()
    await session.refresh(event, ["campus", "responsible"])
    return event


async def delete_event(session: AsyncSession, user: User, event: Event) -> None:
    if not can_delete(user, event):
        raise ForbiddenError("Solo quien creó el evento o un admin pueden borrarlo")
    material_todo_id = event.material_todo_id
    await session.delete(event)
    await session.flush()
    # La tarea automática pendiente ya no tiene sentido; las demás quedan sin evento.
    if material_todo_id:
        await session.execute(
            delete(Todo).where(Todo.id == material_todo_id, Todo.is_done.is_(False))
        )
    await session.commit()
