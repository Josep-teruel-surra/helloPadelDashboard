from sqlalchemy import ColumnElement, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import local_today
from app.modules.home.schemas import HomeSummary, TodoSummary
from app.modules.notes import service as notes_service
from app.modules.todos import service as todos_service
from app.modules.todos.models import Todo
from app.modules.users.models import User
from app.shared.enums import Scope
from app.shared.permissions import visible_to

LIST_LIMIT = 5
NOTES_LIMIT = 4


async def _count(session: AsyncSession, *conditions: ColumnElement[bool]) -> int:
    query = select(func.count()).select_from(Todo).where(*conditions)
    return await session.scalar(query) or 0


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
        notes=[notes_service.to_read(n, user) for n in notes],
    )
