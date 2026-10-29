import uuid
from datetime import date
from enum import StrEnum

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.modules.campuses.models import Campus
from app.modules.users.models import User
from app.shared.models import Base, TimestampMixin, UUIDPrimaryKeyMixin, pg_enum


class EventKind(StrEnum):
    CAMPUS = "campus"
    COACH_TRAINING = "coach_training"
    EXAM = "exam"
    OTHER = "other"


class EventStatus(StrEnum):
    PLANNED = "planned"
    CONFIRMED = "confirmed"
    DONE = "done"
    CANCELLED = "cancelled"


class Event(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Algo que pasa en un campus en unas fechas: un campus, una formación, un examen…"""

    __tablename__ = "events"
    __table_args__ = (
        CheckConstraint("end_date >= start_date", name="dates_in_order"),
        CheckConstraint("expected_participants >= 0", name="participants_not_negative"),
        Index("ix_events_start_date", "start_date"),
        Index("ix_events_campus_id_start_date", "campus_id", "start_date"),
    )

    campus_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("campuses.id"))
    title: Mapped[str] = mapped_column(String(200))
    kind: Mapped[EventKind] = mapped_column(pg_enum(EventKind, "event_kind"))
    status: Mapped[EventStatus] = mapped_column(
        pg_enum(EventStatus, "event_status"), default=EventStatus.PLANNED
    )
    start_date: Mapped[date]
    end_date: Mapped[date]
    responsible_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    expected_participants: Mapped[int | None]
    notes_md: Mapped[str] = mapped_column(Text, default="", server_default="")
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    # Tarea automática "Apartar material para…". use_alter: todos.event_id apunta aquí también.
    material_todo_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("todos.id", ondelete="SET NULL", use_alter=True)
    )

    campus: Mapped[Campus] = relationship(lazy="joined")
    responsible: Mapped[User | None] = relationship(foreign_keys=[responsible_id], lazy="joined")
    created_by: Mapped[User] = relationship(foreign_keys=[created_by_id], lazy="joined")
