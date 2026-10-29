import uuid

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ForbiddenError, NotFoundError
from app.modules.notes.models import Note
from app.modules.notes.schemas import NoteCreate, NoteRead, NoteUpdate
from app.modules.users.models import User
from app.shared.enums import Scope
from app.shared.permissions import is_visible, visible_to

NOT_FOUND = "Nota no encontrada"


def can_edit(user: User, note: Note) -> bool:
    """Editar y borrar: el autor; en las de empresa, también un admin."""
    if note.author_id == user.id:
        return True
    return note.scope == Scope.COMPANY and user.is_admin


def to_read(note: Note, user: User) -> NoteRead:
    return NoteRead.model_validate(note).model_copy(update={"can_edit": can_edit(user, note)})


async def list_notes(
    session: AsyncSession,
    user: User,
    *,
    scope: Scope | None = None,
    q: str | None = None,
    limit: int = 100,
) -> list[Note]:
    query = select(Note).where(visible_to(Note.scope, Note.author_id, user))
    if scope is not None:
        query = query.where(Note.scope == scope)
    if q:
        query = query.where(
            or_(
                Note.title.icontains(q, autoescape=True),
                Note.content_md.icontains(q, autoescape=True),
            )
        )
    query = query.order_by(Note.updated_at.desc()).limit(limit)
    return list(await session.scalars(query))


async def get_visible(session: AsyncSession, user: User, note_id: uuid.UUID) -> Note:
    note = await session.get(Note, note_id)
    # 404 también para lo personal ajeno: no revelamos que existe.
    if note is None or not is_visible(note.scope, note.author_id, user):
        raise NotFoundError(NOT_FOUND)
    return note


async def create_note(session: AsyncSession, user: User, data: NoteCreate) -> Note:
    note = Note(**data.model_dump(), author_id=user.id)
    session.add(note)
    await session.commit()
    await session.refresh(note, ["author"])
    return note


async def update_note(session: AsyncSession, user: User, note: Note, data: NoteUpdate) -> Note:
    if not can_edit(user, note):
        raise ForbiddenError("Solo el autor o un admin pueden editar esta nota")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(note, field, value)
    await session.commit()
    return note


async def delete_note(session: AsyncSession, user: User, note: Note) -> None:
    if not can_edit(user, note):
        raise ForbiddenError("Solo el autor o un admin pueden borrar esta nota")
    await session.delete(note)
    await session.commit()
