import uuid
from datetime import datetime
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.modules.users.schemas import UserSummary
from app.shared.enums import Scope

Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Content = Annotated[str, Field(max_length=100_000)]


class NoteCreate(BaseModel):
    scope: Scope = Scope.PERSONAL
    title: Title
    content_md: Content = ""


class NoteUpdate(BaseModel):
    """El ámbito no se cambia: una nota personal no pasa a ser de empresa ni al revés."""

    title: Title | None = None
    content_md: Content | None = None

    @model_validator(mode="after")
    def _fields_not_null(self) -> Self:
        for field in self.model_fields_set:
            if getattr(self, field) is None:
                raise ValueError(f"'{field}' no puede ser null")
        return self


class NoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    scope: Scope
    title: str
    content_md: str
    author: UserSummary
    created_at: datetime
    updated_at: datetime
    can_edit: bool = Field(
        default=False, description="Si el usuario actual puede editar o borrar la nota"
    )
