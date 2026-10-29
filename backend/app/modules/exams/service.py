import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from app.modules.exams.models import Certification
from app.modules.exams.schemas import CertificationCreate, CertificationUpdate
from app.modules.users.models import User


def _require_admin(user: User) -> None:
    if not user.is_admin:
        raise ForbiddenError("Solo un admin puede gestionar las certificaciones")


async def list_certifications(
    session: AsyncSession, *, include_inactive: bool = False
) -> list[Certification]:
    query = select(Certification).order_by(Certification.position, Certification.name)
    if not include_inactive:
        query = query.where(Certification.is_active.is_(True))
    return list(await session.scalars(query))


async def get_certification(session: AsyncSession, certification_id: uuid.UUID) -> Certification:
    certification = await session.get(Certification, certification_id)
    if certification is None:
        raise NotFoundError("Certificación no encontrada")
    return certification


async def _check_name_free(
    session: AsyncSession, name: str, exclude: uuid.UUID | None = None
) -> None:
    query = select(Certification.id).where(func.lower(Certification.name) == name.lower())
    if exclude:
        query = query.where(Certification.id != exclude)
    if await session.scalar(query):
        raise ConflictError("Ya existe una certificación con ese nombre")


async def create_certification(
    session: AsyncSession, user: User, data: CertificationCreate
) -> Certification:
    _require_admin(user)
    await _check_name_free(session, data.name)
    last = await session.scalar(select(func.max(Certification.position)))
    certification = Certification(**data.model_dump(), position=(last or 0) + 1)
    session.add(certification)
    await session.commit()
    return certification


async def update_certification(
    session: AsyncSession, user: User, certification: Certification, data: CertificationUpdate
) -> Certification:
    _require_admin(user)
    changes = data.model_dump(exclude_unset=True)
    if "name" in changes:
        await _check_name_free(session, changes["name"], exclude=certification.id)
    has_test = changes.get("has_test", certification.has_test)
    has_video = changes.get("has_video", certification.has_video)
    if not (has_test or has_video):
        raise BadRequestError("La certificación debe tener test, vídeo o ambos")
    for field, value in changes.items():
        setattr(certification, field, value)
    await session.commit()
    return certification


async def delete_certification(
    session: AsyncSession, user: User, certification: Certification
) -> None:
    _require_admin(user)
    await session.delete(certification)
    await session.commit()
