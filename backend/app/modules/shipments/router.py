import uuid
from typing import Annotated

from fastapi import APIRouter, Query, status

from app.core.deps import CurrentUser, SessionDep
from app.modules.shipments import service
from app.modules.shipments.models import ShipmentStatus
from app.modules.shipments.schemas import (
    ItemsUpdate,
    SentMaterialRow,
    ShipmentCreate,
    ShipmentRead,
    ShipmentUpdate,
    StatusChange,
)

# Envíos de empresa: todo el equipo los crea y gestiona. Borrar solo en preparación
# (quien lo creó o un admin); después se cancelan para no perder el historial.
router = APIRouter(prefix="/shipments", tags=["shipments"])


@router.get("", response_model=list[ShipmentRead])
async def list_shipments(
    user: CurrentUser,
    session: SessionDep,
    status: ShipmentStatus | None = None,
    campus_id: uuid.UUID | None = None,
    event_id: uuid.UUID | None = None,
    assigned_to_me: bool = False,
    limit: Annotated[int, Query(ge=1, le=500)] = 200,
) -> list[ShipmentRead]:
    shipments = await service.list_shipments(
        session,
        user,
        status=status,
        campus_id=campus_id,
        event_id=event_id,
        assigned_to_me=assigned_to_me,
        limit=limit,
    )
    return await service.to_reads(session, shipments, user)


@router.get("/sent-material", response_model=list[SentMaterialRow])
async def sent_material(
    _: CurrentUser,
    session: SessionDep,
    campus_id: uuid.UUID | None = None,
    year: Annotated[int | None, Query(ge=2000, le=2100)] = None,
) -> list[SentMaterialRow]:
    """Cuánto material ha recibido cada campus (opcionalmente, en un año)."""
    return await service.sent_material(session, campus_id=campus_id, year=year)


@router.post("", response_model=ShipmentRead, status_code=status.HTTP_201_CREATED)
async def create_shipment(
    data: ShipmentCreate, user: CurrentUser, session: SessionDep
) -> ShipmentRead:
    shipment = await service.create_shipment(session, user, data)
    return await service.to_read(session, shipment, user)


@router.get("/{shipment_id}", response_model=ShipmentRead)
async def read_shipment(
    shipment_id: uuid.UUID, user: CurrentUser, session: SessionDep
) -> ShipmentRead:
    shipment = await service.get_shipment(session, shipment_id)
    return await service.to_read(session, shipment, user)


@router.patch("/{shipment_id}", response_model=ShipmentRead)
async def update_shipment(
    shipment_id: uuid.UUID, data: ShipmentUpdate, user: CurrentUser, session: SessionDep
) -> ShipmentRead:
    shipment = await service.get_shipment(session, shipment_id)
    shipment = await service.update_shipment(session, shipment, data)
    return await service.to_read(session, shipment, user)


@router.put("/{shipment_id}/items", response_model=ShipmentRead)
async def replace_items(
    shipment_id: uuid.UUID, data: ItemsUpdate, user: CurrentUser, session: SessionDep
) -> ShipmentRead:
    shipment = await service.get_shipment(session, shipment_id)
    shipment = await service.replace_items(session, shipment, data.items)
    return await service.to_read(session, shipment, user)


@router.post("/{shipment_id}/status", response_model=ShipmentRead)
async def change_status(
    shipment_id: uuid.UUID, data: StatusChange, user: CurrentUser, session: SessionDep
) -> ShipmentRead:
    shipment = await service.get_shipment(session, shipment_id)
    shipment = await service.change_status(session, user, shipment, data)
    return await service.to_read(session, shipment, user)


@router.delete("/{shipment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_shipment(shipment_id: uuid.UUID, user: CurrentUser, session: SessionDep) -> None:
    shipment = await service.get_shipment(session, shipment_id)
    await service.delete_shipment(session, user, shipment)
