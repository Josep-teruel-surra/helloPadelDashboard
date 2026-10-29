import uuid
from typing import Annotated

from fastapi import APIRouter, Query, status

from app.core.deps import CurrentUser, SessionDep
from app.modules.notes import service
from app.modules.notes.schemas import NoteCreate, NoteRead, NoteUpdate
from app.shared.enums import Scope

router = APIRouter(prefix="/notes", tags=["notes"])


@router.get("", response_model=list[NoteRead])
async def list_notes(
    user: CurrentUser,
    session: SessionDep,
    scope: Scope | None = None,
    q: Annotated[
        str | None, Query(max_length=100, description="Busca en título y contenido")
    ] = None,
    event_id: uuid.UUID | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[NoteRead]:
    notes = await service.list_notes(
        session, user, scope=scope, q=q, event_id=event_id, limit=limit
    )
    return [service.to_read(note, user) for note in notes]


@router.post("", response_model=NoteRead, status_code=status.HTTP_201_CREATED)
async def create_note(data: NoteCreate, user: CurrentUser, session: SessionDep) -> NoteRead:
    note = await service.create_note(session, user, data)
    return service.to_read(note, user)


@router.get("/{note_id}", response_model=NoteRead)
async def read_note(note_id: uuid.UUID, user: CurrentUser, session: SessionDep) -> NoteRead:
    note = await service.get_visible(session, user, note_id)
    return service.to_read(note, user)


@router.patch("/{note_id}", response_model=NoteRead)
async def update_note(
    note_id: uuid.UUID, data: NoteUpdate, user: CurrentUser, session: SessionDep
) -> NoteRead:
    note = await service.get_visible(session, user, note_id)
    note = await service.update_note(session, user, note, data)
    return service.to_read(note, user)


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(note_id: uuid.UUID, user: CurrentUser, session: SessionDep) -> None:
    note = await service.get_visible(session, user, note_id)
    await service.delete_note(session, user, note)
