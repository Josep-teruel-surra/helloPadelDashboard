import uuid
from datetime import date, datetime

from sqlalchemy import CheckConstraint, ForeignKey, Index, String, Text, false
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.modules.users.models import User
from app.shared.enums import Scope
from app.shared.models import Base, TimestampMixin, UUIDPrimaryKeyMixin, pg_enum


class Todo(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "todos"
    __table_args__ = (
        CheckConstraint(
            "scope = 'company' OR assignee_id IS NULL", name="personal_without_assignee"
        ),
        Index("ix_todos_scope_is_done", "scope", "is_done"),
        Index("ix_todos_created_by_id_scope", "created_by_id", "scope"),
        Index("ix_todos_assignee_id", "assignee_id"),
    )

    scope: Mapped[Scope] = mapped_column(pg_enum(Scope, "scope"))
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    is_done: Mapped[bool] = mapped_column(default=False, server_default=false())
    completed_at: Mapped[datetime | None]
    due_date: Mapped[date | None]

    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    assignee_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )

    created_by: Mapped[User] = relationship(foreign_keys=[created_by_id], lazy="joined")
    assignee: Mapped[User | None] = relationship(foreign_keys=[assignee_id], lazy="joined")
