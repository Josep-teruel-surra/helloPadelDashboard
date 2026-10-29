import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Self

from pydantic import BaseModel, Field, model_validator

from app.modules.campuses.schemas import CampusSummary
from app.modules.events.schemas import EventRef
from app.modules.shipments.models import ShipmentStatus
from app.modules.users.schemas import UserSummary
from app.shared.address import Address
from app.shared.schemas import Currency, Markdown, OptionalHttpUrl, OptionalText80, OptionalText120

Cost = Annotated[Decimal, Field(ge=0, max_digits=10, decimal_places=2)]


class ItemIn(BaseModel):
    variant_id: uuid.UUID
    quantity: int = Field(ge=1, le=100_000)


Items = Annotated[list[ItemIn], Field(min_length=1, max_length=200)]


def _check_unique_variants(items: list[ItemIn]) -> None:
    ids = [item.variant_id for item in items]
    if len(ids) != len(set(ids)):
        raise ValueError("Hay variantes repetidas: suma las cantidades en una sola línea")


class ShipmentCreate(BaseModel):
    """Crear un envío es apartar su material. Con `event_id`, el campus y la fecha salen
    del evento si no se indican."""

    campus_id: uuid.UUID | None = None
    event_id: uuid.UUID | None = None
    items: Items
    assignee_id: uuid.UUID | None = None
    needed_by: date | None = None
    carrier: OptionalText80 = None
    tracking_number: OptionalText120 = None
    tracking_url: OptionalHttpUrl = None
    cost_amount: Cost | None = None
    cost_currency: Currency = "EUR"
    notes_md: Markdown = ""
    shipping_address: Address | None = Field(
        None, description="Por defecto, la dirección del campus"
    )

    @model_validator(mode="after")
    def _validate(self) -> Self:
        if self.campus_id is None and self.event_id is None:
            raise ValueError("Indica el campus o el evento del envío")
        _check_unique_variants(self.items)
        return self


class ItemsUpdate(BaseModel):
    items: Items

    @model_validator(mode="after")
    def _validate(self) -> Self:
        _check_unique_variants(self.items)
        return self


class ShipmentUpdate(BaseModel):
    """Datos editables en cualquier estado (el contenido va aparte, solo en preparación)."""

    assignee_id: uuid.UUID | None = None
    needed_by: date | None = None
    carrier: OptionalText80 = None
    tracking_number: OptionalText120 = None
    tracking_url: OptionalHttpUrl = None
    cost_amount: Cost | None = None
    cost_currency: Currency | None = None
    notes_md: Markdown | None = None
    shipping_address: Address | None = None

    @model_validator(mode="after")
    def _not_null(self) -> Self:
        for field in ("cost_currency", "notes_md"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"'{field}' no puede ser null")
        return self


class StatusChange(BaseModel):
    status: ShipmentStatus
    # Se suelen conocer justo al enviar.
    carrier: OptionalText80 = None
    tracking_number: OptionalText120 = None
    tracking_url: OptionalHttpUrl = None


class ShipmentItemRead(BaseModel):
    variant_id: uuid.UUID
    product_id: uuid.UUID
    product_name: str
    label: str
    quantity: int


class ShipmentRead(BaseModel):
    id: uuid.UUID
    number: int
    status: ShipmentStatus
    campus: CampusSummary
    event: EventRef | None
    items: list[ShipmentItemRead]
    total_units: int
    shipping_address: Address | None
    carrier: str | None
    tracking_number: str | None
    tracking_url: str | None
    needed_by: date | None
    shipped_at: datetime | None
    delivered_at: datetime | None
    assignee: UserSummary | None
    created_by: UserSummary
    cost_amount: Decimal | None
    cost_currency: str
    notes_md: str
    created_at: datetime
    updated_at: datetime
    can_delete: bool
    stock_warnings: list[str] = Field(
        description="Variantes de este envío en preparación sin stock suficiente"
    )


class SentMaterialRow(BaseModel):
    campus: CampusSummary
    product_id: uuid.UUID
    product_name: str
    variant_id: uuid.UUID
    label: str
    quantity: int
