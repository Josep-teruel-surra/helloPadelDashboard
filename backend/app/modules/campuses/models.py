from sqlalchemy import Index, String, Text, true
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.address import ShippingAddressMixin
from app.shared.models import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Campus(UUIDPrimaryKeyMixin, TimestampMixin, ShippingAddressMixin, Base):
    """Sede de la academia en un país (normalmente con un partner local)."""

    __tablename__ = "campuses"
    __table_args__ = (Index("ix_campuses_country_code", "country_code"),)

    name: Mapped[str] = mapped_column(String(120), unique=True)
    country_code: Mapped[str] = mapped_column(String(2))
    city: Mapped[str] = mapped_column(String(120))
    partner: Mapped[str | None] = mapped_column(String(160))

    coordinator_name: Mapped[str | None] = mapped_column(String(120))
    coordinator_email: Mapped[str | None] = mapped_column(String(255))
    coordinator_phone: Mapped[str | None] = mapped_column(String(40))

    notes_md: Mapped[str] = mapped_column(Text, default="", server_default="")
    is_active: Mapped[bool] = mapped_column(default=True, server_default=true())
