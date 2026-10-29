from sqlalchemy import CheckConstraint, String, true
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.models import Base, TimestampMixin, UUIDPrimaryKeyMixin


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
