import uuid
from typing import Annotated

from fastapi import APIRouter, Query, status

from app.core.deps import CurrentUser, SessionDep
from app.modules.todos import service
from app.modules.todos.schemas import TodoCreate, TodoRead, TodoUpdate
from app.shared.enums import Scope

router = APIRouter(prefix="/todos", tags=["todos"])


@router.get("", response_model=list[TodoRead])
async def list_todos(
    user: CurrentUser,
    session: SessionDep,
    scope: Scope | None = None,
    is_done: bool | None = None,
    assigned_to_me: bool = False,
    limit: Annotated[int, Query(ge=1, le=500)] = 200,
) -> list[TodoRead]:
    todos = await service.list_todos(
        session, user, scope=scope, is_done=is_done, assigned_to_me=assigned_to_me, limit=limit
    )
    return [service.to_read(todo, user) for todo in todos]


@router.post("", response_model=TodoRead, status_code=status.HTTP_201_CREATED)
async def create_todo(data: TodoCreate, user: CurrentUser, session: SessionDep) -> TodoRead:
    todo = await service.create_todo(session, user, data)
    return service.to_read(todo, user)


@router.get("/{todo_id}", response_model=TodoRead)
async def read_todo(todo_id: uuid.UUID, user: CurrentUser, session: SessionDep) -> TodoRead:
    todo = await service.get_visible(session, user, todo_id)
    return service.to_read(todo, user)


@router.patch("/{todo_id}", response_model=TodoRead)
async def update_todo(
    todo_id: uuid.UUID, data: TodoUpdate, user: CurrentUser, session: SessionDep
) -> TodoRead:
    todo = await service.get_visible(session, user, todo_id)
    todo = await service.update_todo(session, user, todo, data)
    return service.to_read(todo, user)


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(todo_id: uuid.UUID, user: CurrentUser, session: SessionDep) -> None:
    todo = await service.get_visible(session, user, todo_id)
    await service.delete_todo(session, user, todo)
