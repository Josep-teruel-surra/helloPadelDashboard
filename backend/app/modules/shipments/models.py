import uuid
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Identity,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.modules.campuses.models import Campus
from app.modules.events.models import Event
from app.modules.inventory.models import ProductVariant
from app.modules.users.models import User
from app.shared.address import ShippingAddressMixin
from app.shared.models import Base, TimestampMixin, UUIDPrimaryKeyMixin, pg_enum


class ShipmentStatus(StrEnum):
    PREPARING = "preparing"  # material apartado, aún en la oficina
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    INCIDENT = "incident"
    CANCELLED = "cancelled"


# Estados en los que el material ya ha salido (cuenta como enviado al campus).
SENT_STATUSES = (ShipmentStatus.SHIPPED, ShipmentStatus.DELIVERED, ShipmentStatus.INCIDENT)


class Shipment(UUIDPrimaryKeyMixin, TimestampMixin, ShippingAddressMixin, Base):
    """Envío de material a un campus. En «preparing» su contenido cuenta como apartado.

    La dirección (`ship_*`) es una copia de la del campus al crearlo: el historial no cambia
    si luego se edita el campus.
    """

    __tablename__ = "shipments"
    __table_args__ = (
        CheckConstraint("cost_amount >= 0", name="cost_not_negative"),
        Index("ix_shipments_status", "status"),
        Index("ix_shipments_campus_id", "campus_id"),
        Index("ix_shipments_event_id", "event_id"),
    )

    # Número correlativo para hablar de «el envío #12».
    number: Mapped[int] = mapped_column(Identity(), unique=True)
    campus_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("campuses.id"))
    # RESTRICT: un evento con envíos no se borra (se cancela).
    event_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("events.id"))
    status: Mapped[ShipmentStatus] = mapped_column(
        pg_enum(ShipmentStatus, "shipment_status"), default=ShipmentStatus.PREPARING
    )

    carrier: Mapped[str | None] = mapped_column(String(80))
    tracking_number: Mapped[str | None] = mapped_column(String(120))
    tracking_url: Mapped[str | None] = mapped_column(String(500))

    needed_by: Mapped[date | None]
    shipped_at: Mapped[datetime | None]
    delivered_at: Mapped[datetime | None]

    assignee_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")
    )
    cost_amount: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    cost_currency: Mapped[str] = mapped_column(String(3), default="EUR", server_default="EUR")
    notes_md: Mapped[str] = mapped_column(Text, default="", server_default="")
    created_by_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))

    campus: Mapped[Campus] = relationship(lazy="joined")
    event: Mapped[Event | None] = relationship(lazy="joined")
    assignee: Mapped[User | None] = relationship(foreign_keys=[assignee_id], lazy="joined")
    created_by: Mapped[User] = relationship(foreign_keys=[created_by_id], lazy="joined")
    items: Mapped[list["ShipmentItem"]] = relationship(
        back_populates="shipment", cascade="all, delete-orphan", lazy="selectin"
    )


class ShipmentItem(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "shipment_items"
    __table_args__ = (
        UniqueConstraint("shipment_id", "variant_id", name="uq_shipment_items_shipment_variant"),
        CheckConstraint("quantity > 0", name="quantity_positive"),
        Index("ix_shipment_items_variant_id", "variant_id"),
    )

    shipment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("shipments.id", ondelete="CASCADE"))
    variant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("product_variants.id", ondelete="RESTRICT")
    )
    quantity: Mapped[int]

    shipment: Mapped[Shipment] = relationship(back_populates="items")
    variant: Mapped[ProductVariant] = relationship(lazy="joined")
