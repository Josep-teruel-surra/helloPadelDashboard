"""Dirección postal: columnas reutilizables (campus, envíos) y su schema anidado en la API."""

from typing import Any, Self

from pydantic import BaseModel
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.schemas import (
    OptionalCountryCode,
    OptionalText120,
    OptionalText160,
    OptionalText200,
)

ADDRESS_FIELDS = ("recipient", "line1", "line2", "postal_code", "city", "region", "country_code")


class ShippingAddressMixin:
    """Columnas `ship_*` de una dirección de envío."""

    ship_recipient: Mapped[str | None] = mapped_column(String(160))
    ship_line1: Mapped[str | None] = mapped_column(String(200))
    ship_line2: Mapped[str | None] = mapped_column(String(200))
    ship_postal_code: Mapped[str | None] = mapped_column(String(20))
    ship_city: Mapped[str | None] = mapped_column(String(120))
    ship_region: Mapped[str | None] = mapped_column(String(120))
    ship_country_code: Mapped[str | None] = mapped_column(String(2))


class Address(BaseModel):
    recipient: OptionalText160 = None
    line1: OptionalText200 = None
    line2: OptionalText200 = None
    postal_code: OptionalText120 = None
    city: OptionalText120 = None
    region: OptionalText120 = None
    country_code: OptionalCountryCode = None

    @classmethod
    def from_model(cls, obj: Any) -> Self | None:
        values = {field: getattr(obj, f"ship_{field}") for field in ADDRESS_FIELDS}
        return cls(**values) if any(values.values()) else None

    @staticmethod
    def apply_to(obj: Any, address: "Address | None") -> None:
        """Sustituye la dirección completa del objeto (None la vacía)."""
        for field in ADDRESS_FIELDS:
            setattr(obj, f"ship_{field}", getattr(address, field) if address else None)
