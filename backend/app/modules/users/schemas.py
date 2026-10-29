import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.modules.users.models import UserRole
from app.shared.schemas import Email, FullName, Password


class UserCreate(BaseModel):
    email: Email
    full_name: FullName
    password: Password
    role: UserRole = UserRole.WORKER


class UserUpdate(BaseModel):
    """Edición por parte de un admin. `password` resetea la contraseña."""

    email: Email | None = None
    full_name: FullName | None = None
    role: UserRole | None = None
    is_active: bool | None = None
    password: Password | None = None


class PasswordChange(BaseModel):
    current_password: str
    new_password: Password


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    full_name: str
    role: UserRole
    is_active: bool
    last_login_at: datetime | None
    created_at: datetime
