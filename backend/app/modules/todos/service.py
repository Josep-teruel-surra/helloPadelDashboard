import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BadRequestError, ForbiddenError, NotFoundError
from app.core.security import utcnow
from app.modules.todos.models import Todo
from app.modules.todos.schemas import TodoCreate, TodoRead, TodoUpdate
from app.modules.users.models import User
from app.shared.enums import Scope
from app.shared.permissions import is_visible, visible_to

NOT_FOUND = "Tarea no encontrada"


def can_edit(user: User, todo: Todo) -> bool:
    """Editar y borrar: lo personal, su dueño; lo de empresa, creador, asignado o admin."""
    if todo.scope == Scope.PERSONAL:
        return todo.created_by_id == user.id
    return user.is_admin or user.id in (todo.created_by_id, todo.assignee_id)


def to_read(todo: Todo, user: User) -> TodoRead:
    return TodoRead.model_validate(todo).model_copy(update={"can_edit": can_edit(user, todo)})


async def list_todos(
    session: AsyncSession,
    user: User,
    *,
    scope: Scope | None = None,
    is_done: bool | None = None,
    assigned_to_me: bool = False,
    limit: int = 200,
) -> list[Todo]:
    query = select(Todo).where(visible_to(Todo.scope, Todo.created_by_id, user))
    if scope is not None:
        query = query.where(Todo.scope == scope)
    if is_done is not None:
        query = query.where(Todo.is_done.is_(is_done))
    if assigned_to_me:
        query = query.where(Todo.assignee_id == user.id)
    query = query.order_by(
        Todo.is_done.asc(), Todo.due_date.asc().nulls_last(), Todo.created_at.desc()
    ).limit(limit)
    return list(await session.scalars(query))


async def get_visible(session: AsyncSession, user: User, todo_id: uuid.UUID) -> Todo:
    todo = await session.get(Todo, todo_id)
    # 404 también para lo personal ajeno: no revelamos que existe.
    if todo is None or not is_visible(todo.scope, todo.created_by_id, user):
        raise NotFoundError(NOT_FOUND)
    return todo


async def _check_assignee(session: AsyncSession, assignee_id: uuid.UUID) -> None:
    assignee = await session.get(User, assignee_id)
    if assignee is None or not assignee.is_active:
        raise BadRequestError("La persona asignada no existe o está inactiva")


async def create_todo(session: AsyncSession, user: User, data: TodoCreate) -> Todo:
    if data.assignee_id is not None:
        await _check_assignee(session, data.assignee_id)
    todo = Todo(**data.model_dump(), created_by_id=user.id)
    session.add(todo)
    await session.commit()
    await session.refresh(todo, ["created_by", "assignee"])
    return todo


async def update_todo(session: AsyncSession, user: User, todo: Todo, data: TodoUpdate) -> Todo:
    changes = data.model_dump(exclude_unset=True)

    # Marcar o desmarcar como hecha lo puede cualquiera que vea la tarea.
    if set(changes) - {"is_done"} and not can_edit(user, todo):
        raise ForbiddenError("Solo el creador, la persona asignada o un admin pueden editarla")

    if "assignee_id" in changes:
        if changes["assignee_id"] is not None:
            if todo.scope == Scope.PERSONAL:
                raise BadRequestError("Las tareas personales no se pueden asignar")
            await _check_assignee(session, changes["assignee_id"])

    if "is_done" in changes and changes["is_done"] != todo.is_done:
        todo.completed_at = utcnow() if changes["is_done"] else None

    for field, value in changes.items():
        setattr(todo, field, value)

    await session.commit()
    await session.refresh(todo, ["created_by", "assignee"])
    return todo


async def delete_todo(session: AsyncSession, user: User, todo: Todo) -> None:
    if not can_edit(user, todo):
        raise ForbiddenError("Solo el creador, la persona asignada o un admin pueden borrarla")
    await session.delete(todo)
    await session.commit()
