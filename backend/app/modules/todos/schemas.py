import uuid
from datetime import date, datetime
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.modules.users.schemas import UserSummary
from app.shared.enums import Scope

Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Description = Annotated[str, Field(max_length=5000)]


class TodoCreate(BaseModel):
    scope: Scope = Scope.PERSONAL
    title: Title
    description: Description | None = None
    due_date: date | None = None
    assignee_id: uuid.UUID | None = None

    @model_validator(mode="after")
    def _personal_cannot_be_assigned(self) -> Self:
        if self.scope == Scope.PERSONAL and self.assignee_id is not None:
            raise ValueError("Las tareas personales no se pueden asignar")
        return self


class TodoUpdate(BaseModel):
    """Campos opcionales; `null` en due_date/assignee_id/description los vacía."""

    title: Title | None = None
    description: Description | None = None
    due_date: date | None = None
    assignee_id: uuid.UUID | None = None
    is_done: bool | None = None

    @model_validator(mode="after")
    def _required_fields_not_null(self) -> Self:
        for field in ("title", "is_done"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"'{field}' no puede ser null")
        return self


class TodoRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    scope: Scope
    title: str
    description: str | None
    is_done: bool
    completed_at: datetime | None
    due_date: date | None
    created_by: UserSummary
    assignee: UserSummary | None
    created_at: datetime
    updated_at: datetime
    can_edit: bool = Field(
        default=False, description="Si el usuario actual puede editar o borrar la tarea"
    )
