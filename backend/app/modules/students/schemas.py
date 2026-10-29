import uuid
from datetime import datetime
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, StringConstraints, model_validator

from app.modules.campuses.schemas import CampusSummary
from app.shared.schemas import Email, Markdown, OptionalCountryCode

Name = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=160)]


class StudentCreate(BaseModel):
    full_name: Name
    email: Email
    country_code: OptionalCountryCode = None
    campus_id: uuid.UUID | None = None
    notes_md: Markdown = ""


class StudentUpdate(BaseModel):
    full_name: Name | None = None
    email: Email | None = None
    country_code: OptionalCountryCode = None
    campus_id: uuid.UUID | None = None
    notes_md: Markdown | None = None

    @model_validator(mode="after")
    def _not_null(self) -> Self:
        for field in ("full_name", "email", "notes_md"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"'{field}' no puede ser null")
        return self


class StudentSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    full_name: str
    email: str
    country_code: str | None


class StudentRead(StudentSummary):
    campus: CampusSummary | None
    notes_md: str
    created_at: datetime
    updated_at: datetime
