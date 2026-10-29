import uuid
from typing import Annotated

from fastapi import APIRouter, Query, status

from app.core.deps import CurrentUser, SessionDep
from app.modules.events import service
from app.modules.events.models import EventStatus
from app.modules.events.schemas import EventCreate, EventRead, EventUpdate

router = APIRouter(prefix="/events", tags=["events"])


@router.get("", response_model=list[EventRead])
async def list_events(
    user: CurrentUser,
    session: SessionDep,
    campus_id: uuid.UUID | None = None,
    status: EventStatus | None = None,
    when: service.When = "upcoming",
    limit: Annotated[int, Query(ge=1, le=500)] = 200,
) -> list[EventRead]:
    events = await service.list_events(
        session, campus_id=campus_id, status=status, when=when, limit=limit
    )
    return await service.to_reads(session, events, user)


@router.post("", response_model=EventRead, status_code=status.HTTP_201_CREATED)
async def create_event(data: EventCreate, user: CurrentUser, session: SessionDep) -> EventRead:
    event = await service.create_event(session, user, data)
    return await service.to_read(session, event, user)


@router.get("/{event_id}", response_model=EventRead)
async def read_event(event_id: uuid.UUID, user: CurrentUser, session: SessionDep) -> EventRead:
    event = await service.get_event(session, event_id)
    return await service.to_read(session, event, user)


@router.patch("/{event_id}", response_model=EventRead)
async def update_event(
    event_id: uuid.UUID, data: EventUpdate, user: CurrentUser, session: SessionDep
) -> EventRead:
    event = await service.get_event(session, event_id)
    event = await service.update_event(session, event, data)
    return await service.to_read(session, event, user)


@router.delete("/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(event_id: uuid.UUID, user: CurrentUser, session: SessionDep) -> None:
    event = await service.get_event(session, event_id)
    await service.delete_event(session, user, event)
