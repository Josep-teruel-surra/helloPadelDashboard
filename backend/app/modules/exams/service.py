import uuid
from datetime import date, timedelta
from urllib.parse import urlparse

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import BadRequestError, ConflictError, ForbiddenError, NotFoundError
from app.core.security import local_today, utcnow
from app.modules.exams.models import (
    CLOSED_STATUSES,
    Certification,
    ExamKind,
    ExamSource,
    ExamStatus,
    ExamSubmission,
)
from app.modules.exams.schemas import (
    CertificationCreate,
    CertificationUpdate,
    CorrectionIn,
    SubmissionCreate,
    SubmissionRead,
    SubmissionUpdate,
)
from app.modules.students.models import Student
from app.modules.todos import service as todos_service
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
    if await has_submissions(session, certification_id=certification.id):
        raise ConflictError("La certificación tiene entregas: desactívala en lugar de borrarla")
    await session.delete(certification)
    await session.commit()


# --- Entregas ---

WETRANSFER_HOSTS = ("we.tl", "wetransfer.com")
LINK_WARNING_DAYS = 2

STATUS_LABELS = {
    ExamStatus.RECEIVED: "pendiente",
    ExamStatus.IN_REVIEW: "en corrección",
    ExamStatus.ON_HOLD: "en espera",
    ExamStatus.CORRECTED: "corregida",
    ExamStatus.NOTIFIED: "comunicada",
    ExamStatus.CANCELLED: "cancelada",
}

# «corrected» solo se alcanza con /correct, que exige el resultado.
TRANSITIONS: dict[ExamStatus, set[ExamStatus]] = {
    ExamStatus.RECEIVED: {ExamStatus.IN_REVIEW, ExamStatus.ON_HOLD, ExamStatus.CANCELLED},
    ExamStatus.IN_REVIEW: {ExamStatus.RECEIVED, ExamStatus.ON_HOLD, ExamStatus.CANCELLED},
    ExamStatus.ON_HOLD: {ExamStatus.RECEIVED, ExamStatus.IN_REVIEW, ExamStatus.CANCELLED},
    ExamStatus.CORRECTED: {ExamStatus.NOTIFIED, ExamStatus.IN_REVIEW},
    ExamStatus.NOTIFIED: {ExamStatus.IN_REVIEW},
    ExamStatus.CANCELLED: {ExamStatus.RECEIVED},
}
CORRECTABLE = {
    ExamStatus.RECEIVED,
    ExamStatus.IN_REVIEW,
    ExamStatus.ON_HOLD,
    ExamStatus.CORRECTED,
}


def is_wetransfer(url: str | None) -> bool:
    if not url:
        return False
    host = (urlparse(url).hostname or "").lower()
    return any(host == h or host.endswith(f".{h}") for h in WETRANSFER_HOSTS)


def _link_status(submission: ExamSubmission, today: date) -> str | None:
    if submission.saved_url:
        return "saved"
    if submission.link_expires_on is None or submission.status in CLOSED_STATUSES:
        return None
    days = (submission.link_expires_on - today).days
    if days < 0:
        return "expired"
    return "expiring" if days <= LINK_WARNING_DAYS else "ok"


async def _attempts(
    session: AsyncSession, submissions: list[ExamSubmission]
) -> dict[uuid.UUID, int]:
    """N.º de intento de cada entrega entre las de su alumno, certificación y tipo."""
    student_ids = {s.student_id for s in submissions}
    if not student_ids:
        return {}
    rows = await session.execute(
        select(
            ExamSubmission.id,
            ExamSubmission.student_id,
            ExamSubmission.certification_id,
            ExamSubmission.kind,
        )
        .where(ExamSubmission.student_id.in_(student_ids))
        .order_by(ExamSubmission.received_on, ExamSubmission.created_at)
    )
    counters: dict[tuple, int] = {}
    attempts: dict[uuid.UUID, int] = {}
    for submission_id, student_id, certification_id, kind in rows:
        key = (student_id, certification_id, kind)
        counters[key] = counters.get(key, 0) + 1
        attempts[submission_id] = counters[key]
    return attempts


async def to_reads(
    session: AsyncSession, submissions: list[ExamSubmission], user: User
) -> list[SubmissionRead]:
    attempts = await _attempts(session, submissions)
    today = local_today()
    return [
        SubmissionRead.model_validate(s).model_copy(
            update={
                "attempt": attempts.get(s.id, 1),
                "days_left": None
                if s.status in (*CLOSED_STATUSES, ExamStatus.CORRECTED)
                else (s.due_on - today).days,
                "link_status": _link_status(s, today),
                "can_delete": user.is_admin,
            }
        )
        for s in submissions
    ]


async def to_read(session: AsyncSession, submission: ExamSubmission, user: User) -> SubmissionRead:
    return (await to_reads(session, [submission], user))[0]


