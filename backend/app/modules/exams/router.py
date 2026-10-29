import uuid
from typing import Annotated

from fastapi import APIRouter, Query, status

from app.core.deps import CurrentUser, SessionDep
from app.modules.exams import service
from app.modules.exams.models import ExamKind, ExamSource, ExamStatus
from app.modules.exams.schemas import (
    CertificationCreate,
    CertificationRead,
    CertificationUpdate,
    CorrectionIn,
    StatusChangeIn,
    SubmissionCreate,
    SubmissionRead,
    SubmissionUpdate,
)

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


# --- Entregas de examen: el equipo las registra, se las reparte y las corrige ---


@router.get("/exams", response_model=list[SubmissionRead])
async def list_submissions(
    user: CurrentUser,
    session: SessionDep,
    status: ExamStatus | None = None,
    open_only: Annotated[bool, Query(description="Sin las comunicadas ni canceladas")] = False,
    kind: ExamKind | None = None,
    source: ExamSource | None = None,
    assigned_to_me: bool = False,
    student_id: uuid.UUID | None = None,
    certification_id: uuid.UUID | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 200,
) -> list[SubmissionRead]:
    submissions = await service.list_submissions(
        session,
        user,
        status=status,
        open_only=open_only,
        kind=kind,
        source=source,
        assigned_to_me=assigned_to_me,
        student_id=student_id,
        certification_id=certification_id,
        limit=limit,
    )
    return await service.to_reads(session, submissions, user)


@router.post("/exams", response_model=SubmissionRead, status_code=status.HTTP_201_CREATED)
async def create_submission(
    data: SubmissionCreate, user: CurrentUser, session: SessionDep
) -> SubmissionRead:
    submission = await service.create_submission(session, user, data)
    return await service.to_read(session, submission, user)


@router.get("/exams/{submission_id}", response_model=SubmissionRead)
async def read_submission(
    submission_id: uuid.UUID, user: CurrentUser, session: SessionDep
) -> SubmissionRead:
    submission = await service.get_submission(session, submission_id)
    return await service.to_read(session, submission, user)


@router.patch("/exams/{submission_id}", response_model=SubmissionRead)
async def update_submission(
    submission_id: uuid.UUID, data: SubmissionUpdate, user: CurrentUser, session: SessionDep
) -> SubmissionRead:
    submission = await service.get_submission(session, submission_id)
    submission = await service.update_submission(session, submission, data)
    return await service.to_read(session, submission, user)


@router.post("/exams/{submission_id}/correct", response_model=SubmissionRead)
async def correct_submission(
    submission_id: uuid.UUID, data: CorrectionIn, user: CurrentUser, session: SessionDep
) -> SubmissionRead:
    submission = await service.get_submission(session, submission_id)
    submission = await service.correct_submission(session, user, submission, data)
    return await service.to_read(session, submission, user)


@router.post("/exams/{submission_id}/status", response_model=SubmissionRead)
async def change_status(
    submission_id: uuid.UUID, data: StatusChangeIn, user: CurrentUser, session: SessionDep
) -> SubmissionRead:
    submission = await service.get_submission(session, submission_id)
    submission = await service.change_status(session, submission, data.status)
    return await service.to_read(session, submission, user)


@router.delete("/exams/{submission_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_submission(
    submission_id: uuid.UUID, user: CurrentUser, session: SessionDep
) -> None:
    submission = await service.get_submission(session, submission_id)
    await service.delete_submission(session, user, submission)
