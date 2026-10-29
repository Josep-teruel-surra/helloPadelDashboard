import uuid
from typing import Annotated

from fastapi import APIRouter, Query, status

from app.core.deps import CurrentUser, SessionDep
from app.modules.campuses import service
from app.modules.campuses.schemas import CampusCreate, CampusRead, CampusUpdate

router = APIRouter(prefix="/campuses", tags=["campuses"])

# Los campus son de empresa: cualquiera del equipo los consulta y los mantiene.
# No se borran (tienen historial de eventos y envíos): se desactivan con is_active=false.


@router.get("", response_model=list[CampusRead])
async def list_campuses(
    _: CurrentUser,
    session: SessionDep,
    include_inactive: bool = False,
    q: Annotated[str | None, Query(max_length=100)] = None,
) -> list[CampusRead]:
    campuses = await service.list_campuses(session, include_inactive=include_inactive, q=q)
    return [CampusRead.from_model(c) for c in campuses]


@router.post("", response_model=CampusRead, status_code=status.HTTP_201_CREATED)
async def create_campus(data: CampusCreate, _: CurrentUser, session: SessionDep) -> CampusRead:
    return CampusRead.from_model(await service.create_campus(session, data))


@router.get("/{campus_id}", response_model=CampusRead)
async def read_campus(campus_id: uuid.UUID, _: CurrentUser, session: SessionDep) -> CampusRead:
    return CampusRead.from_model(await service.get_campus(session, campus_id))


@router.patch("/{campus_id}", response_model=CampusRead)
async def update_campus(
    campus_id: uuid.UUID, data: CampusUpdate, _: CurrentUser, session: SessionDep
) -> CampusRead:
    campus = await service.get_campus(session, campus_id)
    return CampusRead.from_model(await service.update_campus(session, campus, data))
