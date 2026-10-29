import uuid
from datetime import datetime
from typing import Annotated, Self

from pydantic import BaseModel, ConfigDict, StringConstraints, model_validator

CertificationName = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)
]


class CertificationCreate(BaseModel):
    name: CertificationName
    has_test: bool = True
    has_video: bool = True

    @model_validator(mode="after")
    def _some_part(self) -> Self:
        if not (self.has_test or self.has_video):
            raise ValueError("La certificación debe tener test, vídeo o ambos")
        return self


class CertificationUpdate(BaseModel):
    name: CertificationName | None = None
    has_test: bool | None = None
    has_video: bool | None = None
    position: int | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def _not_null(self) -> Self:
        for field in self.model_fields_set:
            if getattr(self, field) is None:
                raise ValueError(f"'{field}' no puede ser null")
        return self


class CertificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    has_test: bool
    has_video: bool
    position: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
