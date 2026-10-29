import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import CheckConstraint, ForeignKey, Index, Numeric, String, Text, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.modules.students.models import Student
from app.modules.users.models import User
from app.shared.models import Base, TimestampMixin, UUIDPrimaryKeyMixin, pg_enum


class Certification(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Lo que se examina (p. ej. «Bronze 1») y de qué partes consta."""

    __tablename__ = "certifications"
    __table_args__ = (CheckConstraint("has_test OR has_video", name="has_some_part"),)

    name: Mapped[str] = mapped_column(String(80), unique=True)
    has_test: Mapped[bool] = mapped_column(default=True, server_default=true())
    has_video: Mapped[bool] = mapped_column(default=True, server_default=true())
    # Orden de presentación (Bronze 1, Bronze 2…).
    position: Mapped[int] = mapped_column(default=0, server_default="0")
    is_active: Mapped[bool] = mapped_column(default=True, server_default=true())


class ExamKind(StrEnum):
    TEST = "test"
    VIDEO = "video"


class ExamSource(StrEnum):
    EXAMPORTAL = "examportal"
    WETRANSFER = "wetransfer"
    EMAIL = "email"
    OTHER = "other"


class ExamStatus(StrEnum):
    RECEIVED = "received"  # pendiente de corregir
    IN_REVIEW = "in_review"
    ON_HOLD = "on_hold"  # falta algo del alumno (vídeo que no se ve…)
    CORRECTED = "corrected"
    NOTIFIED = "notified"  # resultado comunicado al alumno
    CANCELLED = "cancelled"


# Estados en los que la entrega ya no está pendiente de trabajo.
CLOSED_STATUSES = (ExamStatus.NOTIFIED, ExamStatus.CANCELLED)


class ExamOutcome(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    RESUBMIT = "resubmit"


class ExamSubmission(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Un examen (test o vídeo) que ha enviado un alumno y hay que corregir."""

    __tablename__ = "exam_submissions"
    __table_args__ = (
        CheckConstraint("score >= 0 AND score <= 10", name="score_in_range"),
        CheckConstraint("due_on >= received_on", name="due_after_received"),
        Index("ix_exam_submissions_status_due_on", "status", "due_on"),
        Index("ix_exam_submissions_assignee_id", "assignee_id"),
        Index("ix_exam_submissions_student_id", "student_id"),
    )

    # RESTRICT: alumnos y certificaciones con entregas no se borran.
    student_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("students.id"))
    certification_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("certifications.id"))
    kind: Mapped[ExamKind] = mapped_column(pg_enum(ExamKind, "exam_kind"))
    source: Mapped[ExamSource] = mapped_column(pg_enum(ExamSource, "exam_source"))

    link_url: Mapped[str | None] = mapped_column(String(1000))
    link_expires_on: Mapped[date | None]
    # Dónde se ha guardado el material (p. ej. Drive). Guardado, el enlace ya puede caducar.
    saved_url: Mapped[str | None] = mapped_column(String(1000))
    saved_at: Mapped[datetime | None]

    received_on: Mapped[date]
    due_on: Mapped[date]
    status: Mapped[ExamStatus] = mapped_column(
        pg_enum(ExamStatus, "exam_status"), default=ExamStatus.RECEIVED
    )
    assignee_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )

    outcome: Mapped[ExamOutcome | None] = mapped_column(pg_enum(ExamOutcome, "exam_outcome"))
    score: Mapped[Decimal | None] = mapped_column(Numeric(4, 2))
    feedback_md: Mapped[str] = mapped_column(Text, default="", server_default="")
    corrected_by_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    corrected_at: Mapped[datetime | None]
    notified_at: Mapped[datetime | None]
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))

    student: Mapped[Student] = relationship(lazy="joined")
    certification: Mapped[Certification] = relationship(lazy="joined")
    assignee: Mapped[User | None] = relationship(foreign_keys=[assignee_id], lazy="joined")
    corrected_by: Mapped[User | None] = relationship(foreign_keys=[corrected_by_id], lazy="joined")
    created_by: Mapped[User] = relationship(foreign_keys=[created_by_id], lazy="joined")
