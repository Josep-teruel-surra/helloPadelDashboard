import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.modules.exams.models import ExamKind, ExamOutcome, ExamSource, ExamStatus
from app.modules.students.schemas import StudentSummary
from app.modules.users.schemas import UserSummary
from app.shared.schemas import Markdown, OptionalHttpUrl

CertificationName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)
]


class CertificationCreate(BaseModel):
    name: CertificationName
    has_test: bool = True
    has_video: bool = True

    @model_validator(mode="after")
    def _some_part(self) -> Self:
        if not (self.has_test or self.has_video):
            raise ValueError("La certificación debe tener test, vídeo o ambos")
        return self


class CertificationUpdate(BaseModel):
    name: CertificationName | None = None
    has_test: bool | None = None
    has_video: bool | None = None
    position: int | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def _not_null(self) -> Self:
        for field in self.model_fields_set:
            if getattr(self, field) is None:
                raise ValueError(f"'{field}' no puede ser null")
        return self


class CertificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    has_test: bool
    has_video: bool
    position: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class CertificationSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str


# --- Entregas ---

Score = Annotated[Decimal, Field(ge=0, le=10, max_digits=4, decimal_places=2)]


class SubmissionCreate(BaseModel):
    """Plazos opcionales: por defecto se calculan desde la fecha de recepción."""

    student_id: uuid.UUID
    certification_id: uuid.UUID
    kind: ExamKind
    source: ExamSource | None = Field(
        None, description="Si falta: WeTransfer si el enlace lo es, si no examportal"
    )
    link_url: OptionalHttpUrl = None
    link_expires_on: date | None = None
    received_on: date | None = Field(None, description="Por defecto, hoy")
    due_on: date | None = None
    assignee_id: uuid.UUID | None = None


class SubmissionUpdate(BaseModel):
    source: ExamSource | None = None
    link_url: OptionalHttpUrl = None
    link_expires_on: date | None = None
    saved_url: OptionalHttpUrl = Field(None, description="Al indicarlo se marca como guardado")
    received_on: date | None = None
    due_on: date | None = None
    assignee_id: uuid.UUID | None = None

    @model_validator(mode="after")
    def _not_null(self) -> Self:
        for field in ("source", "received_on", "due_on"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"'{field}' no puede ser null")
        return self


class CorrectionIn(BaseModel):
    outcome: ExamOutcome
    score: Score | None = None
    feedback_md: Markdown = ""


class StatusChangeIn(BaseModel):
    """Cambios de estado salvo «corrected», que va por /correct con el resultado."""

    status: Literal[
        ExamStatus.RECEIVED,
        ExamStatus.IN_REVIEW,
        ExamStatus.ON_HOLD,
        ExamStatus.NOTIFIED,
        ExamStatus.CANCELLED,
    ]


LinkStatus = Literal["ok", "expiring", "expired", "saved"]


class SubmissionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    student: StudentSummary
    certification: CertificationSummary
    kind: ExamKind
    source: ExamSource
    link_url: str | None
    link_expires_on: date | None
    saved_url: str | None
    saved_at: datetime | None
    received_on: date
    due_on: date
    status: ExamStatus
    assignee: UserSummary | None
    outcome: ExamOutcome | None
    score: Decimal | None
    feedback_md: str
    corrected_by: UserSummary | None
    corrected_at: datetime | None
    notified_at: datetime | None
    created_by: UserSummary
    created_at: datetime
    updated_at: datetime
    attempt: int = Field(1, description="Intento n.º para este alumno, certificación y tipo")
    days_left: int | None = Field(
        None, description="Días hasta la fecha límite (negativo si se pasó); null si está cerrada"
    )
    link_status: LinkStatus | None = Field(
        None,
        description="Estado del enlace: expiring (≤2 días), expired, saved; null si no caduca",
    )
    can_delete: bool = False
