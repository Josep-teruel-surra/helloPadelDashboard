import uuid

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.modules.campuses.models import Campus
from app.shared.models import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Student(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Alumno que se examina (y, más adelante, que pide soporte de la plataforma)."""

    __tablename__ = "students"
    __table_args__ = (Index("ix_students_full_name", "full_name"),)

    full_name: Mapped[str] = mapped_column(String(160))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    country_code: Mapped[str | None] = mapped_column(String(2))
    # Sede o partner por el que viene, si lo hay.
    campus_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("campuses.id", ondelete="SET NULL")
    )
    notes_md: Mapped[str] = mapped_column(Text, default="", server_default="")

    campus: Mapped[Campus | None] = relationship(lazy="joined")
