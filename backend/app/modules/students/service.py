import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from app.modules.campuses.models import Campus
from app.modules.students.models import Student
from app.modules.students.schemas import StudentCreate, StudentUpdate
from app.modules.users.models import User

EMAIL_TAKEN = "Ya hay un alumno con ese email"


async def list_students(
    session: AsyncSession,
    *,
    q: str | None = None,
    campus_id: uuid.UUID | None = None,
    limit: int = 100,
) -> list[Student]:
    query = select(Student).order_by(Student.full_name).limit(limit)
    if q:
        query = query.where(
            or_(
                Student.full_name.icontains(q, autoescape=True),
                Student.email.icontains(q, autoescape=True),
            )
        )
    if campus_id:
        query = query.where(Student.campus_id == campus_id)
    return list(await session.scalars(query))


async def get_student(session: AsyncSession, student_id: uuid.UUID) -> Student:
    student = await session.get(Student, student_id)
    if student is None:
        raise NotFoundError("Alumno no encontrado")
    return student


async def _check_email_free(
    session: AsyncSession, email: str, exclude: uuid.UUID | None = None
) -> None:
    query = select(Student.id).where(func.lower(Student.email) == email.lower())
    if exclude:
        query = query.where(Student.id != exclude)
    if await session.scalar(query):
        raise ConflictError(EMAIL_TAKEN)


async def _check_campus(session: AsyncSession, campus_id: uuid.UUID) -> None:
    if await session.get(Campus, campus_id) is None:
        raise BadRequestError("La sede no existe")


async def create_student(session: AsyncSession, data: StudentCreate) -> Student:
    await _check_email_free(session, data.email)
    if data.campus_id:
        await _check_campus(session, data.campus_id)
    student = Student(**data.model_dump())
    session.add(student)
    await session.commit()
    await session.refresh(student, ["campus"])
    return student


async def update_student(session: AsyncSession, student: Student, data: StudentUpdate) -> Student:
    changes = data.model_dump(exclude_unset=True)
    if "email" in changes:
        await _check_email_free(session, changes["email"], exclude=student.id)
    if changes.get("campus_id"):
        await _check_campus(session, changes["campus_id"])
    for field, value in changes.items():
        setattr(student, field, value)
    await session.commit()
    await session.refresh(student, ["campus"])
    return student


async def delete_student(session: AsyncSession, user: User, student: Student) -> None:
    if not user.is_admin:
        raise ForbiddenError("Solo un admin puede borrar alumnos")
    await session.delete(student)
    await session.commit()
