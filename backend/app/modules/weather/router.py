from typing import Annotated, Self

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field, model_validator

from app.core.deps import CurrentUser
from app.modules.weather import service
from app.modules.weather.schemas import WeatherRead

router = APIRouter(prefix="/weather", tags=["weather"])


class WeatherQuery(BaseModel):
    lat: float | None = Field(None, ge=-90, le=90)
    lon: float | None = Field(None, ge=-180, le=180)

    @model_validator(mode="after")
    def _both_or_neither(self) -> Self:
        if (self.lat is None) != (self.lon is None):
            raise ValueError(
                "Indica lat y lon a la vez, o ninguno para usar la ubicación por defecto"
            )
        return self


@router.get("", response_model=WeatherRead)
async def read_weather(_: CurrentUser, query: Annotated[WeatherQuery, Query()]) -> WeatherRead:
    """Tiempo actual y previsión. Sin coordenadas, usa la ubicación por defecto (Barcelona)."""
    return await service.get_weather(query.lat, query.lon)
