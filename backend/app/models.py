"""Registro de todos los modelos para Alembic y los tests. Añade aquí los de cada módulo nuevo."""

from app.modules.auth.models import RefreshToken
from app.modules.notes.models import Note
from app.modules.todos.models import Todo
from app.modules.users.models import User
from app.shared.models import Base

__all__ = ["Base", "Note", "RefreshToken", "Todo", "User"]
