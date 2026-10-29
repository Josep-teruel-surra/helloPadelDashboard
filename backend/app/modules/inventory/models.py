import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.security import utcnow
from app.modules.users.models import User
from app.shared.models import Base, TimestampMixin, UUIDPrimaryKeyMixin, pg_enum


class ProductCategory(StrEnum):
    CLOTHING = "clothing"
    BOOK = "book"
    OTHER = "other"


class StockMovementKind(StrEnum):
    RESTOCK = "restock"  # entra material (compra, reposición)
    SHIPMENT = "shipment"  # sale en un envío (lo crea el módulo de envíos)
    ADJUSTMENT = "adjustment"  # corrección manual (inventario, roturas…)
    RETURN = "return"  # vuelve material (envío cancelado, sobrante de un campus)


class Product(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Material que se envía a los campus: camisetas, libros…"""

    __tablename__ = "products"

    name: Mapped[str] = mapped_column(String(160), unique=True)
    category: Mapped[ProductCategory] = mapped_column(pg_enum(ProductCategory, "product_category"))
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(default=True, server_default=true())

    variants: Mapped[list["ProductVariant"]] = relationship(
        back_populates="product",
        order_by="ProductVariant.position",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ProductVariant(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    """Lo que se cuenta en stock: una talla de camiseta, un idioma de un libro…"""

    __tablename__ = "product_variants"
    __table_args__ = (
        UniqueConstraint("product_id", "label", name="uq_product_variants_product_id_label"),
        CheckConstraint("low_stock_threshold >= 0", name="threshold_not_negative"),
    )

    product_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    label: Mapped[str] = mapped_column(String(60))
    sku: Mapped[str | None] = mapped_column(String(60), unique=True)
    # Orden de presentación (XS, S, M… en el orden en que se crearon).
    position: Mapped[int] = mapped_column(default=0, server_default="0")
    low_stock_threshold: Mapped[int | None]
    is_active: Mapped[bool] = mapped_column(default=True, server_default=true())

    product: Mapped[Product] = relationship(back_populates="variants", lazy="joined")


class StockMovement(UUIDPrimaryKeyMixin, Base):
    """Cada entrada o salida de material. El stock de una variante es la suma de sus movimientos."""

    __tablename__ = "stock_movements"
    __table_args__ = (
        CheckConstraint("quantity <> 0", name="quantity_not_zero"),
        CheckConstraint(
            "(kind IN ('restock', 'return') AND quantity > 0)"
            " OR (kind = 'shipment' AND quantity < 0)"
            " OR kind = 'adjustment'",
            name="quantity_sign_matches_kind",
        ),
        Index("ix_stock_movements_variant_id_created_at", "variant_id", "created_at"),
    )

    # RESTRICT: una variante con historial no se puede borrar, solo desactivar.
    variant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("product_variants.id", ondelete="RESTRICT")
    )
    kind: Mapped[StockMovementKind] = mapped_column(
        pg_enum(StockMovementKind, "stock_movement_kind")
    )
    quantity: Mapped[int]
    note: Mapped[str | None] = mapped_column(String(500))
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(default=utcnow, server_default=func.now())

    variant: Mapped[ProductVariant] = relationship(lazy="joined")
    created_by: Mapped[User] = relationship(lazy="joined")
