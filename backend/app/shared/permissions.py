"""Reglas de visibilidad comunes a los recursos con ámbito personal/empresa."""

from sqlalchemy import ColumnElement, or_
from sqlalchemy.orm import InstrumentedAttribute

from app.modules.users.models import User
from app.shared.enums import Scope


def visible_to(
    scope_col: InstrumentedAttribute[Scope],
    owner_col: InstrumentedAttribute,
    user: User,
) -> ColumnElement[bool]:
    """Filtro SQL: lo de empresa lo ve todo el mundo; lo personal, solo su dueño (ni un admin)."""
    return or_(scope_col == Scope.COMPANY, owner_col == user.id)


def is_visible(scope: Scope, owner_id: object, user: User) -> bool:
    return scope == Scope.COMPANY or owner_id == user.id
