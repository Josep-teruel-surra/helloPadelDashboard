import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ConflictError, NotFoundError
from app.modules.campuses.models import Campus
from app.modules.campuses.schemas import CampusCreate, CampusUpdate
from app.shared.address import Address

NAME_TAKEN = "Ya existe un campus con ese nombre"


async def list_campuses(
    session: AsyncSession, *, include_inactive: bool = False, q: str | None = None
) -> list[Campus]:
    query = select(Campus).order_by(Campus.country_code, Campus.name)
    if not include_inactive:
        query = query.where(Campus.is_active.is_(True))
    if q:
        query = query.where(
            or_(
                Campus.name.icontains(q, autoescape=True),
                Campus.city.icontains(q, autoescape=True),
                Campus.partner.icontains(q, autoescape=True),
            )
        )
    return list(await session.scalars(query))


async def get_campus(session: AsyncSession, campus_id: uuid.UUID) -> Campus:
    campus = await session.get(Campus, campus_id)
    if campus is None:
        raise NotFoundError("Campus no encontrado")
    return campus


async def _check_name_free(session: AsyncSession, name: str, exclude: uuid.UUID | None = None):
    query = select(Campus.id).where(func.lower(Campus.name) == name.lower())
    if exclude:
        query = query.where(Campus.id != exclude)
    if await session.scalar(query):
        raise ConflictError(NAME_TAKEN)


async def create_campus(session: AsyncSession, data: CampusCreate) -> Campus:
    await _check_name_free(session, data.name)
    campus = Campus(**data.model_dump(exclude={"shipping_address"}))
    Address.apply_to(campus, data.shipping_address)
    session.add(campus)
    await session.commit()
    return campus


async def update_campus(session: AsyncSession, campus: Campus, data: CampusUpdate) -> Campus:
    changes = data.model_dump(exclude_unset=True, exclude={"shipping_address"})
    if "name" in changes:
        await _check_name_free(session, changes["name"], exclude=campus.id)
    for field, value in changes.items():
        setattr(campus, field, value)
    if "shipping_address" in data.model_fields_set:
        Address.apply_to(campus, data.shipping_address)
    await session.commit()
    return campus
