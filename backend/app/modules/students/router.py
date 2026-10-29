import uuid
from typing import Annotated

from fastapi import APIRouter, Query, status

from app.core.deps import CurrentUser, SessionDep
from app.modules.students import service
from app.modules.students.schemas import StudentCreate, StudentRead, StudentUpdate

# Alumnos: todo el equipo los consulta y los da de alta; borrar, solo admin.
router = APIRouter(prefix="/students", tags=["students"])


@router.get("", response_model=list[StudentRead])
async def list_students(
    _: CurrentUser,
    session: SessionDep,
    q: Annotated[str | None, Query(max_length=100, description="Nombre o email")] = None,
    campus_id: uuid.UUID | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> object:
    return await service.list_students(session, q=q, campus_id=campus_id, limit=limit)


@router.post("", response_model=StudentRead, status_code=status.HTTP_201_CREATED)
async def create_student(data: StudentCreate, _: CurrentUser, session: SessionDep) -> object:
    return await service.create_student(session, data)


@router.get("/{student_id}", response_model=StudentRead)
async def read_student(student_id: uuid.UUID, _: CurrentUser, session: SessionDep) -> object:
    return await service.get_student(session, student_id)


@router.patch("/{student_id}", response_model=StudentRead)
async def update_student(
    student_id: uuid.UUID, data: StudentUpdate, _: CurrentUser, session: SessionDep
) -> object:
    student = await service.get_student(session, student_id)
    return await service.update_student(session, student, data)


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_student(student_id: uuid.UUID, user: CurrentUser, session: SessionDep) -> None:
    await service.delete_student(session, user, await service.get_student(session, student_id))
