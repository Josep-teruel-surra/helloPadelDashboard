import uuid
from datetime import date, datetime
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.modules.campuses.schemas import CampusSummary
from app.modules.events.models import EventKind, EventStatus
from app.modules.users.schemas import UserSummary
from app.shared.schemas import Markdown

Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=200)]
Participants = Annotated[int, Field(ge=0, le=100_000)]


class EventCreate(BaseModel):
    campus_id: uuid.UUID
    title: Title
    kind: EventKind = EventKind.CAMPUS
    status: EventStatus = EventStatus.PLANNED
    start_date: date
    end_date: date | None = Field(None, description="Por defecto, el mismo día de inicio")
    responsible_id: uuid.UUID | None = None
    expected_participants: Participants | None = None
    notes_md: Markdown = ""

    @model_validator(mode="after")
    def _dates_in_order(self) -> Self:
        if self.end_date is None:
            self.end_date = self.start_date
        if self.end_date < self.start_date:
            raise ValueError("La fecha de fin no puede ser anterior a la de inicio")
        return self


class EventUpdate(BaseModel):
    """Campos opcionales; el orden de fechas se valida contra los valores ya guardados."""

    campus_id: uuid.UUID | None = None
    title: Title | None = None
    kind: EventKind | None = None
    status: EventStatus | None = None
    start_date: date | None = None
    end_date: date | None = None
    responsible_id: uuid.UUID | None = None
    expected_participants: Participants | None = None
    notes_md: Markdown | None = None

    @model_validator(mode="after")
    def _required_fields_not_null(self) -> Self:
        nullable = {"responsible_id", "expected_participants"}
        for field in self.model_fields_set - nullable:
            if getattr(self, field) is None:
                raise ValueError(f"'{field}' no puede ser null")
        return self


class EventRef(BaseModel):
    """Referencia ligera a un evento dentro de tareas y notas."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    start_date: date


class MaterialTask(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    is_done: bool
    due_date: date | None
    assignee: UserSummary | None


class EventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    campus: CampusSummary
    title: str
    kind: EventKind
    status: EventStatus
    start_date: date
    end_date: date
    responsible: UserSummary | None
    expected_participants: int | None
    notes_md: str
    created_by: UserSummary
    material_task: MaterialTask | None = None
    created_at: datetime
    updated_at: datetime
    can_delete: bool = Field(default=False, description="Solo quien lo creó o un admin")
