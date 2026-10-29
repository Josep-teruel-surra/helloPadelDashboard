import uuid
from datetime import datetime
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, StringConstraints, model_validator

from app.modules.campuses.models import Campus
from app.shared.address import Address
from app.shared.schemas import (
    CountryCode,
    Markdown,
    OptionalEmail,
    OptionalShortText,
    OptionalText120,
    OptionalText160,
)

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]


class CampusCreate(BaseModel):
    name: Name
    country_code: CountryCode
    city: Name
    partner: OptionalText160 = None
    coordinator_name: OptionalText120 = None
    coordinator_email: OptionalEmail = None
    coordinator_phone: OptionalShortText = None
    shipping_address: Address | None = None
    notes_md: Markdown = ""


class CampusUpdate(BaseModel):
    """Campos opcionales. `shipping_address` sustituye la dirección entera (null la borra)."""

    name: Name | None = None
    country_code: CountryCode | None = None
    city: Name | None = None
    partner: OptionalText160 = None
    coordinator_name: OptionalText120 = None
    coordinator_email: OptionalEmail = None
    coordinator_phone: OptionalShortText = None
    shipping_address: Address | None = None
    notes_md: Markdown | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def _required_fields_not_null(self) -> Self:
        for field in ("name", "country_code", "city", "notes_md", "is_active"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"'{field}' no puede ser null")
        return self


class CampusSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    country_code: str
    city: str


class CampusRead(CampusSummary):
    partner: str | None
    coordinator_name: str | None
    coordinator_email: str | None
    coordinator_phone: str | None
    shipping_address: Address | None
    notes_md: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, campus: Campus) -> Self:
        data = {
            field: getattr(campus, field)
            for field in cls.model_fields
            if field != "shipping_address"
        }
        return cls(**data, shipping_address=Address.from_model(campus))
