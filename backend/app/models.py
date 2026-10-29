"""Registro de todos los modelos para Alembic y los tests. Añade aquí los de cada módulo nuevo."""

from app.modules.auth.models import RefreshToken
from app.modules.campuses.models import Campus
from app.modules.events.models import Event
from app.modules.inventory.models import Product, ProductVariant, StockMovement
from app.modules.notes.models import Note
from app.modules.shipments.models import Shipment, ShipmentItem
from app.modules.todos.models import Todo
from app.modules.users.models import User
from app.shared.models import Base

__all__ = [
    "Base",
    "Campus",
    "Event",
    "Note",
    "Product",
    "ProductVariant",
    "RefreshToken",
    "Shipment",
    "ShipmentItem",
    "StockMovement",
    "Todo",
    "User",
]
