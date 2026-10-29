import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.modules.users.models import User
from app.shared.enums import Scope
from app.shared.models import Base, TimestampMixin, UUIDPrimaryKeyMixin, pg_enum

if TYPE_CHECKING:
    from app.modules.events.models import Event


class Note(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "notes"
    __table_args__ = (
        Index("ix_notes_scope_updated_at", "scope", "updated_at"),
        Index("ix_notes_author_id_scope", "author_id", "scope"),
        Index("ix_notes_event_id", "event_id"),
    )

    scope: Mapped[Scope] = mapped_column(pg_enum(Scope, "scope"))
    title: Mapped[str] = mapped_column(String(200))
    content_md: Mapped[str] = mapped_column(Text, default="", server_default="")
    author_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    event_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("events.id", ondelete="SET NULL"))

    author: Mapped[User] = relationship(lazy="joined")
    event: Mapped["Event | None"] = relationship("Event", lazy="joined")