async def list_submissions(
    session: AsyncSession,
    user: User,
    *,
    status: ExamStatus | None = None,
    open_only: bool = False,
    kind: ExamKind | None = None,
    source: ExamSource | None = None,
    assigned_to_me: bool = False,
    student_id: uuid.UUID | None = None,
    certification_id: uuid.UUID | None = None,
    limit: int = 200,
) -> list[ExamSubmission]:
    query = select(ExamSubmission)
    if status:
        query = query.where(ExamSubmission.status == status)
    if open_only:
        query = query.where(ExamSubmission.status.not_in(CLOSED_STATUSES))
    if kind:
        query = query.where(ExamSubmission.kind == kind)
    if source:
        query = query.where(ExamSubmission.source == source)
    if assigned_to_me:
        query = query.where(ExamSubmission.assignee_id == user.id)
    if student_id:
        query = query.where(ExamSubmission.student_id == student_id)
    if certification_id:
        query = query.where(ExamSubmission.certification_id == certification_id)
    # Primero lo que está abierto, por plazo; después lo cerrado, lo más reciente antes.
    closed_last = case((ExamSubmission.status.in_(CLOSED_STATUSES), 1), else_=0)
    query = query.order_by(
        closed_last, ExamSubmission.due_on, ExamSubmission.received_on.desc()
    ).limit(limit)
    return list(await session.scalars(query))


async def get_submission(session: AsyncSession, submission_id: uuid.UUID) -> ExamSubmission:
    submission = await session.get(ExamSubmission, submission_id)
    if submission is None:
        raise NotFoundError("Entrega no encontrada")
    return submission


def _check_dates(received_on: date, due_on: date) -> None:
    if due_on < received_on:
        raise BadRequestError("La fecha límite no puede ser anterior a la de recepción")


async def create_submission(
    session: AsyncSession, user: User, data: SubmissionCreate
) -> ExamSubmission:
    if await session.get(Student, data.student_id) is None:
        raise BadRequestError("El alumno no existe")
    certification = await session.get(Certification, data.certification_id)
    if certification is None or not certification.is_active:
        raise BadRequestError("La certificación no existe o está desactivada")
    if (data.kind == ExamKind.TEST and not certification.has_test) or (
        data.kind == ExamKind.VIDEO and not certification.has_video
    ):
        raise BadRequestError(f"«{certification.name}» no tiene examen de ese tipo")
    if data.assignee_id:
        await todos_service.check_assignee(session, data.assignee_id)

    received_on = data.received_on or local_today()
    source = data.source or (
        ExamSource.WETRANSFER if is_wetransfer(data.link_url) else ExamSource.EXAMPORTAL
    )
    link_expires_on = data.link_expires_on
    if link_expires_on is None and source == ExamSource.WETRANSFER:
        link_expires_on = received_on + timedelta(days=settings.wetransfer_link_days)
    due_on = data.due_on or received_on + timedelta(days=settings.exam_correction_days)
    _check_dates(received_on, due_on)

    submission = ExamSubmission(
        **data.model_dump(exclude={"source", "link_expires_on", "received_on", "due_on"}),
        source=source,
        link_expires_on=link_expires_on,
        received_on=received_on,
        due_on=due_on,
        created_by_id=user.id,
    )
    session.add(submission)
    await session.commit()
    await session.refresh(submission)
    return submission


async def update_submission(
    session: AsyncSession, submission: ExamSubmission, data: SubmissionUpdate
) -> ExamSubmission:
    changes = data.model_dump(exclude_unset=True)
    if changes.get("assignee_id"):
        await todos_service.check_assignee(session, changes["assignee_id"])
    _check_dates(
        changes.get("received_on", submission.received_on),
        changes.get("due_on", submission.due_on),
    )
    if "saved_url" in changes:
        # Guardar fija la fecha la primera vez; quitar el enlace lo desmarca.
        if changes["saved_url"] and not submission.saved_url:
            submission.saved_at = utcnow()
        elif not changes["saved_url"]:
            submission.saved_at = None
    for field, value in changes.items():
        setattr(submission, field, value)
    await session.commit()
    await session.refresh(submission)
    return submission


async def correct_submission(
    session: AsyncSession, user: User, submission: ExamSubmission, data: CorrectionIn
) -> ExamSubmission:
    if submission.status not in CORRECTABLE:
        raise BadRequestError(
            f"Una entrega {STATUS_LABELS[submission.status]} no se puede corregir: reábrela antes"
        )
    submission.outcome = data.outcome
    submission.score = data.score
    submission.feedback_md = data.feedback_md
    submission.status = ExamStatus.CORRECTED
    submission.corrected_by_id = user.id
    submission.corrected_at = utcnow()
    await session.commit()
    await session.refresh(submission)
    return submission


async def change_status(
    session: AsyncSession, submission: ExamSubmission, new: ExamStatus
) -> ExamSubmission:
    old = submission.status
    if new not in TRANSITIONS[old]:
        raise BadRequestError(
            f"Una entrega {STATUS_LABELS[old]} no puede pasar a {STATUS_LABELS[new]}"
        )
    if new == ExamStatus.NOTIFIED:
        submission.notified_at = utcnow()
    elif old in (ExamStatus.CORRECTED, ExamStatus.NOTIFIED):
        # Reabrir: el resultado anterior se conserva como referencia hasta la nueva corrección.
        submission.notified_at = None
    submission.status = new
    await session.commit()
    await session.refresh(submission)
    return submission


async def delete_submission(session: AsyncSession, user: User, submission: ExamSubmission) -> None:
    if not user.is_admin:
        raise ForbiddenError("Solo un admin puede borrar entregas")
    await session.delete(submission)
    await session.commit()


async def has_submissions(session: AsyncSession, **filters: uuid.UUID) -> bool:
    query = select(ExamSubmission.id).limit(1)
    for column, value in filters.items():
        query = query.where(getattr(ExamSubmission, column) == value)
    return await session.scalar(query) is not None
