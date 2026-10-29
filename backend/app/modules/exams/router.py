import uuid

from fastapi import APIRouter, status

from app.core.deps import CurrentUser, SessionDep
from app.modules.exams import service
from app.modules.exams.schemas import CertificationCreate, CertificationRead, CertificationUpdate

router = APIRouter(tags=["exams"])

# --- Certificaciones: las ve todo el equipo, las gestiona un admin ---


@router.get("/certifications", response_model=list[CertificationRead])
async def list_certifications(
    _: CurrentUser, session: SessionDep, include_inactive: bool = False
) -> object:
    return await service.list_certifications(session, include_inactive=include_inactive)


@router.post(
    "/certifications", response_model=CertificationRead, status_code=status.HTTP_201_CREATED
)
async def create_certification(
    data: CertificationCreate, user: CurrentUser, session: SessionDep
) -> object:
    return await service.create_certification(session, user, data)


@router.patch("/certifications/{certification_id}", response_model=CertificationRead)
async def update_certification(
    certification_id: uuid.UUID, data: CertificationUpdate, user: CurrentUser, session: SessionDep
) -> object:
    certification = await service.get_certification(session, certification_id)
    return await service.update_certification(session, user, certification, data)


@router.delete("/certifications/{certification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_certification(
    certification_id: uuid.UUID, user: CurrentUser, session: SessionDep
) -> None:
    certification = await service.get_certification(session, certification_id)
    await service.delete_certification(session, user, certification)
