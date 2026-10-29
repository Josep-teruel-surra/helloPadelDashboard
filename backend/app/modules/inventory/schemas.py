import uuid
from datetime import datetime
from typing import Annotated, Literal, Self

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    StringConstraints,
    model_validator,
)

from app.modules.inventory.models import ProductCategory, StockMovementKind
from app.modules.users.schemas import UserSummary
from app.shared.schemas import blank_to_none

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]
Label = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=60)]
Sku = Annotated[Annotated[str, Field(max_length=60)] | None, BeforeValidator(blank_to_none)]
Description = Annotated[
    Annotated[str, Field(max_length=5000)] | None, BeforeValidator(blank_to_none)
]
Note = Annotated[Annotated[str, Field(max_length=500)] | None, BeforeValidator(blank_to_none)]
Threshold = Annotated[int, Field(ge=0, le=1_000_000)]


def _ensure_not_null(model: BaseModel, nullable: set[str]) -> None:
    for field in model.model_fields_set - nullable:
        if getattr(model, field) is None:
            raise ValueError(f"'{field}' no puede ser null")


# --- Variantes ---


class VariantCreate(BaseModel):
    label: Label
    sku: Sku = None
    low_stock_threshold: Threshold | None = None
    initial_stock: int = Field(0, ge=0, le=1_000_000, description="Se registra como entrada")


class VariantUpdate(BaseModel):
    label: Label | None = None
    sku: Sku = None
    low_stock_threshold: Threshold | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def _not_null(self) -> Self:
        _ensure_not_null(self, {"sku", "low_stock_threshold"})
        return self


class VariantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    label: str
    sku: str | None
    low_stock_threshold: int | None
    is_active: bool
    on_hand: int = Field(0, description="Unidades en almacén (suma de movimientos)")
    low_stock: bool = Field(False, description="Por debajo o igual al umbral de aviso")


# --- Productos ---


class ProductCreate(BaseModel):
    name: Name
    category: ProductCategory
    description: Description = None
    variants: list[VariantCreate] = Field(min_length=1, max_length=50)

    @model_validator(mode="after")
    def _unique_labels(self) -> Self:
        labels = [v.label.lower() for v in self.variants]
        if len(labels) != len(set(labels)):
            raise ValueError("Hay variantes repetidas")
        return self


class ProductUpdate(BaseModel):
    name: Name | None = None
    category: ProductCategory | None = None
    description: Description = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def _not_null(self) -> Self:
        _ensure_not_null(self, {"description"})
        return self


class ProductRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    category: ProductCategory
    description: str | None
    is_active: bool
    variants: list[VariantRead]
    total_on_hand: int = 0
    created_at: datetime
    updated_at: datetime


# --- Movimientos ---


class MovementCreate(BaseModel):
    """Movimientos manuales. Las salidas por envío las genera el módulo de envíos."""

    variant_id: uuid.UUID
    kind: Literal[StockMovementKind.RESTOCK, StockMovementKind.RETURN, StockMovementKind.ADJUSTMENT]
    quantity: int = Field(ge=-1_000_000, le=1_000_000)
    note: Note = None

    @model_validator(mode="after")
    def _sign_matches_kind(self) -> Self:
        if self.quantity == 0:
            raise ValueError("La cantidad no puede ser 0")
        if self.kind != StockMovementKind.ADJUSTMENT and self.quantity < 0:
            raise ValueError("Las entradas y devoluciones deben ser positivas")
        return self


class VariantRef(BaseModel):
    id: uuid.UUID
    label: str
    product_id: uuid.UUID
    product_name: str


class MovementRead(BaseModel):
    id: uuid.UUID
    kind: StockMovementKind
    quantity: int
    note: str | None
    variant: VariantRef
    created_by: UserSummary
    created_at: datetime
