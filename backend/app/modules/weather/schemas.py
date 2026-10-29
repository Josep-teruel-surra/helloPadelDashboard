from datetime import date, datetime

from pydantic import BaseModel, Field


class Location(BaseModel):
    latitude: float
    longitude: float
    name: str | None = Field(description="Solo se conoce para la ubicación por defecto")
    is_default: bool
    timezone: str


class Condition(BaseModel):
    weather_code: int
    description: str
    icon: str = Field(description="clear, partly-cloudy, cloudy, fog, drizzle, rain, snow o storm")


class CurrentWeather(Condition):
    time: datetime = Field(description="Hora local de la ubicación")
    is_day: bool
    temperature: float
    apparent_temperature: float | None
    humidity: float | None
    precipitation: float | None
    wind_speed: float | None = Field(description="km/h")
    wind_gusts: float | None = Field(description="km/h")


class HourlyForecast(Condition):
    time: datetime
    temperature: float | None
    precipitation_probability: float | None


class DailyForecast(Condition):
    date: date
    temperature_max: float | None
    temperature_min: float | None
    precipitation_probability_max: float | None
    sunrise: datetime | None
    sunset: datetime | None


class WeatherRead(BaseModel):
    location: Location
    current: CurrentWeather
    hourly: list[HourlyForecast] = Field(description="Próximas 12 horas")
    daily: list[DailyForecast] = Field(description="Hoy y los 3 días siguientes")
    fetched_at: datetime
    stale: bool = Field(
        default=False, description="True si Open-Meteo falló y se sirve el último dato guardado"
    )
