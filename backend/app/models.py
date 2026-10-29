"""Registro de todos los modelos para Alembic y los tests. Añade aquí los de cada módulo nuevo."""

from app.modules.auth.models import RefreshToken
from app.modules.users.models import User
from app.shared.models import Base

__all__ = ["Base", "RefreshToken", "User"]
